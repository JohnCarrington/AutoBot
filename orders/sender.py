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
    sent once. One IG cannot account for yet stays UNRESOLVED (owner, 27 November 2026, after the 25 November 18:02
    slow grind IG accepted at once but showed only minutes later): it counts as an open trade for every safety rule,
    and at every regular check and start-up it is settled from IG's own records only: an open position carrying its
    deal reference, IG's confirmation, or IG's activity (details.dealReference). Found: the bot's own trade, adopted
    with IG's deal ID, fill and open time and the strategy and management context recorded with the order, and
    handed to the engine (take_recovered); found already closed by IG: adopted, then recorded closed at IG's own
    level and time. REJECTED: refused. No record at IG at all orders.unresolved_no_record_after_minutes after it
    was sent: "not placed at IG". Otherwise escalated, never guessed. A position carrying an AutoBot-format
    reference that is in none of the records is escalated and left alone; one opened by hand is left alone.
  * Every close records where its level came from (IG's activity, IG's confirmation, or the bot's own price when IG
    had not yet given its level); the bot's price is looked for again at IG at the next orders.ig_close_level_checks
    regular checks and, once found, handed to the engine as a correction (take_corrections), else escalated.
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
    the bot did not open are recorded and alerted, once each. The owner's 9 and 10 November 2026 closes by hand
    (IG's channel SYSTEM, not the stop or limit) were missed before this.
  * A trade found gone at IG whose close IG shows on channel SYSTEM or WEB but not at its stop or take profit (at or
    beyond either) was closed by the owner by hand (owner, 11 November 2026 for SYSTEM; 23 November 2026 for WEB):
    "closed by owner" at IG's price and time, a short Telegram message (not a warning), and kept apart from the bot's
    own exits (closed_by_owner()).
  * It moves a Bollinger bounce's stop when the trade manager's trail says so (owner, 15 November 2026): the
    position's stop at IG becomes the level the trail gives (beyond the last 3 finished candles).
    IG's open position is read first (GET /positions/{dealId}, VERSION 2) for its take profit, then the position is
    updated (PUT /positions/otc/{dealId}, VERSION 2, the body stopLevel, limitLevel as IG has it, trailingStop false,
    trailingStopDistance and trailingStopIncrement null, guaranteedStop false; a stop moved on an open position is a
    level, unlike an order's stop, which is always a distance) and the move is confirmed (GET /confirms/{reference}).
    The move counts only once IG confirms it ("stop moved"); if IG refuses it, or the answer is unclear and IG's
    position still shows the old stop, the old stop stays ("stop not moved") and the trade manager tries again after
    orders.close_retry_seconds, up to orders.stop_move_attempts in all, then alerts the owner once. Before each move
    IG's buy and sell prices (from that position read) and its minimum stop distance (GET /markets/{epic}) are read
    and recorded with it, and a level on the wrong side of IG's price or inside the minimum is sent as the nearest
    level IG allows (owner, 17 November 2026). Paper: recorded, nothing sent.
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
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any, Callable

from ig.errors import IGRequestError
from safety.refusals import min_stop_pips, on_refusal
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
    stop_level: Decimal | None = None   # the stop as moved at IG and confirmed (the bounce's trail); None: not moved
    once_a_day: str = ""                # the idea's once-a-day key (safety rule 10; owner, 16 November 2026)
    signal: str = ""                    # the idea's signal key (safety rule 11; owner, 18 November 2026)
    recovery: dict = field(default_factory=dict)   # what the engine needs to manage and record it (27 November 2026)
    adopted: bool = False               # accounted for by IG only after it was sent (an "adopted" record)
    stp: dict = field(default_factory=dict)    # the STP opportunity, lineage, test and keys it was authorised on
                                                # (Phase 2 WP2): acknowledged to STP once IG confirms it (executions.py)

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
    price_source: str = ""                  # a close: where its level came from (IG_ACTIVITY, IG_CONFIRMATION, BOT_PRICE)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


CLOSED_BY_OWNER = "closed by owner"
# Where a close's level came from (owner, 27 November 2026: IG's confirmed execution records are the authority for
# realised results; a level IG has not given yet is never presented as IG's, and is looked for again)
IG_ACTIVITY, IG_CONFIRMATION, BOT_PRICE, PAPER_PRICE = (
    "IG's activity", "IG's confirmation", "the bot's price (IG's level not yet known)", "paper")
NOT_PLACED_AT_IG, IG_CLOSE_CONFIRMED, IG_CLOSE_NOT_FOUND = "not placed at IG", "IG close confirmed", "IG close not found"
ACCEPTED_AT_IG = "accepted at IG"       # IG's own evidence that an unresolved order was accepted (kept for good)
# IG's channels for the owner's closes by hand: SYSTEM (owner, 11 November 2026: the IG demo platform labels them so)
# and WEB (owner, 23 November 2026: four closes on IG's web platform at 18:36 UTC that day).
OWNER_CHANNELS = ("SYSTEM", "WEB")


def closed_by_owner(direction: str, info: dict) -> bool:
    """The owner's rule (11 November 2026; WEB added 23 November 2026): a close IG shows on channel SYSTEM or WEB
    that is not at the position's stop or take profit is one the owner made by hand. At the stop means at it or
    beyond it (a stop can fill worse); at the take profit means at it or beyond it. `info` is _ig_close_of's answer
    (IG's own stop and limit levels)."""
    if info.get("ig_channel") not in OWNER_CHANNELS or info.get("ig_level") is None:
        return False
    level, stop, limit = info["ig_level"], info.get("ig_stop_level"), info.get("ig_limit_level")
    buy = direction == "buy"
    at_stop = stop is not None and (level <= stop if buy else level >= stop)
    at_limit = limit is not None and (level >= limit if buy else level <= limit)
    return not (at_stop or at_limit)


def _dec(x: Any) -> Decimal | None:
    return None if x is None else Decimal(str(x))


def _when(x: Any) -> datetime | None:
    """IG's dates ("2026-11-25T18:02:03", "2026/11/25 18:02:03:000", with or without Z), as UTC; None if unreadable."""
    if not x:
        return None
    t = str(x).strip().replace("/", "-").replace(" ", "T").rstrip("Z")
    if t.count(":") == 3:                                   # IG's milliseconds after a colon
        t = t.rsplit(":", 1)[0]
    try:
        return datetime.fromisoformat(t).replace(tzinfo=UTC)
    except ValueError:
        return None


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
        self.recovered_new: list[Trade] = []           # orders IG accounted for only after their sending (the engine
                                                        # takes them into management and the records: take_recovered)
        self.pending_close: dict[str, dict] = {}       # closes whose level IG has not given yet (looked for again)
        self.corrections_new: list[dict] = []          # IG's own close found later (take_corrections)
        self.close_source: dict[str, str] = {}         # reference -> where its close level came from
        self._unresolved_noted: set[str] = set()       # unresolved orders already escalated by the regular check
        self.not_placed: dict[str, dict] = {}          # orders recorded "not placed at IG": still the bot's if IG ever
                                                        # shows a position with their reference (review R4)
        self.funds: AccountFunds | None = None
        self.ready = False
        self._lock = threading.RLock()
        from orders.executions import ExecutionAcks
        self.acks = None if paper else ExecutionAcks(self.folder, self.now)   # STP's execution acknowledgements

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

    def _pending_of(self, row: dict) -> dict:
        """An order sent and not yet accounted for by IG, from its "sending" record: everything needed to count it
        in the safety rules, to settle it with IG, and to recover its management (owner, 27 November 2026)."""
        out = {k: v for k, v in row.items() if k not in ("body", "event", "pair")}
        if row.get("stop_distance") is not None:            # the distance actually sent (a structural stop too)
            out["stop_pips"] = str(Decimal(str(row["stop_distance"])) / self.ppp)
        out["sent_utc"] = row.get("time_utc")
        return out

    def _read_record(self) -> None:
        """Rebuild the trades and the unresolved references from the record."""
        self.trades, self.unresolved, self.gone = {}, {}, {}
        self.not_placed, self.corrections_new = {}, []
        if not self.journal.exists():
            return
        for line in self.journal.read_text().splitlines():
            r = json.loads(line)
            ref, ev = r.get("reference"), r["event"]
            if ev == "sending":
                self.unresolved[ref] = self._pending_of(r)
            elif ev in ("opened", "adopted"):
                sent = self.unresolved.pop(ref, None) or {}
                self.trades[ref] = Trade(ref, r["strategy"], r["direction"], Decimal(r["size"]), Decimal(r["stop_pips"]),
                                         datetime.fromisoformat(r["opened_utc"].replace("Z", "+00:00")),
                                         r.get("deal_id", ""), _dec(r.get("level")),
                                         once_a_day=r.get("once_a_day") or sent.get("once_a_day") or "",
                                         signal=r.get("signal") or sent.get("signal") or "",
                                         recovery=r.get("recovery") or sent.get("recovery") or {},
                                         adopted=ev == "adopted", stp=r.get("stp") or sent.get("stp") or {})
                self.not_placed.pop(ref, None)
            elif ev == ACCEPTED_AT_IG and ref in self.unresolved:
                self.unresolved[ref]["accepted_deal_id"] = r.get("deal_id")
            elif ev == NOT_PLACED_AT_IG:
                sent = self.unresolved.pop(ref, None)
                if sent is not None:
                    self.not_placed[ref] = sent
            elif ev in ("refused", "not placed"):
                self.unresolved.pop(ref, None)
            elif ev in (IG_CLOSE_CONFIRMED, IG_CLOSE_NOT_FOUND):
                self.pending_close.pop(ref, None)
                if ev == IG_CLOSE_CONFIRMED and r.get("ig_level") is not None:   # handed on again after a restart: the
                    self.close_source[ref] = IG_ACTIVITY                        # engine applies it once (review R3)
                    self.corrections_new.append({"reference": ref, "close_price": Decimal(r["ig_level"]),
                                                 "closed_utc": _when(r.get("ig_time_utc")), "price_source": IG_ACTIVITY})
            elif ev == "deal id changed" and ref in self.trades:
                self.trades[ref].deal_id = r["deal_id"]
            elif ev == "stop moved" and ref in self.trades:
                self.trades[ref].stop_level = Decimal(r["stop_level"])
            elif ev == "half closed" and ref in self.trades:
                self.trades[ref].half_closed = True
                self.trades[ref].size = Decimal(r["remaining_size"])
            elif ev in ("closed", "gone at IG", "closed at IG", CLOSED_BY_OWNER) and ref in self.trades:
                self.trades[ref].status = CLOSED
                if ev in ("gone at IG", CLOSED_BY_OWNER):
                    self.gone[ref] = self._gone_result(self.trades[ref], r, ev)
                if r.get("level_source") == BOT_PRICE:     # IG's level still to be found (after a restart too)
                    self._await_ig_close(self.trades[ref])

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
                self.acks.backfill(self.trades.values())   # never lost by a stop between the journal and the ack
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
        ours |= self._settle_unresolved(positions, "start-up", at_start=True)
        for p in positions:
            pos, mk = p["position"], p.get("market", {})
            if pos["dealId"] not in ours:
                self._not_ours(pos, mk)

    def _autobot_format(self, ref: Any) -> bool:
        """A deal reference in AutoBot's own format (prefix, yymmddHHMMSS, "-", 8 hex digits)."""
        import re
        return bool(ref) and re.fullmatch(rf"{re.escape(self.o.deal_reference_prefix)}\d{{12}}-[0-9a-f]{{8}}", str(ref)) is not None

    def _not_ours(self, pos: dict, mk: dict) -> None:
        """An open position at IG the bot did not open: recorded and alerted once, left alone. One whose deal
        reference is in AutoBot's own format but in none of the bot's records is NOT adopted (its strategy and
        management cannot be established from the records): it is escalated for the owner to look at (owner,
        27 November 2026: escalate rather than guess). A position opened by hand keeps IG's own reference and is the
        owner's: never touched."""
        if pos["dealId"] in self._reported:
            return
        self._reported.add(pos["dealId"])
        fmt = self._autobot_format(pos.get("dealReference"))
        self._record("not ours", deal_id=pos["dealId"], deal_reference=pos.get("dealReference"),
                     epic=mk.get("epic"), direction=pos.get("direction"), size=pos.get("size"), autobot_format=fmt)
        if fmt:
            self.alerts.problem("position-not-ours",
                                f"IG has an open position ({mk.get('epic')}, {pos.get('direction')} {pos.get('size')}, "
                                f"deal {pos['dealId']}) whose deal reference {pos.get('dealReference')} is in AutoBot's own "
                                "format but in none of the bot's records: NOT adopted and NOT managed. Please check it at "
                                "IG; the bot leaves it alone.")
            return
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
        # newest first, in windows of 3 hours (IG answers at most 50 activities a read; a trade open for hours, with its
        # stop moves, can have more): the close is usually in the first window (27 November 2026)
        # (newest first for a close just made; then forwards from the open for a trade found long after, such as an
        # unclear order IG opened and closed days before the bot looked)
        first, last = t.opened_at - timedelta(minutes=5), self.now() + timedelta(minutes=1)
        windows, to = [], last
        for _ in range(16):
            frm = max(first, to - timedelta(hours=3))
            windows.append((frm, to))
            if frm <= first:
                break
            to = frm
        earliest = windows[-1][0]                               # where the newest-first windows stopped
        frm = first
        for _ in range(16):
            if frm >= earliest:
                break
            windows.append((frm, min(earliest, frm + timedelta(hours=3))))
            frm += timedelta(hours=3)
        rows: list = []
        for frm, to in windows:
            got = self._activity(frm, to)
            if got is None:
                return None
            if any(self._closes(a, t.deal_id) for a in got):
                rows = got
                break
        for a in rows:
            d = a.get("details") or {}
            if any(x.get("affectedDealId") == t.deal_id and str(x.get("actionType", "")).startswith(("POSITION_CLOSED",
                                                                                                    "POSITION_DELETED"))
                   for x in d.get("actions") or []):
                return {"ig_level": _dec(d.get("level")), "ig_time_utc": a.get("date", "") + "Z" if a.get("date") else None,
                        "ig_channel": a.get("channel"), "ig_close_deal_id": a.get("dealId"),
                        "ig_description": a.get("description"), "ig_stop_level": _dec(d.get("stopLevel")),
                        "ig_limit_level": _dec(d.get("limitLevel"))}
        return None

    @staticmethod
    def _closes(a: dict, deal_id: str) -> bool:
        return any(x.get("affectedDealId") == deal_id and str(x.get("actionType", "")).startswith(
            ("POSITION_CLOSED", "POSITION_DELETED")) for x in (a.get("details") or {}).get("actions") or [])

    def _gone_result(self, t: Trade, row: dict, what: str = "gone at IG") -> Result:
        when = row.get("ig_time_utc")
        return Result(True, what, t.reference, t.deal_id, _dec(row.get("ig_level")),
                      [row.get("note", "")], datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None)

    def _gone(self, t: Trade, why: str) -> Result:
        """IG says the position no longer exists although the bot did not close it: closed in the records with
        IG's own level and time (IG's activity), and an alert straight away."""
        info = self._ig_close_of(t) or {}
        t.status = CLOSED
        owner = closed_by_owner(t.direction, info)
        what = CLOSED_BY_OWNER if owner else "gone at IG"
        row = {"note": f"closed by the owner at IG (IG's channel {info.get('ig_channel')}, not at the stop or take profit)"
               if owner
               else why} | {k: v for k, v in info.items() if v is not None}
        source = IG_ACTIVITY if info.get("ig_level") is not None else BOT_PRICE
        self._record(what, reference=t.reference, deal_id=t.deal_id, strategy=t.strategy, level_source=source, **row)
        r = self._gone_result(t, {k: (str(v) if isinstance(v, Decimal) else v) for k, v in row.items()}, what)
        r.price_source = source
        self.close_source[t.reference] = source
        if source == BOT_PRICE:
            self._await_ig_close(t)
        self.gone[t.reference] = r
        self.gone_new.append(r)
        if not self.paper:
            self._read_funds("a trade closed at IG")
        if owner:
            self._tell_owner(t, info)
            return r
        how = (f"IG closed it at {info['ig_level']} at {info['ig_time_utc']} ({info.get('ig_channel')}: "
               f"{info.get('ig_description')})") if info.get("ig_level") is not None else "IG's activity does not show the close yet"
        self.alerts.problem(f"gone-at-ig-{t.deal_id}",
                            f"The bot's {t.strategy} {t.direction} trade {t.deal_id} is no longer open at IG, but the "
                            f"bot did not close it: {why}. {how}. It is now closed in the bot's records.")
        return r

    def _tell_owner(self, t: Trade, info: dict) -> None:
        """A short Telegram message (not a warning) for a trade the owner closed by hand."""
        level, when = info["ig_level"], info.get("ig_time_utc")
        pips = None if t.level is None else ((level - t.level) if t.direction == "buy" else (t.level - level)) / self.ppp
        try:
            from zoneinfo import ZoneInfo
            tz = self.s.hours.timezone
            uk = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)
            at = f" at {uk:%H:%M} UK on {uk:%a %d %b}"
        except Exception:                                           # noqa: BLE001
            at = ""
        result = "" if pips is None else f": {pips:+.1f} pips (£{pips * t.size:,.2f})"
        self.alerts.info(f"AutoBot: you closed the {t.strategy} {t.direction} (deal {t.deal_id}) at {level}{at}"
                         f"{result}. Recorded as closed by you, not counted in the bot's results.")

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
            ours = self._settle_unresolved(positions, why)  # before anything is called "not ours" (25 Nov 2026)
            by_ref = {p["position"].get("dealReference"): p for p in positions}
            by_id = {p["position"].get("dealId"): p for p in positions}
            gone = []
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
            self._look_for_ig_closes()
            return gone

    def take_gone(self) -> list[Result]:
        """The trades found gone at IG since the last call (for the trade manager and the records)."""
        with self._lock:
            out, self.gone_new = self.gone_new, []
            return out

    def _adopt(self, ref: str, sent: dict, pos: dict, note: str, opened_at: datetime | None = None,
               recovered: bool = False) -> Trade:
        """An order IG accounted for after an unclear answer: the bot's own trade, by its deal reference (ownership
        is the reference the bot recorded before sending), with IG's deal ID, fill and open time, and the strategy and
        management context recorded with the order. `recovered`: found after place() returned (the regular check or
        a start-up): handed to the engine (take_recovered) and alerted."""
        opened = (_when(pos.get("createdDateUTC")) or _when(pos.get("createdDate")) or opened_at
                  or _when(sent.get("sent_utc")) or self.now())     # never later than IG opened it (review R1)
        level = _dec(pos.get("level"))
        stop_pips, tp = Decimal(str(sent["stop_pips"])), sent.get("take_profit_pips")
        ig_stop, ig_limit = _dec(pos.get("stopLevel")), _dec(pos.get("limitLevel"))
        if level is not None and ig_stop is not None:          # IG's own stop and limit, as attached (review)
            stop_pips = abs(level - ig_stop) / self.ppp
        if level is not None and ig_limit is not None:
            tp = str(abs(ig_limit - level) / self.ppp)
        t = Trade(ref, sent["strategy"], sent["direction"], Decimal(str(pos.get("size") or sent["size"])),
                  stop_pips, opened, pos.get("dealId", ""), level,
                  once_a_day=sent.get("once_a_day") or "", signal=sent.get("signal") or "",
                  recovery=dict(sent.get("recovery") or {}, take_profit_pips=tp, idea_price=sent.get("idea_price"),
                                sent_utc=sent.get("sent_utc"), ig_stop_level=None if ig_stop is None else str(ig_stop),
                                ig_limit_level=None if ig_limit is None else str(ig_limit)),
                  adopted=True, stp=sent.get("stp") or {})
        self.not_placed.pop(ref, None)
        self.trades[ref] = t
        self.unresolved.pop(ref, None)
        self._unresolved_noted.discard(ref)
        self._record("adopted", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                     stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level, note=note,
                     recovery=t.recovery, **({"once_a_day": t.once_a_day} if t.once_a_day else {}),
                     **({"signal": t.signal} if t.signal else {}))
        if getattr(self, "acks", None) is not None:   # IG's own open time: the confirmed execution chronology
            self.acks.record(t, t.opened_at, "IG's records: an order IG accounted for after it was sent (recovered)")
        if recovered:
            self.recovered_new.append(t)
            self.alerts.problem(f"order-recovered-{ref}",
                                f"Order {ref} ({t.strategy} {t.direction}) that IG had not confirmed is the bot's own "
                                f"trade at IG (deal {t.deal_id}, opened {_iso(t.opened_at)} at {t.level}): {note}. It "
                                "is now in the records and managed by the trade manager.")
        return t

    # ---- orders IG has not yet accounted for (owner, 27 November 2026) --------------------------------------------

    def _confirmation_state(self, ref: str) -> tuple[str, dict | None]:
        """IG's confirmation of a reference: ("accepted" | "rejected", the confirmation), ("absent", None) when IG
        answers 404 (it has none), or ("error", None) when IG could not be read: never taken as an answer."""
        try:
            c = self.client.request("GET", f"/confirms/{ref}", "1", what="checking a deal confirmation",
                                    headers=_headers("1")).json() or {}
        except IGRequestError as e:
            return ("absent", None) if e.status == 404 else ("error", None)
        status = c.get("dealStatus")
        return ("accepted", c) if status == "ACCEPTED" else ("rejected", c) if status == "REJECTED" else ("error", c)

    def _activity(self, frm: datetime, to: datetime, deal_id: str | None = None) -> list | None:
        """IG's activity history with details (GET /history/activity, VERSION 3); None if it cannot be read."""
        q = f"from={frm.astimezone(UTC):%Y-%m-%dT%H:%M:%S}&to={to.astimezone(UTC):%Y-%m-%dT%H:%M:%S}&detailed=true&pageSize=50"
        if deal_id:
            q += f"&dealId={deal_id}"
        try:
            r = self.client.request("GET", f"/history/activity?{q}", "3", what="reading IG's activity", headers=_headers("3"))
            return list((r.json() or {}).get("activities") or [])
        except Exception:                                           # noqa: BLE001
            return None

    def _opening_in_activity(self, ref: str, sent: dict) -> tuple[dict | None, bool]:
        """IG's own record of this reference's order (its activity, details.dealReference): (the activity or None,
        whether the activity could be read)."""
        start = _when(sent.get("sent_utc")) or self.now()
        rows = self._activity(start - timedelta(minutes=2), min(self.now(), start + timedelta(
            minutes=self.o.unresolved_no_record_after_minutes)) + timedelta(minutes=1))
        if rows is None:
            return None, False
        for a in rows:
            if (a.get("details") or {}).get("dealReference") == ref:
                return a, True
        return None, len(rows) < 50                     # a full page (IG gives 50 at most) proves nothing by absence

    def _settle_unresolved(self, positions: list[dict], why: str, at_start: bool = False) -> set[str]:
        """Every order sent that IG had not accounted for, settled from IG's own records, never by a guess and never
        by sending it again (owner, 27 November 2026):
          1. an open position carrying its deal reference: the bot's own trade, adopted with its strategy and
             management context (the 25 November 18:02 slow grind was called "not ours" here);
          2. IG's confirmation REJECTED, or its activity showing the order REJECTED: refused;
          3. IG's confirmation ACCEPTED, or its activity showing the position opened: adopted at IG's deal ID, fill and
             open time; if IG has closed it meanwhile (its stop or limit while the bot did not know), it is then
             recorded closed at IG's own level and time (gone at IG);
          4. no position, IG's confirmation answering 404, and IG's activity (read without error) showing nothing for
             the reference orders.unresolved_no_record_after_minutes after it was sent: IG never placed it
             (NOT_PLACED_AT_IG, alerted);
          5. otherwise it stays unresolved: still counted in the safety rules (open_trades) and escalated.
        Returns the deal IDs of the positions adopted (they are the bot's, never "not ours")."""
        ours: set[str] = set()
        by_ref = {p["position"].get("dealReference"): p for p in positions}
        by_id = {p["position"].get("dealId"): p for p in positions}
        where = "at start-up" if at_start else f"by the regular check ({why})"
        for ref, sent in list(self.not_placed.items()):        # review R4: IG shows it after all
            p = by_ref.get(ref)
            if p is not None:
                ours.add(p["position"]["dealId"])
                self._adopt(ref, sent, p["position"], f"IG shows it {where}, after it had been recorded not placed at "
                                                      "IG", recovered=True)
        if not self.unresolved:
            return ours
        for ref, sent in list(self.unresolved.items()):
            p = by_ref.get(ref)
            if p is not None:
                ours.add(p["position"]["dealId"])
                self._adopt(ref, sent, p["position"], f"found among IG's open positions {where}", recovered=True)
                continue
            state, c = self._confirmation_state(ref)
            if state == "rejected":
                self.unresolved.pop(ref)
                self._record("refused", reference=ref, reason=(c or {}).get("reason"), note=f"IG's confirmation, {where}")
                continue
            act, readable = self._opening_in_activity(ref, sent)
            if act is not None and act.get("status") == "REJECTED":
                self.unresolved.pop(ref)
                self._record("refused", reference=ref, reason=act.get("description"), note=f"IG's activity, {where}")
                continue
            det = (act or {}).get("details") or {}
            deal = (c or {}).get("dealId") if state == "accepted" else None
            deal = deal or next((x.get("affectedDealId") for x in det.get("actions") or []
                                 if x.get("actionType") == "POSITION_OPENED"), None) or (act or {}).get("dealId")
            if deal and not sent.get("accepted_deal_id"):        # IG's evidence of acceptance, journalled once: an
                sent["accepted_deal_id"] = deal                  # accepted order is never "not placed" afterwards
                self._record(ACCEPTED_AT_IG, reference=ref, deal_id=deal,
                             source="IG's confirmation" if state == "accepted" else "IG's activity")
            deal = deal or sent.get("accepted_deal_id")
            if deal:
                pos = by_id.get(deal, {}).get("position")
                if pos is None:
                    try:
                        got = self.client.request("GET", f"/positions/{deal}", "2", what="checking a position",
                                                  headers=_headers("2")).json() or {}
                        pos = got.get("position")
                    except IGRequestError as e:
                        if e.status != 404:
                            self._escalate_unresolved(ref, sent, at_start, f"IG's position {deal} could not be read")
                            continue
                opened = _when((act or {}).get("date"))
                if pos is not None:
                    ours.add(deal)
                    self._adopt(ref, sent, pos, f"IG opened it as deal {deal}; found {where}", opened, recovered=True)
                    continue
                # no position by list or by deal ID: recorded closed ONLY on IG's own evidence of the close (review R1:
                # IG's position endpoints can lag behind its confirmation); otherwise it stays unresolved and counted
                level = det.get("level") if act else (c or {}).get("level")
                probe = Trade(ref, sent["strategy"], sent["direction"], Decimal(str(sent["size"])),
                              Decimal(str(sent["stop_pips"])), opened or _when(sent.get("sent_utc")) or self.now(), deal)
                if (self._ig_close_of(probe) or {}).get("ig_level") is None:
                    self._escalate_unresolved(ref, sent, at_start, f"IG accepted it as deal {deal}, but neither its "
                                              "open position nor its close is visible at IG yet")
                    continue
                t = self._adopt(ref, sent, {"dealId": deal, "size": det.get("size") or sent["size"], "level": level,
                                            "stopLevel": det.get("stopLevel"), "limitLevel": det.get("limitLevel")},
                                f"IG opened it as deal {deal} and has closed it since; found {where}", opened,
                                recovered=True)
                self._gone(t, "IG opened it and then closed it while the bot did not know (an unclear order)")
                continue
            age = self.now() - (_when(sent.get("sent_utc")) or self.now())
            if state == "absent" and readable and age >= timedelta(minutes=self.o.unresolved_no_record_after_minutes):
                self.not_placed[ref] = self.unresolved.pop(ref)    # kept: recovered if IG ever shows it (review R4)
                self._unresolved_noted.discard(ref)
                self._record(NOT_PLACED_AT_IG, reference=ref, strategy=sent.get("strategy"),
                             note=f"no position, no confirmation and nothing in IG's activity "
                                  f"{int(age.total_seconds() // 60)} minutes after it was sent; it is not sent again")
                self.alerts.problem(f"order-not-placed-{ref}",
                                    f"Order {ref} ({sent.get('strategy')} {sent.get('direction')}) was sent but IG has no "
                                    f"record of it: no position, no confirmation and nothing in its activity "
                                    f"{int(age.total_seconds() // 60)} minutes later. Recorded as not placed at IG; it "
                                    "is not sent again and no longer counts as open. If IG ever shows a position with "
                                    "this reference, the bot adopts and manages it.")
                continue
            self._escalate_unresolved(ref, sent, at_start, "IG has no open position, confirmation or activity for it yet")
        return ours

    def _escalate_unresolved(self, ref: str, sent: dict, at_start: bool, why: str) -> None:
        """An order still not accounted for: it keeps counting as open in the safety rules; recorded and alerted at
        every start-up and once by the regular checks."""
        if not at_start and ref in self._unresolved_noted:
            return
        self._unresolved_noted.add(ref)
        self.alerts.problem("order-unresolved", f"Order {ref} ({sent.get('strategy')}) was sent but IG has no "
                                                 f"open position for it and no confirmation ({why}): it is not sent "
                                                 "again, and it counts as an open trade for the safety rules until "
                                                 "IG's own records settle it.")
        self._record("still unresolved", reference=ref, why=why)

    # ---- closes whose level IG has not given yet (owner, 27 November 2026) ------------------------------------------

    def _await_ig_close(self, t: Trade) -> None:
        self.pending_close[t.reference] = {"deal_id": t.deal_id, "opened_at": t.opened_at, "direction": t.direction,
                                           "checks": 0}
        self.close_source[t.reference] = BOT_PRICE

    def _look_for_ig_closes(self) -> None:
        """Each regular check: IG's own close level and time for every close recorded at the bot's price, up to
        orders.ig_close_level_checks checks; found: recorded (IG_CLOSE_CONFIRMED) and handed to the engine
        (take_corrections); never found: escalated (IG's statement is needed)."""
        for ref, w in list(self.pending_close.items()):
            t = self.trades.get(ref)
            if t is None:
                self.pending_close.pop(ref)
                continue
            info = self._ig_close_of(t) or {}
            if info.get("ig_level") is not None:
                self.pending_close.pop(ref)
                self.close_source[ref] = IG_ACTIVITY
                self._record(IG_CLOSE_CONFIRMED, reference=ref, deal_id=t.deal_id,
                             **{k: v for k, v in info.items() if v is not None})
                self.corrections_new.append({"reference": ref, "close_price": info["ig_level"],
                                             "closed_utc": _when(info.get("ig_time_utc")), "price_source": IG_ACTIVITY})
                continue
            w["checks"] += 1
            if w["checks"] >= self.o.ig_close_level_checks:
                self.pending_close.pop(ref)
                self._record(IG_CLOSE_NOT_FOUND, reference=ref, deal_id=t.deal_id, checks=w["checks"])
                self.alerts.problem(f"ig-close-not-found-{ref}",
                                    f"IG's own close level for {t.strategy} trade {t.deal_id} was not found in its activity "
                                    f"after {w['checks']} checks: the records keep the bot's price, marked as such. "
                                    "IG's statement is needed to correct it.")

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
        """The bot's open trades for the safety rules, AND every order sent that IG has not yet accounted for: an
        uncertain submission may be open at IG, so it counts towards every limit and the risk until IG's own records
        settle it (owner, 27 November 2026: the 25 November 18:45 slow grind opened beside an unrecorded one)."""
        # each at its ACTUAL size at IG (£ a point x points a pip; already the rest after a half close), not the
        # configured size: a recovered position can differ (pre-deployment verification, 27 November 2026)
        out = [OpenTrade(t.strategy, t.direction, t.opened_at, t.stop_pips, t.size * self.ppp, t.deal_id)
               for t in self.trades.values() if t.status == OPEN]
        for u in self.unresolved.values():
            out.append(OpenTrade(u["strategy"], u["direction"], _when(u.get("sent_utc")) or self.now(),
                                 Decimal(str(u["stop_pips"])), Decimal(str(u.get("size") or self.size_gbp / self.ppp))
                                 * self.ppp, ""))
        return out

    def unresolved_orders(self) -> list[dict]:
        """The orders sent that IG has not yet accounted for (the dashboard's warning)."""
        return [dict(u, reference=ref) for ref, u in self.unresolved.items()]

    def take_recovered(self) -> list[Trade]:
        """Orders IG accounted for only after they were sent (adopted by the regular check or at start-up), since the
        last call: for the trade manager and the records."""
        with self._lock:
            out, self.recovered_new = self.recovered_new, []
            return out

    def take_corrections(self) -> list[dict]:
        """IG's own close levels found after a close was recorded at the bot's price, since the last call."""
        with self._lock:
            out, self.corrections_new = self.corrections_new, []
            return out

    def used_signals(self) -> dict[str, str]:
        """The signal keys of every trade opened (open or closed) and every order sent and not yet settled, each with
        its strategy (safety rule 11; owner, 18 November 2026)."""
        out = {u["signal"]: u["strategy"] for u in self.unresolved.values() if u.get("signal")}
        out.update({t.signal: t.strategy for t in self.trades.values() if t.signal})
        # OD-32 (owner, 24 November 2026): each part of a key joined by "|" counts as used too (an STP-authorised
        # trade keeps the strategy's own key and STP's opportunity/test key); a key without "|" is unchanged
        for key, strategy in list(out.items()):
            if "|" in key:
                for part in key.split("|"):
                    out.setdefault(part, strategy)
        return out

    def used_once_a_day(self) -> set[str]:
        """The once-a-day keys of every trade opened (open or closed) and every order sent and not yet settled
        (safety rule 10)."""
        return ({t.once_a_day for t in self.trades.values() if t.once_a_day}
                | {u.get("once_a_day") for u in self.unresolved.values() if u.get("once_a_day")})

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
        """The stop as a distance in IG's points. The level reversal's and the session sweep's stop price becomes the
        distance from the current price (the bid for a sell, the offer for a buy: the price it opens at) at the
        moment of sending."""
        sp = stop_price(self.s, idea)
        if sp is None:
            return (order.stop_pips * self.ppp), ""
        q = self.quote()
        if not q:
            return None, f"no current price to turn the {idea.strategy}'s stop price into a distance"
        bid, offer = (Decimal(str(x)) for x in q)
        dist = (Decimal(sp) - bid) if idea.direction == "sell" else (offer - Decimal(sp))
        dist = dist.quantize(Decimal("0.1"))
        if dist <= 0:
            return None, (f"the price ({bid if idea.direction == 'sell' else offer}) is already past the "
                          f"{idea.strategy}'s stop price ({sp})")
        return dist, ""

    def place(self, idea: Any, *, paused: bool = False, trend_day: str | None = None,
              calendar: list | None = None, day: Any = None, recovery: dict | None = None) -> Result:
        """Send one market order for an idea, after the safety rules. Never sent twice. `recovery`: what the engine
        needs to manage and record the trade if IG accounts for it only later (the idea's entry price, the market
        state, its reason and steps, the trend day), recorded with the order before IG is contacted."""
        with self._lock:
            now = self.now()
            if not self.ready:
                self._record("safety refused", strategy=idea.strategy, reasons=["the order sender's start-up is not done"])
                return Result(False, "safety refused", reasons=["the order sender's start-up is not done"])
            order = order_for(self.s, idea)
            d = decide(self.s, order, self.open_trades(), self.funds, now, paused, calendar, day,
                       self.used_once_a_day(), self.used_signals())
            if not d.allowed:
                held = [ref for ref, u in self.unresolved.items() if u.get("strategy") == idea.strategy]
                reasons = list(d.reasons) + ([f"counted as open: order {', '.join(held)} sent but not yet accounted for "
                                              "by IG"] if held else [])
                self._record("safety refused", strategy=idea.strategy, direction=idea.direction, reasons=reasons)
                return Result(False, "safety refused", reasons=reasons)
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
            once = (getattr(idea, "context", None) or {}).get("once_a_day", "")
            signal = (getattr(idea, "context", None) or {}).get("signal", "")
            row = {"reference": ref, "strategy": idea.strategy, "direction": idea.direction,
                   "size": Decimal(str(body["size"])), "stop_pips": order.stop_pips, "stop_distance": stop_points,
                   "take_profit_pips": tp, "idea_time": idea.time, "idea_price": idea.entry_price}
            row |= ({"once_a_day": once} if once else {}) | ({"signal": signal} if signal else {})
            row |= {"recovery": recovery} if recovery else {}
            stp = (getattr(idea, "context", None) or {}).get("stp")
            row |= {"stp": {k: stp.get(k) for k in ("opportunity", "lineage", "test", "key", "keys")}} if stp else {}
            self._record("sending", **row, body=body)              # written and flushed before IG is contacted
            self.unresolved[ref] = self._pending_of(json.loads(json.dumps(
                {k: (str(v) if isinstance(v, Decimal) else _iso(v) if isinstance(v, datetime) else v)
                 for k, v in row.items()})) | {"time_utc": _iso(now)})
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
                  f"PAPER-{ref}", level, once_a_day=sent.get("once_a_day") or "",
                  signal=sent.get("signal") or "")
        self.trades[ref] = t
        self._record("opened", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                     stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level,
                     **({"once_a_day": t.once_a_day} if t.once_a_day else {}),
                     **({"signal": t.signal} if t.signal else {}))
        return Result(True, "opened", ref, t.deal_id, t.level)

    def _on_confirmation(self, ref: str, idea: Any, order: Any, c: dict) -> Result:
        if c.get("dealStatus") == "ACCEPTED":
            sent = self.unresolved[ref]
            t = Trade(ref, idea.strategy, idea.direction, Decimal(sent["size"]), Decimal(sent["stop_pips"]), self.now(),
                      c.get("dealId", ""), _dec(c.get("level")), once_a_day=sent.get("once_a_day") or "",
                      signal=sent.get("signal") or "", recovery=sent.get("recovery") or {}, stp=sent.get("stp") or {})
            self.trades[ref] = t
            self.unresolved.pop(ref, None)
            self._record("opened", reference=ref, strategy=t.strategy, direction=t.direction, size=t.size,
                         stop_pips=t.stop_pips, opened_utc=t.opened_at, deal_id=t.deal_id, level=t.level,
                         stop_level=c.get("stopLevel"), limit_level=c.get("limitLevel"),
                         **({"once_a_day": t.once_a_day} if t.once_a_day else {}),
                     **({"signal": t.signal} if t.signal else {}))
            if getattr(self, "acks", None) is not None:   # IG confirmed it ACCEPTED: an actual execution
                self.acks.record(t, t.opened_at, "IG's deal confirmation: ACCEPTED")
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
            info = {} if self.paper else (self._ig_close_of(t) or {})
            if closed_by_owner(t.direction, info):                  # not IG's stop or limit: the owner closed it
                return self._gone(t, "closed by the owner at IG")
            t.status = CLOSED
            source = PAPER_PRICE if self.paper else BOT_PRICE
            if info.get("ig_level") is not None:                    # IG's own close, not the bot's price
                price, source = info["ig_level"], IG_ACTIVITY
            self._record("closed at IG", reference=reference, deal_id=t.deal_id, how=kind, level=price, size=t.size,
                         level_source=source, **{k: v for k, v in info.items() if v is not None})
            self.close_source[reference] = source
            if source == BOT_PRICE:                                 # IG's activity lags: looked for again
                self._await_ig_close(t)
            if not self.paper:
                self._read_funds("a trade closed")
            when = info.get("ig_time_utc")
            return Result(True, "closed at IG", reference, t.deal_id, price, [],
                          datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None, source)

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

    # ---- moving a stop (the Bollinger bounce's trail) ----------------------------------------------

    def move_stop(self, reference: str, level: Decimal, why: str = "") -> Result:
        """Move one open trade's stop at IG to `level` (the Bollinger bounce's trail), or to the nearest level IG
        allows when `level` is on the wrong side of IG's price or inside IG's minimum stop distance (owner,
        17 November 2026). IG's buy and sell prices and its minimum stop distance are read and recorded with every
        move. Counts only once IG confirms it; Result.level is the level sent. Result.ok False: the old stop stays at
        IG and in the records; the trade manager decides whether to try again and alerts the owner when it gives up."""
        with self._lock:
            t = self.trades.get(reference)
            if t is None or t.status != OPEN:
                return Result(False, "not open", reference, reasons=["not one of the bot's open trades"])
            level = Decimal(level)
            if self.paper:
                self._record("stop move sending", reference=reference, deal_id=t.deal_id, stop_level=level, why=why)
                return self._stop_moved(t, level, "paper")
            try:
                r = self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position",
                                        headers=_headers("2"))
                got = r.json() or {}
                pos, mkt = got.get("position") or {}, got.get("market") or {}
            except IGRequestError as e:
                if e.status == 404:
                    self._record("stop not moved", reference=reference, deal_id=t.deal_id, stop_level=level,
                                 reason="IG has no open position with this deal ID")
                    return Result(False, "stop not moved", reference, t.deal_id,
                                  reasons=["IG has no open position with this deal ID"])
                return self._stop_refused(t, level, f"IG's position could not be read ({e.error_code or e.status})")
            seen = self._market_now(mkt)
            send = self._nearest_allowed(t.direction, level, seen)
            ig_stop = _dec(pos.get("stopLevel"))
            seen["rule_level"] = level
            seen["distance_from_market_pips"] = self._distance(t.direction, send, seen)
            if ig_stop is not None and send != ig_stop and not self._closer(t.direction, send, ig_stop):
                reason = (f"the nearest level IG allows now, {send}, is not closer than the stop IG has, {ig_stop}: "
                          f"not sent")
                self._record("stop not moved", reference=reference, deal_id=t.deal_id, stop_level=send,
                             reason=reason, **seen)
                return Result(False, "stop not moved", reference, t.deal_id, send, reasons=[reason])
            if ig_stop == send:                                     # already there (an earlier unclear answer)
                return self._stop_moved(t, send, "already at IG")
            body = {"stopLevel": float(send),
                    "limitLevel": pos.get("limitLevel"),            # the take profit as IG has it: never removed
                    "trailingStop": False, "trailingStopDistance": None, "trailingStopIncrement": None,
                    "guaranteedStop": False}
            self._record("stop move sending", reference=reference, deal_id=t.deal_id, stop_level=send,
                         old_stop_level=ig_stop, why=why, body=body, **seen)
            level = send
            try:
                r = self.client.request("PUT", f"/positions/otc/{t.deal_id}", "2", body, what="moving a stop",
                                        headers=_headers("2"))
                ref = (r.json() or {}).get("dealReference")
                c = self._confirmation(ref, self.o.confirm_attempts) if ref else None
            except IGRequestError as e:
                if e.status is not None and 400 <= e.status < 500:
                    return self._stop_refused(t, level, e.error_code or f"HTTP {e.status}")
                c = None
            if c is not None and c.get("dealStatus") == "ACCEPTED":
                return self._stop_moved(t, _dec(c.get("stopLevel")) or level, "confirmed")
            if c is not None and c.get("dealStatus") == "REJECTED":
                return self._stop_refused(t, level, c.get("reason") or "no reason given")
            try:                                                    # no clear answer: look at the position
                r = self.client.request("GET", f"/positions/{t.deal_id}", "2", what="checking a position",
                                        headers=_headers("2"))
                if _dec(((r.json() or {}).get("position") or {}).get("stopLevel")) == level:
                    return self._stop_moved(t, level, "IG's position shows the new stop")
            except IGRequestError:
                pass
            return self._stop_refused(t, level, "no clear answer from IG, and its position does not show the new stop")

    def _stop_moved(self, t: Trade, level: Decimal, how: str) -> Result:
        t.stop_level = level
        self._record("stop moved", reference=t.reference, deal_id=t.deal_id, stop_level=level, how=how)
        return Result(True, "stop moved", t.reference, t.deal_id, level)

    def _stop_refused(self, t: Trade, level: Decimal, reason: str) -> Result:
        # No alert here (owner, 17 November 2026): the trade manager tries up to orders.stop_move_attempts times and
        # alerts the owner once when it gives up.
        self._record("stop not moved", reference=t.reference, deal_id=t.deal_id, stop_level=level, reason=reason)
        return Result(False, "stop not moved", t.reference, t.deal_id, level, reasons=[reason])

    def _market_now(self, mkt: dict) -> dict:
        """IG's buy and sell prices and minimum stop distance for a stop move, as recorded with it (owner,
        17 November 2026). The prices come from IG's position read just before (its market snapshot), else from the
        price stream; the minimum from GET /markets/{epic} (dealingRules.minNormalStopOrLimitDistance), read with
        every move because IG can change it. A minimum that cannot be read is recorded as not known."""
        bid, offer, source = _dec(mkt.get("bid")), _dec(mkt.get("offer")), "IG's position"
        if bid is None or offer is None:
            q = self.quote()
            bid, offer, source = (Decimal(q[0]), Decimal(q[1]), "the price stream") if q else (None, None, "not known")
        seen: dict[str, Any] = {"ig_bid": bid, "ig_offer": offer, "prices_from": source,
                                "ig_min_stop_value": None, "ig_min_stop_unit": None, "ig_min_stop_pips": None}
        try:
            from ig.markets import min_stop
            m = min_stop(self.client, self.epic)
            seen.update(ig_min_stop_value=m.value, ig_min_stop_unit=m.unit,
                        ig_min_stop_pips=min_stop_pips(self.s, m.value, m.unit, offer or bid or Decimal(0)))
        except Exception as e:                                      # noqa: BLE001  (recorded; the move goes on)
            seen["ig_min_stop_error"] = str(e) or type(e).__name__
        return seen

    def _nearest_allowed(self, direction: str, level: Decimal, seen: dict) -> Decimal:
        """`level`, or the nearest level IG allows if it is on the wrong side of IG's price or closer to it than IG's
        minimum stop distance (owner, 17 November 2026): a sell's stop at least the minimum above IG's buy price, a
        buy's at least the minimum below IG's sell price (the price each would close at), rounded to IG's tenth of a
        point away from the price. Unchanged if IG's prices are not known; a minimum not known counts as 0."""
        tenth = self.ppp / 10
        gap = Decimal(seen.get("ig_min_stop_pips") or 0) * self.ppp
        if direction == "sell":
            if seen["ig_offer"] is None:
                return level
            floor = seen["ig_offer"] + gap
            return level if level >= floor else (floor / tenth).to_integral_value(ROUND_CEILING) * tenth
        if seen["ig_bid"] is None:
            return level
        ceiling = seen["ig_bid"] - gap
        return level if level <= ceiling else (ceiling / tenth).to_integral_value(ROUND_FLOOR) * tenth

    def _distance(self, direction: str, level: Decimal, seen: dict) -> Decimal | None:
        """How far the stop sent is from the price it would close at, in pips (negative: the wrong side)."""
        px = seen["ig_offer"] if direction == "sell" else seen["ig_bid"]
        if px is None:
            return None
        return ((level - px) if direction == "sell" else (px - level)) / self.ppp

    @staticmethod
    def _closer(direction: str, level: Decimal, than: Decimal) -> bool:
        return level < than if direction == "sell" else level > than

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
            source = PAPER_PRICE if self.paper else (IG_CONFIRMATION if level is not None else BOT_PRICE)
            self._record("closed", reference=t.reference, deal_id=t.deal_id, size=size, level=level, profit=profit, how=how,
                         level_source=source)
            self.close_source[t.reference] = source
            if source == BOT_PRICE:                                 # an unclear close: IG's level looked for later
                self._await_ig_close(t)
        if not self.paper:
            self._read_funds("a trade closed")
        return Result(True, "half closed" if half else "closed", t.reference, t.deal_id, level, [],
                      None if self.paper else self.now())      # live: when IG confirmed the close

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
