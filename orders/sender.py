"""The order sender (design sections 6 and 7): the only part that places or closes trades at IG.

  * It uses the price service's IG client, already logged in and switched to the bot's account: it
    NEVER logs in itself (the IG login rules allow one login). It refuses to start otherwise, and on
    anything but IG's demo address.
  * Market orders for the pair on the demo account, at trade.size_gbp_per_pip, each with its strategy's
    stop (a distance; the level reversal's a level) and take profit (a distance) attached, and FORCE OPEN
    on every order, so it can never close or reduce another position.
  * Before sending, it records its own unique deal reference. A trade counts only once IG confirms it
    (GET /confirms/{reference}); IG's deal ID and fill price are recorded with the reference.
  * If IG times out or its answer is unclear, it checks with IG (the reference's confirmation, then the
    open positions) up to orders.unclear_checks times. It never sends the same trade twice: an order is
    sent once, and one IG cannot account for is reported and checked again at the next start-up.
  * Every new order goes through the safety rules first (safety/rules.py), with the open trades and the
    available funds it keeps: the funds are read from IG at start-up and whenever a trade opens or closes.
    IG refusing a trade for its stop or for lack of funds is handled by safety/refusals.py.
  * At start-up it finds its own open trades at IG by their recorded deal references (and deal IDs) before
    any new trade is allowed. Positions it did not open are left alone and reported.
  * It closes trades when the trade manager says so, in full, or by half for the range trade, and confirms
    each close with IG.
  * Every order, confirmation, refusal and close is recorded in orders.folder/<PAIR>/orders.jsonl (one JSON
    line per event, written and flushed before the next step). The open trades are rebuilt from it.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
import time as _time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from ig.errors import IGRequestError
from safety.refusals import on_refusal
from safety.rules import AccountFunds, OpenTrade, decide, order_for
from strategies.common import RANGE_TRADE, stop_price, take_profit_pips

log = logging.getLogger("autobot.orders")
UTC = timezone.utc
OPEN, CLOSED = "open", "closed"


class NotReady(RuntimeError):
    """The order sender has not finished its start-up (or cannot use IG): no orders."""


@dataclass
class Trade:
    """One of the bot's trades, from the record."""
    reference: str
    strategy: str
    direction: str                      # buy or sell
    size: Decimal                       # IG's size: £ per point
    stop_pips: Decimal
    opened_at: datetime
    deal_id: str = ""
    level: Decimal | None = None        # IG's fill price
    status: str = OPEN
    half_closed: bool = False

    def as_open_trade(self, size_gbp_per_pip: Decimal) -> OpenTrade:
        part = Decimal("0.5") if self.half_closed else Decimal(1)
        return OpenTrade(self.strategy, self.direction, self.opened_at, self.stop_pips, size_gbp_per_pip * part,
                         self.deal_id)


@dataclass
class Result:
    """What happened to one order or close."""
    ok: bool
    what: str                           # opened, closed, half closed, refused, safety refused, not found, ...
    reference: str = ""
    deal_id: str = ""
    level: Decimal | None = None
    reasons: list[str] = field(default_factory=list)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dec(x: Any) -> Decimal | None:
    return None if x is None else Decimal(str(x))


class OrderSender:
    def __init__(self, settings: Any, client: Any, alerts: Any, *, now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 sleep: Callable[[float], None] = _time.sleep):
        self.s, self.client, self.alerts, self.now, self.sleep = settings, client, alerts, now, sleep
        self.o = settings.orders
        self.pair, self.epic = settings.market.pair, settings.market.epic
        self.ppp = Decimal(settings.market.points_per_pip)
        self.size_gbp = Decimal(settings.trade.size_gbp_per_pip)
        self.folder = Path(self.o.folder) / self.pair
        self.journal = self.folder / "orders.jsonl"
        self.trades: dict[str, Trade] = {}
        self.unresolved: dict[str, dict] = {}          # references sent but never accounted for by IG
        self.funds: AccountFunds | None = None
        self.ready = False
        self._lock = threading.RLock()

    # ---- the record ---------------------------------------------------------------------------

    def _record(self, event: str, **data: Any) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        row = {"time_utc": _iso(self.now()), "event": event, "pair": self.pair}
        row.update({k: (str(v) if isinstance(v, Decimal) else _iso(v) if isinstance(v, datetime) else v)
                    for k, v in data.items()})
        with self.journal.open("a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        log.info("Order record: %s %s", event, data.get("reference", ""))

    def _read_record(self) -> None:
        """Rebuild the trades and the unresolved references from the record."""
        self.trades, self.unresolved = {}, {}
        if not self.journal.exists():
            return
        for line in self.journal.read_text().splitlines():
            r = json.loads(line)
            ref, ev = r.get("reference"), r["event"]
            if ev == "sending":
                self.unresolved[ref] = r
            elif ev in ("opened", "adopted"):
                self.unresolved.pop(ref, None)
                self.trades[ref] = Trade(ref, r["strategy"], r["direction"], Decimal(r["size"]), Decimal(r["stop_pips"]),
                                         datetime.fromisoformat(r["opened_utc"].replace("Z", "+00:00")),
                                         r.get("deal_id", ""), _dec(r.get("level")))
            elif ev in ("refused", "not placed"):
                self.unresolved.pop(ref, None)
            elif ev == "half closed" and ref in self.trades:
                self.trades[ref].half_closed = True
                self.trades[ref].size = Decimal(r["remaining_size"])
            elif ev in ("closed", "gone at IG") and ref in self.trades:
                self.trades[ref].status = CLOSED

    # ---- start-up ----------------------------------------------------------------------------

    def start(self) -> None:
        """Before any order: check the IG session, find the bot's own trades at IG, read the funds."""
        with self._lock:
            demo = self.s.ig.demo_base_url                      # settings refuse any other address
            if getattr(self.client, "base_url", None) != demo:
                raise NotReady(f"the IG client is not on IG's demo address ({demo}): no orders")
            if not getattr(self.client, "account_active", False):
                raise NotReady("the price service's IG login is not active: the order sender never logs in itself")
            self._read_record()
            self._recover()
            self._read_funds("start-up")
            self.ready = True
            self._record("ready", open_trades=len(self.open_trades()))

    def _positions(self) -> list[dict]:
        r = self.client.request("GET", "/positions", "2", what="reading the open positions")
        return list((r.json() or {}).get("positions") or [])

    def _recover(self) -> None:
        positions = self._positions()
        by_ref = {p["position"].get("dealReference"): p for p in positions}
        by_id = {p["position"].get("dealId"): p for p in positions}
        ours = set()
        for t in [t for t in self.trades.values() if t.status == OPEN]:
            p = by_ref.get(t.reference) or by_id.get(t.deal_id)
            if p is None:
                t.status = CLOSED
                self._record("gone at IG", reference=t.reference, deal_id=t.deal_id, strategy=t.strategy,
                             note="not among IG's open positions at start-up (closed at IG while the bot was away)")
                continue
            ours.add(p["position"]["dealId"])
            t.deal_id, t.size = p["position"]["dealId"], Decimal(str(p["position"]["size"]))
            self._record("found at IG", reference=t.reference, deal_id=t.deal_id, size=t.size)
        for ref, sent in list(self.unresolved.items()):
            p = by_ref.get(ref)
            if p is not None:
                ours.add(p["position"]["dealId"])
                self._adopt(ref, sent, p["position"], "found at IG at start-up")
            else:
                c = self._confirmation(ref)
                if c is not None and c.get("dealStatus") == "REJECTED":
                    self.unresolved.pop(ref)
                    self._record("refused", reference=ref, reason=c.get("reason"), note="found at start-up")
                else:
                    self.alerts.problem("order-unresolved", f"Order {ref} ({sent.get('strategy')}) was sent but IG has no "
                                                             "open position for it and no confirmation: it is not sent again.")
                    self._record("still unresolved", reference=ref)
        for p in positions:
            pos, mk = p["position"], p.get("market", {})
            if pos["dealId"] not in ours:
                self._record("not ours", deal_id=pos["dealId"], deal_reference=pos.get("dealReference"),
                             epic=mk.get("epic"), direction=pos.get("direction"), size=pos.get("size"))
                self.alerts.problem("position-not-ours",
                                    f"IG has an open position the bot did not open ({mk.get('epic')}, "
                                    f"{pos.get('direction')} {pos.get('size')}, deal {pos['dealId']}): left alone.")

    def _adopt(self, ref: str, sent: dict, pos: dict, note: str) -> Trade:
        t = Trade(ref, sent["strategy"], sent["direction"], Decimal(str(pos.get("size") or sent["size"])),
                  Decimal(sent["stop_pips"]), self.now(), pos.get("dealId", ""), _dec(pos.get("level")))
        self.trades[ref] = t
        self.unresolved.pop(ref, None)
        self._record("adopted", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                     stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level, note=note)
        return t

    def _read_funds(self, why: str) -> None:
        try:
            self.funds = AccountFunds.from_ig(self.client.account_balance(), self.now())
            self._record("funds", available=self.funds.available, why=why)
        except Exception as e:                                      # noqa: BLE001
            self.funds = None                                       # unknown funds: the safety rules refuse
            self._record("funds not read", why=why, error=str(e))
            self.alerts.problem("funds-not-read", f"The account's available funds could not be read from IG ({why}): {e}. "
                                                  "New trades are refused until they are.")

    def open_trades(self) -> list[OpenTrade]:
        return [t.as_open_trade(self.size_gbp) for t in self.trades.values() if t.status == OPEN]

    # ---- placing -----------------------------------------------------------------------------

    def _reference(self) -> str:
        ref = f"{self.o.deal_reference_prefix}{self.now().strftime('%y%m%d%H%M%S')}-{secrets.token_hex(4)}"
        assert len(ref) <= 30 and ref not in self.trades and ref not in self.unresolved
        return ref

    def _confirmation(self, ref: str) -> dict | None:
        """IG's confirmation of a deal reference, or None if IG does not have it (yet) or did not answer."""
        try:
            r = self.client.request("GET", f"/confirms/{ref}", "1", what="checking a deal confirmation")
            return r.json()
        except IGRequestError:
            return None

    def place(self, idea: Any, *, paused: bool = False, trend_day: str | None = None,
              calendar: list | None = None) -> Result:
        """Send one market order for an idea, after the safety rules. Never sent twice."""
        with self._lock:
            now = self.now()
            if not self.ready:
                self._record("safety refused", strategy=idea.strategy, reasons=["the order sender's start-up is not done"])
                return Result(False, "safety refused", reasons=["the order sender's start-up is not done"])
            order = order_for(self.s, idea)
            d = decide(self.s, order, self.open_trades(), self.funds, now, paused, calendar)
            if not d.allowed:
                self._record("safety refused", strategy=idea.strategy, direction=idea.direction, reasons=d.reasons)
                return Result(False, "safety refused", reasons=d.reasons)
            ref = self._reference()
            tp = take_profit_pips(self.s, idea.strategy, now, self.pair, calendar, direction=idea.direction,
                                  trend_day=trend_day)
            body = {"epic": self.epic, "expiry": self.o.expiry, "direction": idea.direction.upper(),
                    "size": float(order.size_gbp_per_pip / self.ppp), "orderType": "MARKET",
                    "currencyCode": self.o.currency, "forceOpen": True, "guaranteedStop": False,
                    "dealReference": ref, "limitDistance": float(Decimal(tp) * self.ppp)}
            sp = stop_price(self.s, idea)
            if sp is not None:
                body["stopLevel"] = float(sp)
            else:
                body["stopDistance"] = float(order.stop_pips * self.ppp)
            self._record("sending", reference=ref, strategy=idea.strategy, direction=idea.direction,
                         size=Decimal(str(body["size"])), stop_pips=order.stop_pips, take_profit_pips=tp,
                         idea_time=idea.time, idea_price=idea.entry_price, body=body)
            self.unresolved[ref] = {"strategy": idea.strategy, "direction": idea.direction, "size": str(body["size"]),
                                    "stop_pips": str(order.stop_pips)}
            try:
                self.client.request("POST", "/positions/otc", "2", body, what="placing an order")
            except IGRequestError as e:
                if e.status is not None and 400 <= e.status < 500:
                    return self._refused(ref, idea, order, e.error_code or f"HTTP {e.status}")
                self._record("unclear", reference=ref, error=str(e))
                return self._settle_unclear(ref, idea, order)
            c = self._confirmation(ref)
            if c is None:
                self._record("unclear", reference=ref, error="no confirmation")
                return self._settle_unclear(ref, idea, order)
            return self._on_confirmation(ref, idea, order, c)

    def _on_confirmation(self, ref: str, idea: Any, order: Any, c: dict) -> Result:
        if c.get("dealStatus") == "ACCEPTED":
            sent = self.unresolved[ref]
            t = Trade(ref, idea.strategy, idea.direction, Decimal(sent["size"]), order.stop_pips, self.now(),
                      c.get("dealId", ""), _dec(c.get("level")))
            self.trades[ref] = t
            self.unresolved.pop(ref, None)
            self._record("opened", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                         stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level,
                         stop_level=c.get("stopLevel"), limit_level=c.get("limitLevel"))
            self._read_funds("a trade opened")
            return Result(True, "opened", ref, t.deal_id, t.level)
        return self._refused(ref, idea, order, c.get("reason") or c.get("dealStatus") or "no reason given")

    def _refused(self, ref: str, idea: Any, order: Any, reason: str) -> Result:
        from ig.markets import min_stop
        self.unresolved.pop(ref, None)
        self._record("refused", reference=ref, strategy=idea.strategy, reason=reason)
        kind = on_refusal(self.s, reason, idea.strategy, order.stop_pips, Decimal(idea.entry_price),
                          lambda: min_stop(self.client, self.epic), self.alerts, self.now(),
                          self.funds.available if self.funds else None)
        return Result(False, "refused", ref, reasons=[f"IG refused it: {reason} ({kind})"])

    def _settle_unclear(self, ref: str, idea: Any, order: Any) -> Result:
        """IG timed out or was unclear: find out whether the order went through. Never send it again."""
        for k in range(self.o.unclear_checks):
            if k:
                self.sleep(self.o.unclear_check_wait_seconds)
            c = self._confirmation(ref)
            if c is not None and c.get("dealStatus") in ("ACCEPTED", "REJECTED"):
                self._record("checked", reference=ref, found="confirmation", status=c.get("dealStatus"))
                return self._on_confirmation(ref, idea, order, c)
            try:
                p = next((p for p in self._positions() if p["position"].get("dealReference") == ref), None)
            except IGRequestError:
                p = None
            if p is not None:
                self._record("checked", reference=ref, found="open position")
                t = self._adopt(ref, self.unresolved[ref], p["position"], "found among the open positions after an unclear answer")
                self._read_funds("a trade opened")
                return Result(True, "opened", ref, t.deal_id, t.level)
        self._record("not found", reference=ref, checks=self.o.unclear_checks,
                     note="IG has neither a confirmation nor an open position for it; it is not sent again")
        self.alerts.problem("order-unclear", f"Order {ref} ({idea.strategy} {idea.direction}) got no clear answer from IG "
                                             f"and was not found after {self.o.unclear_checks} checks. It is NOT sent again; "
                                             "it is checked again at the next start-up.")
        return Result(False, "not found", ref, reasons=["no clear answer from IG; not found; not sent again"])

    # ---- closing -----------------------------------------------------------------------------

    def close(self, reference: str, *, half: bool = False, why: str = "") -> Result:
        """Close one of the bot's trades in full, or by half (the range trade only), when the trade manager says so."""
        with self._lock:
            t = self.trades.get(reference)
            if t is None or t.status != OPEN:
                return Result(False, "not open", reference, reasons=["not one of the bot's open trades"])
            if half and (t.strategy != RANGE_TRADE or t.half_closed):
                return Result(False, "refused", reference, t.deal_id,
                              reasons=["only a range trade is closed by half, and only once"])
            size = (t.size / 2) if half else t.size
            body = {"dealId": t.deal_id, "direction": "SELL" if t.direction == "buy" else "BUY", "size": float(size),
                    "orderType": "MARKET", "expiry": self.o.expiry}
            self._record("close sending", reference=reference, deal_id=t.deal_id, size=size, half=half, why=why, body=body)
            try:
                r = self.client.request("POST", "/positions/otc", "1", body, what="closing a position",
                                        headers={"_method": "DELETE"})
                close_ref = (r.json() or {}).get("dealReference")
                c = self._confirmation(close_ref) if close_ref else None
            except IGRequestError as e:
                if e.status is not None and 400 <= e.status < 500:
                    return self._close_refused(t, e.error_code or f"HTTP {e.status}")
                c = None
            if c is not None and c.get("dealStatus") == "ACCEPTED":
                return self._closed(t, half, size, _dec(c.get("level")), c.get("profit"), "confirmed")
            if c is not None and c.get("dealStatus") == "REJECTED":
                return self._close_refused(t, c.get("reason") or "no reason given")
            return self._settle_unclear_close(t, half, size)

    def _closed(self, t: Trade, half: bool, size: Decimal, level: Decimal | None, profit: Any, how: str) -> Result:
        if half:
            t.half_closed, t.size = True, t.size - size
            self._record("half closed", reference=t.reference, deal_id=t.deal_id, size=size, remaining_size=t.size,
                         level=level, profit=profit, how=how)
        else:
            t.status = CLOSED
            self._record("closed", reference=t.reference, deal_id=t.deal_id, size=size, level=level, profit=profit, how=how)
        self._read_funds("a trade closed")
        return Result(True, "half closed" if half else "closed", t.reference, t.deal_id, level)

    def _close_refused(self, t: Trade, reason: str) -> Result:
        self._record("close refused", reference=t.reference, deal_id=t.deal_id, reason=reason)
        self.alerts.problem("close-refused", f"IG refused to close {t.strategy} trade {t.deal_id}: {reason}.")
        return Result(False, "close refused", t.reference, t.deal_id, reasons=[reason])

    def _settle_unclear_close(self, t: Trade, half: bool, size: Decimal) -> Result:
        """No clear answer to a close: look at the position before anything else. Never sent again here."""
        for k in range(self.o.unclear_checks):
            if k:
                self.sleep(self.o.unclear_check_wait_seconds)
            try:
                r = self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position")
            except IGRequestError as e:
                if e.status == 404:
                    return self._closed(t, False, t.size, None, None, "the position is gone at IG")
                continue
            now_size = Decimal(str(((r.json() or {}).get("position") or {}).get("size")))
            if now_size < t.size:
                return self._closed(t, half and now_size > 0, t.size - now_size, None, None, "the position is smaller at IG")
            break
        self._record("close not done", reference=t.reference, deal_id=t.deal_id,
                     note="no clear answer and the position is unchanged at IG; not sent again")
        self.alerts.problem("close-unclear", f"Closing {t.strategy} trade {t.deal_id} got no clear answer and the "
                                             "position is still open at IG. Not sent again: the trade manager decides.")
        return Result(False, "close not done", t.reference, t.deal_id)
