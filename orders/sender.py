"""The order sender (design sections 6 and 7): the only part that places or closes trades at IG.

  * It uses the price service's IG client, already logged in and switched to the bot's account: it
    NEVER logs in itself (the IG login rules allow one login). It refuses to start otherwise, and on
    anything but IG's demo address.
  * Market orders for the pair on the demo account, at trade.size_gbp_per_pip, each with its strategy's
    stop and take profit attached as DISTANCES (stopDistance, limitDistance; the level reversal's stop
    price is turned into a distance from the current price at the moment the order is sent), and FORCE
    OPEN on every order, so it can never close or reduce another position. The request matches AutoBot
    161's open_sb_now.py exactly (owner, 8 November 2026): POST /positions/otc with VERSION 2 and
    Content-Type application/json, the same 17 body fields; the confirmation GET /confirms/{reference}
    with VERSION 1, tried up to orders.confirm_attempts times, orders.confirm_wait_seconds apart, while
    IG answers 404.
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
  * A trade is closed in the record only once IG confirms the close (owner, 10 November 2026). If IG refuses a
    close, IG is asked at once whether the position still exists (GET /positions/{dealId}): if IG says it does
    not, IG had already closed it ("gone at IG"); otherwise the trade stays open, the owner gets a Telegram alert
    straight away with IG's error (each trade its own alert), and the trade manager tries again every
    orders.close_retry_seconds. A trade "gone at IG" is recorded with IG's own close level and time, read from
    IG's activity (GET /history/activity, VERSION 3); so is a stop or take profit IG confirms.
  * reconcile(): at start-up and after every 5-minute candle, the bot's open trades are compared with IG's open
    positions. A trade IG no longer has (confirmed by GET /positions/{dealId} answering 404; nothing is marked
    closed on a failed read) is closed in the record at IG's level and alerted; a size that differs and a position
    the bot did not open are recorded and alerted, once each. IG's 9 and 10 November 2026 closes of the bot's
    positions by its own system (channel SYSTEM, not the stop or limit) were missed before this.
  * It closes trades when the trade manager says so, in full, or by half for the range trade, and confirms
    each close with IG. The close matches AutoBot 161's close_sb_now.py exactly: POST /positions/otc with
    VERSION 1 and _method DELETE, the body dealId, direction (the opposite), orderType MARKET and size only
    (never the epic or expiry: IG refuses dealId with either). After a part close IG leaves the rest as a
    position with a new deal ID: it is found among the open positions and recorded.
  * Every order, confirmation, refusal and close is recorded in orders.folder/<PAIR>/orders.jsonl (one JSON
    line per event, written and flushed before the next step). The open trades are rebuilt from it.
  * PAPER mode (the master switch TRADING=off, design 13): everything runs and is recorded, in
    orders.folder/<PAIR>/paper_orders.jsonl, but NOTHING is ever sent to IG: no order, no close, and IG's open
    positions are not read. A paper trade opens and closes at the current price (the offer for a buy, the bid
    for a sell; a close at the price the trade manager gives).
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
import time as _time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from ig.errors import IGRequestError
from safety.refusals import on_refusal
from safety.rules import AccountFunds, OpenTrade, decide, order_for
from strategies.common import RANGE_TRADE, stop_price, take_profit_pips

log = logging.getLogger("autobot.orders")


def _headers(version: str, **more: str) -> dict:
    """The headers AutoBot 161 sends (besides the API key and the session tokens, which the IG client adds)."""
    return {"VERSION": version, "Content-Type": "application/json", **more}
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
    closed_utc: datetime | None = None      # "gone at IG": when IG closed it (from IG's activity), if known


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dec(x: Any) -> Decimal | None:
    return None if x is None else Decimal(str(x))


class OrderSender:
    def __init__(self, settings: Any, client: Any, alerts: Any, *, now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 sleep: Callable[[float], None] = _time.sleep,
                 quote: Callable[[], tuple[Decimal, Decimal] | None] = lambda: None, paper: bool = False):
        """`quote`: the current (bid, offer) from the price stream, for the level reversal's stop distance (and a
        paper trade's price). `paper`: never send anything to IG (TRADING=off)."""
        self.s, self.client, self.alerts, self.now, self.sleep = settings, client, alerts, now, sleep
        self.quote = quote
        self.paper = paper
        self.o = settings.orders
        self.pair, self.epic = settings.market.pair, settings.market.epic
        self.ppp = Decimal(settings.market.points_per_pip)
        self.size_gbp = Decimal(settings.trade.size_gbp_per_pip)
        self.folder = Path(self.o.folder) / self.pair
        self.journal = self.folder / ("paper_orders.jsonl" if paper else "orders.jsonl")
        self.trades: dict[str, Trade] = {}
        self.unresolved: dict[str, dict] = {}          # references sent but never accounted for by IG
        self.gone: dict[str, Result] = {}              # trades IG closed without the bot (IG's level and time)
        self.gone_new: list[Result] = []               # found since the engine last asked (reconcile / start-up)
        self._reported: set[str] = set()               # differences already alerted (once each)
        self.funds: AccountFunds | None = None
        self.ready = False
        self._lock = threading.RLock()

    # ---- the record ---------------------------------------------------------------------------

    def _record(self, event: str, **data: Any) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        row = {"time_utc": _iso(self.now()), "event": event, "pair": self.pair}
        if self.paper:
            row["paper"] = True
        row.update({k: (str(v) if isinstance(v, Decimal) else _iso(v) if isinstance(v, datetime) else v)
                    for k, v in data.items()})
        with self.journal.open("a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        log.info("Order record: %s %s", event, data.get("reference", ""))

    def _read_record(self) -> None:
        """Rebuild the trades and the unresolved references from the record."""
        self.trades, self.unresolved, self.gone = {}, {}, {}
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
            elif ev == "deal id changed" and ref in self.trades:
                self.trades[ref].deal_id = r["deal_id"]
            elif ev == "half closed" and ref in self.trades:
                self.trades[ref].half_closed = True
                self.trades[ref].size = Decimal(r["remaining_size"])
            elif ev in ("closed", "gone at IG", "closed at IG") and ref in self.trades:
                self.trades[ref].status = CLOSED
                if ev == "gone at IG":
                    self.gone[ref] = self._gone_result(self.trades[ref], r)

    # ---- start-up ----------------------------------------------------------------------------

    def start(self) -> None:
        """Before any order: check the IG session, find the bot's own trades at IG, read the funds."""
        with self._lock:
            if not self.paper:
                demo = self.s.ig.demo_base_url                  # settings refuse any other address
                if getattr(self.client, "base_url", None) != demo:
                    raise NotReady(f"the IG client is not on IG's demo address ({demo}): no orders")
                if not getattr(self.client, "account_active", False):
                    raise NotReady("the price service's IG login is not active: the order sender never logs in itself")
            self._read_record()
            if not self.paper:
                self._recover()
            self._read_funds("start-up")
            self.ready = True
            self._record("ready", open_trades=len(self.open_trades()))

    def _positions(self) -> list[dict]:
        r = self.client.request("GET", "/positions", "2", what="reading the open positions", headers=_headers("2"))
        return list((r.json() or {}).get("positions") or [])

    def _recover(self) -> None:
        positions = self._positions()
        by_ref = {p["position"].get("dealReference"): p for p in positions}
        by_id = {p["position"].get("dealId"): p for p in positions}
        ours = set()
        for t in [t for t in self.trades.values() if t.status == OPEN]:
            p = by_ref.get(t.reference) or by_id.get(t.deal_id)
            if p is None:
                if not self._still_open_at_ig(t):
                    self._gone(t, "not among IG's open positions at start-up (closed at IG while the bot was away)")
                    continue
                p = {"position": {"dealId": t.deal_id, "size": t.size}}
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
                self._not_ours(pos, mk)

    def _not_ours(self, pos: dict, mk: dict) -> None:
        """An open position at IG the bot did not open: recorded and alerted once, left alone."""
        if pos["dealId"] in self._reported:
            return
        self._reported.add(pos["dealId"])
        self._record("not ours", deal_id=pos["dealId"], deal_reference=pos.get("dealReference"),
                     epic=mk.get("epic"), direction=pos.get("direction"), size=pos.get("size"))
        self.alerts.problem("position-not-ours",
                            f"IG has an open position the bot did not open ({mk.get('epic')}, "
                            f"{pos.get('direction')} {pos.get('size')}, deal {pos['dealId']}): left alone.")

    # ---- the bot's open trades against IG's open positions ----------------------------------------

    def _still_open_at_ig(self, t: Trade) -> bool:
        """IG's answer for one position (GET /positions/{dealId}): False only when IG says it does not exist
        (404). Any other failure counts as still open: nothing is marked closed on a guess."""
        try:
            self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position", headers=_headers("2"))
            return True
        except IGRequestError as e:
            return e.status != 404

    def _ig_close_of(self, t: Trade) -> dict | None:
        """IG's own record of how a position closed (GET /history/activity, VERSION 3, with details): the
        activity whose actions close this deal ID. None if IG's activity does not show it (or cannot be read)."""
        frm = (t.opened_at - timedelta(minutes=5)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        to = (self.now() + timedelta(minutes=1)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        try:
            r = self.client.request("GET", f"/history/activity?from={frm}&to={to}&detailed=true&pageSize=50", "3",
                                    what="reading IG's activity", headers=_headers("3"))
            rows = (r.json() or {}).get("activities") or []
        except Exception:                                           # noqa: BLE001
            return None
        for a in rows:
            d = a.get("details") or {}
            if any(x.get("affectedDealId") == t.deal_id and str(x.get("actionType", "")).startswith(("POSITION_CLOSED",
                                                                                                    "POSITION_DELETED"))
                   for x in d.get("actions") or []):
                return {"ig_level": _dec(d.get("level")), "ig_time_utc": a.get("date", "") + "Z" if a.get("date") else None,
                        "ig_channel": a.get("channel"), "ig_close_deal_id": a.get("dealId"),
                        "ig_description": a.get("description")}
        return None

    def _gone_result(self, t: Trade, row: dict) -> Result:
        when = row.get("ig_time_utc")
        return Result(True, "gone at IG", t.reference, t.deal_id, _dec(row.get("ig_level")),
                      [row.get("note", "")], datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None)

    def _gone(self, t: Trade, why: str) -> Result:
        """IG says the position no longer exists although the bot did not close it: closed in the records with
        IG's own level and time (IG's activity), and an alert straight away."""
        info = self._ig_close_of(t) or {}
        t.status = CLOSED
        row = {"note": why} | {k: v for k, v in info.items() if v is not None}
        self._record("gone at IG", reference=t.reference, deal_id=t.deal_id, strategy=t.strategy, **row)
        r = self._gone_result(t, {k: (str(v) if isinstance(v, Decimal) else v) for k, v in row.items()})
        self.gone[t.reference] = r
        self.gone_new.append(r)
        how = (f"IG closed it at {info['ig_level']} at {info['ig_time_utc']} ({info.get('ig_channel')}: "
               f"{info.get('ig_description')})") if info.get("ig_level") is not None else "IG's activity does not show the close yet"
        self.alerts.problem(f"gone-at-ig-{t.deal_id}",
                            f"The bot's {t.strategy} {t.direction} trade {t.deal_id} is no longer open at IG, but the "
                            f"bot did not close it: {why}. {how}. It is now closed in the bot's records.")
        if not self.paper:
            self._read_funds("a trade closed at IG")
        return r

    def reconcile(self, why: str = "regular check") -> list[Result]:
        """The bot's open trades against IG's open positions (GET /positions), at start-up (_recover) and
        regularly: a trade IG no longer has is closed in the records with IG's level (an alert); a size that
        differs, or a position the bot did not open, is recorded and alerted (once each). Returns the trades
        found gone at IG. Live only."""
        if self.paper or not self.ready:
            return []
        with self._lock:
            try:
                positions = self._positions()
            except IGRequestError as e:
                self._record("not checked at IG", why=why, error=str(e))
                self.alerts.problem("positions-not-read", f"IG's open positions could not be read ({why}): {e}. "
                                                          "The bot's open trades were not checked against them.")
                return []
            by_ref = {p["position"].get("dealReference"): p for p in positions}
            by_id = {p["position"].get("dealId"): p for p in positions}
            ours, gone = set(), []
            for t in [t for t in self.trades.values() if t.status == OPEN]:
                p = by_ref.get(t.reference) or by_id.get(t.deal_id)
                if p is None:
                    if self._still_open_at_ig(t):
                        ours.add(t.deal_id)
                        continue
                    gone.append(self._gone(t, f"not among IG's open positions ({why})"))
                    continue
                pos = p["position"]
                ours.add(pos["dealId"])
                if pos["dealId"] != t.deal_id:
                    self._record("deal id changed", reference=t.reference, old_deal_id=t.deal_id, deal_id=pos["dealId"],
                                 note=f"IG's open positions ({why})")
                    t.deal_id = pos["dealId"]
                size = Decimal(str(pos.get("size")))
                key = f"{t.reference}:{size}"
                if size != t.size and key not in self._reported:
                    self._reported.add(key)
                    self._record("size differs at IG", reference=t.reference, deal_id=t.deal_id, size=t.size, ig_size=size)
                    self.alerts.problem(f"size-differs-{t.deal_id}",
                                        f"The bot's {t.strategy} trade {t.deal_id} is {t.size} in its records but "
                                        f"{size} at IG ({why}). Nothing was changed.")
            for p in positions:
                if p["position"]["dealId"] not in ours:
                    self._not_ours(p["position"], p.get("market", {}))
            return gone

    def take_gone(self) -> list[Result]:
        """The trades found gone at IG since the last call (for the trade manager and the records)."""
        with self._lock:
            out, self.gone_new = self.gone_new, []
            return out

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

    def _confirmation(self, ref: str, attempts: int = 1) -> dict | None:
        """IG's confirmation of a deal reference (GET /confirms/{reference}, VERSION 1), tried up to `attempts`
        times, orders.confirm_wait_seconds apart, while IG answers 404 (not there yet). None if IG does not
        have it or did not answer."""
        for k in range(attempts):
            if k:
                self.sleep(self.o.confirm_wait_seconds)
            try:
                r = self.client.request("GET", f"/confirms/{ref}", "1", what="checking a deal confirmation",
                                        headers=_headers("1"))
                return r.json()
            except IGRequestError as e:
                if e.status != 404:
                    return None
        return None

    def _stop_distance(self, idea: Any, order: Any) -> tuple[Decimal | None, str]:
        """The stop as a distance in IG's points. The level reversal's stop price becomes the distance from the
        current price (the bid for a sell, the offer for a buy: the price it opens at) at the moment of sending."""
        sp = stop_price(self.s, idea)
        if sp is None:
            return (order.stop_pips * self.ppp), ""
        q = self.quote()
        if not q:
            return None, "no current price to turn the level reversal's stop price into a distance"
        bid, offer = (Decimal(str(x)) for x in q)
        dist = (Decimal(sp) - bid) if idea.direction == "sell" else (offer - Decimal(sp))
        dist = dist.quantize(Decimal("0.1"))
        if dist <= 0:
            return None, (f"the price ({bid if idea.direction == 'sell' else offer}) is already past the level "
                          f"reversal's stop price ({sp})")
        return dist, ""

    def place(self, idea: Any, *, paused: bool = False, trend_day: str | None = None,
              calendar: list | None = None, day: Any = None) -> Result:
        """Send one market order for an idea, after the safety rules. Never sent twice."""
        with self._lock:
            now = self.now()
            if not self.ready:
                self._record("safety refused", strategy=idea.strategy, reasons=["the order sender's start-up is not done"])
                return Result(False, "safety refused", reasons=["the order sender's start-up is not done"])
            order = order_for(self.s, idea)
            d = decide(self.s, order, self.open_trades(), self.funds, now, paused, calendar, day)
            if not d.allowed:
                self._record("safety refused", strategy=idea.strategy, direction=idea.direction, reasons=d.reasons)
                return Result(False, "safety refused", reasons=d.reasons)
            stop_points, why = self._stop_distance(idea, order)
            if stop_points is None:
                self._record("safety refused", strategy=idea.strategy, direction=idea.direction, reasons=[why])
                return Result(False, "safety refused", reasons=[why])
            ref = self._reference()
            tp = take_profit_pips(self.s, idea.strategy, now, self.pair, calendar, direction=idea.direction,
                                  trend_day=trend_day)
            body = {                                                # exactly AutoBot 161's 17 fields
                "currencyCode": self.o.currency,
                "direction": idea.direction.upper(),
                "epic": self.epic,
                "expiry": self.o.expiry,
                "forceOpen": True,                                  # always
                "guaranteedStop": False,
                "level": None,
                "limitDistance": float(Decimal(tp) * self.ppp),
                "limitLevel": None,
                "orderType": "MARKET",
                "quoteId": None,
                "size": float(order.size_gbp_per_pip / self.ppp),
                "stopDistance": float(stop_points),                 # always a distance, never stopLevel
                "stopLevel": None,
                "trailingStop": False,
                "trailingStopIncrement": None,
                "dealReference": ref,
            }
            self._record("sending", reference=ref, strategy=idea.strategy, direction=idea.direction,
                         size=Decimal(str(body["size"])), stop_pips=order.stop_pips, stop_distance=stop_points,
                         take_profit_pips=tp, idea_time=idea.time, idea_price=idea.entry_price, body=body)
            self.unresolved[ref] = {"strategy": idea.strategy, "direction": idea.direction, "size": str(body["size"]),
                                    "stop_pips": str(stop_points / self.ppp)}
            if self.paper:
                return self._paper_open(ref, idea)
            try:
                r = self.client.request("POST", "/positions/otc", "2", body, what="placing an order",
                                        headers=_headers("2"))
            except IGRequestError as e:
                if e.status is not None and 400 <= e.status < 500:
                    return self._refused(ref, idea, order, e.error_code or f"HTTP {e.status}")
                self._record("unclear", reference=ref, error=str(e))
                return self._settle_unclear(ref, idea, order)
            try:
                echoed = (r.json() or {}).get("dealReference")
            except Exception:                                       # noqa: BLE001
                echoed = None
            confirm_ref = echoed or ref                             # as 161: IG's echo if it sends one
            if confirm_ref != ref:
                self._record("reference echoed", reference=ref, ig_reference=confirm_ref)
            c = self._confirmation(confirm_ref, self.o.confirm_attempts)
            if c is None:
                self._record("unclear", reference=ref, error="no confirmation")
                return self._settle_unclear(ref, idea, order)
            return self._on_confirmation(ref, idea, order, c)

    def _paper_open(self, ref: str, idea: Any) -> Result:
        """TRADING=off: nothing is sent to IG; the paper trade opens at the current price."""
        q = self.quote()
        sent = self.unresolved.pop(ref)
        if not q:
            self._record("not placed", reference=ref, reason="no current price for a paper trade")
            return Result(False, "refused", ref, reasons=["no current price for a paper trade"])
        level = Decimal(str(q[1] if idea.direction == "buy" else q[0]))
        t = Trade(ref, idea.strategy, idea.direction, Decimal(sent["size"]), Decimal(sent["stop_pips"]), self.now(),
                  f"PAPER-{ref}", level)
        self.trades[ref] = t
        self._record("opened", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                     stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level)
        return Result(True, "opened", ref, t.deal_id, t.level)

    def _on_confirmation(self, ref: str, idea: Any, order: Any, c: dict) -> Result:
        if c.get("dealStatus") == "ACCEPTED":
            sent = self.unresolved[ref]
            t = Trade(ref, idea.strategy, idea.direction, Decimal(sent["size"]), Decimal(sent["stop_pips"]), self.now(),
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

    def closed_at_ig(self, reference: str, kind: str, price: Decimal | None = None) -> Result:
        """The trade manager expects IG to have closed this trade (its stop or take profit at IG). Paper: it is
        recorded closed. Live: confirmed with IG (GET /positions/{dealId}); a position still open is reported."""
        with self._lock:
            t = self.trades.get(reference)
            if t is None or t.status != OPEN:
                return Result(False, "not open", reference)
            if not self.paper:
                try:
                    self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position",
                                        headers=_headers("2"))
                    self._record("still open at IG", reference=reference, deal_id=t.deal_id, expected=kind)
                    return Result(False, "still open at IG", reference, t.deal_id)
                except IGRequestError as e:
                    if e.status != 404:
                        self._record("not checked at IG", reference=reference, deal_id=t.deal_id, error=str(e))
                        return Result(False, "not checked", reference, t.deal_id)
            t.status = CLOSED
            info = {} if self.paper else (self._ig_close_of(t) or {})
            if info.get("ig_level") is not None:                    # IG's own close, not the bot's price
                price = info["ig_level"]
            self._record("closed at IG", reference=reference, deal_id=t.deal_id, how=kind, level=price, size=t.size,
                         **{k: v for k, v in info.items() if v is not None})
            if not self.paper:
                self._read_funds("a trade closed")
            when = info.get("ig_time_utc")
            return Result(True, "closed at IG", reference, t.deal_id, price, [],
                          datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None)

    def close(self, reference: str, *, half: bool = False, why: str = "", price: Decimal | None = None) -> Result:
        """Close one of the bot's trades in full, or by half (the range trade only), when the trade manager says so.
        `price`: the trade manager's price (a paper close is recorded at it)."""
        with self._lock:
            if reference in self.gone:
                return self.gone[reference]
            t = self.trades.get(reference)
            if t is None or t.status != OPEN:
                return Result(False, "not open", reference, reasons=["not one of the bot's open trades"])
            if half and (t.strategy != RANGE_TRADE or t.half_closed):
                return Result(False, "refused", reference, t.deal_id,
                              reasons=["only a range trade is closed by half, and only once"])
            size = (t.size / 2) if half else t.size
            if self.paper:
                q = self.quote()
                level = price if price is not None else (Decimal(str(q[0] if t.direction == "buy" else q[1])) if q else None)
                self._record("close sending", reference=reference, deal_id=t.deal_id, size=size, half=half, why=why)
                return self._closed(t, half, size, level, None, "paper")
            body = {"dealId": t.deal_id,                            # exactly AutoBot 161's close: these four only
                    "direction": "SELL" if t.direction == "buy" else "BUY",      # never the epic or expiry
                    "orderType": "MARKET",
                    "size": float(size)}
            self._record("close sending", reference=reference, deal_id=t.deal_id, size=size, half=half, why=why, body=body)
            try:
                r = self.client.request("POST", "/positions/otc", "1", body, what="closing a position",
                                        headers=_headers("1", _method="DELETE"))
                close_ref = (r.json() or {}).get("dealReference")
                c = self._confirmation(close_ref, self.o.confirm_attempts) if close_ref else None
            except IGRequestError as e:
                if e.status is not None and 400 <= e.status < 500:
                    return self._close_refused(t, e.error_code or f"HTTP {e.status}")
                c = None
            if c is not None and c.get("dealStatus") == "ACCEPTED":
                return self._closed(t, half, size, _dec(c.get("level")), c.get("profit"), "confirmed")
            if c is not None and c.get("dealStatus") == "REJECTED":
                return self._close_refused(t, c.get("reason") or "no reason given")
            return self._settle_unclear_close(t, half, size)

    def _residual(self, t: Trade, remaining: Decimal) -> str | None:
        """After a part close IG leaves the rest as a position with a NEW deal ID (AutoBot 161's close report):
        the one open position of the pair in the trade's direction and of the remaining size that is not
        another of the bot's trades. None if there is not exactly one."""
        others = {x.deal_id for x in self.trades.values() if x.status == OPEN and x is not t}
        try:
            positions = self._positions()
        except IGRequestError:
            return None
        if any(p["position"].get("dealId") == t.deal_id for p in positions):
            return t.deal_id                                        # IG kept the deal ID
        found = [p["position"]["dealId"] for p in positions
                 if p.get("market", {}).get("epic") == self.epic and p["position"].get("direction") == t.direction.upper()
                 and Decimal(str(p["position"].get("size"))) == remaining and p["position"]["dealId"] not in others]
        return found[0] if len(found) == 1 else None

    def _closed(self, t: Trade, half: bool, size: Decimal, level: Decimal | None, profit: Any, how: str) -> Result:
        if half:
            t.half_closed, t.size = True, t.size - size
            self._record("half closed", reference=t.reference, deal_id=t.deal_id, size=size, remaining_size=t.size,
                         level=level, profit=profit, how=how)
            new = t.deal_id if self.paper else self._residual(t, t.size)
            if new is None:
                self._record("rest not found", reference=t.reference, deal_id=t.deal_id, remaining_size=t.size)
                self.alerts.problem("part-close-rest", f"After half closing {t.strategy} trade {t.deal_id}, the rest "
                                                       f"({t.size}) could not be found among IG's open positions.")
            elif new != t.deal_id:
                self._record("deal id changed", reference=t.reference, old_deal_id=t.deal_id, deal_id=new,
                             note="IG left the rest of the part close as a new position")
                t.deal_id = new
        else:
            t.status = CLOSED
            self._record("closed", reference=t.reference, deal_id=t.deal_id, size=size, level=level, profit=profit, how=how)
        if not self.paper:
            self._read_funds("a trade closed")
        return Result(True, "half closed" if half else "closed", t.reference, t.deal_id, level)

    def _close_refused(self, t: Trade, reason: str) -> Result:
        """IG refused a close. First IG is asked whether the position still exists: if IG says it does not, IG had
        already closed it (gone at IG, with IG's own level). Otherwise the trade stays open (the trade manager
        tries again) and the owner is alerted straight away with IG's error (each trade its own alert)."""
        self._record("close refused", reference=t.reference, deal_id=t.deal_id, reason=reason)
        if not self._still_open_at_ig(t):
            return self._gone(t, f"IG refused the close ({reason}) because it had already closed the position")
        self.alerts.problem(f"close-refused-{t.deal_id}",
                            f"IG refused to close {t.strategy} {t.direction} trade {t.deal_id}: {reason}. The trade "
                            f"is still open at IG and in the bot's records; the close is tried again every "
                            f"{self.o.close_retry_seconds} seconds.")
        return Result(False, "close refused", t.reference, t.deal_id, reasons=[reason])

    def _settle_unclear_close(self, t: Trade, half: bool, size: Decimal) -> Result:
        """No clear answer to a close: look at the position before anything else. Never sent again here."""
        for k in range(self.o.unclear_checks):
            if k:
                self.sleep(self.o.unclear_check_wait_seconds)
            try:
                r = self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position",
                                        headers=_headers("2"))
            except IGRequestError as e:
                if e.status == 404:
                    if half and self._residual(t, t.size - size) not in (None, t.deal_id):
                        return self._closed(t, True, size, None, None, "the rest is a new position at IG")
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
