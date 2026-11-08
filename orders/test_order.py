"""One real test order on the demo account, approved by the owner (8 November 2026), run INSIDE the price
service on its own IG login (never a second one).

The price service calls tick() every second. Nothing happens unless the owner's request file exists:
    orders.folder/test_request.json
    {"approved_by": "owner", "not_before_utc": "2026-11-09T10:30:00Z", "direction": "buy",
     "strategy": "breakout", "hold_seconds": 60}
Once its time has come, the file is renamed (test_request.running.json) BEFORE anything is sent, so it can
never run twice. Then, in its own thread (the price stream is never held up):
  1. the order sender starts: it reads IG's open positions (its own found, any others reported and left
     alone) and the account's available funds;
  2. one market order, as a trade of the named strategy (its stop and take profit, £10 a pip, force open),
     through the safety rules like any other;
  3. after hold_seconds it is closed in full, confirmed with IG;
  4. every step is in the order record, the result in orders.folder/test_result.json, and on Telegram.
The file is then renamed test_request.done.json.

The spread condition (owner, 8 November 2026), when the request has "max_spread_pips": while the request is
there, the spread (offer - bid, in pips) is sampled from the price stream every second. From not_before_utc,
the order is sent only if every sample over the last "spread_minutes" (15) was under max_spread_pips (2),
with no gap in the samples of more than 60 seconds (no current price counts as a gap). If not, it is checked
again every "check_every_minutes" (5) up to "give_up_utc" (midnight UK) and, if never, nothing is sent: the
request is closed and the owner told on Telegram. Every check is in the log and the result.

The owner's extras (approved 8 November 2026), by "extra" in the request, each with the same rules as above:
  * "restart_recovery" (a): one order; once IG confirms it, the request becomes test_request.restart.json
    (with the reference) and the price service is asked to restart (it stops the stream, logs out and exits
    with code 75, so systemd starts it again after 30 seconds: one logout, one login). After the restart,
    BEFORE anything else, the file is renamed test_request.recovering.json and a new order sender starts: it
    must find the trade at IG by its reference before it allows anything new. The trade is then closed.
  * "half_close" (b): one range trade order; after hold_seconds half of it is closed, after hold_seconds
    more the rest (IG leaves the rest as a position with a new deal ID: it must be found and recorded).
  * "stop_refusal" (c): IG's minimum stop distance is read once (GET /markets/{epic}) and the order is sent
    with its stop at HALF of it (deliberately inside IG's minimum): IG should refuse it, which confirms IG's
    reason code and tests the refusal alert. If IG accepts it anyway, it is closed after hold_seconds.
Each extra's result is in orders.folder/test_result_<extra>.json.
The queue: orders.folder/test_queue.json, a list of requests. Whenever no test request is waiting, running
or restarting, the first is taken off the queue and becomes test_request.json, not before its own
not_before_utc nor before queue_gap_minutes (5) after the previous one finished: one at a time.
"""

from __future__ import annotations

import json
import logging
import threading
import time as _time
from collections import deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from orders.sender import OrderSender
from strategies.common import BREAKOUT, BUY, RANGE_TRADE, SELL, SWITCH, Idea

log = logging.getLogger("autobot.orders.test")
UTC = timezone.utc
REQUEST, RUNNING, DONE, RESULT = "test_request.json", "test_request.running.json", "test_request.done.json", "test_result.json"
RESTART, RECOVERING, QUEUE = "test_request.restart.json", "test_request.recovering.json", "test_queue.json"
RESTART_RECOVERY, HALF_CLOSE, STOP_REFUSAL = "restart_recovery", "half_close", "stop_refusal"
EXTRAS = (RESTART_RECOVERY, HALF_CLOSE, STOP_REFUSAL)
QUEUE_GAP_MINUTES = 5


def result_name(r: dict) -> str:
    return f"test_result_{r['extra']}.json" if r.get("extra") in EXTRAS else RESULT


class _ForcedStopSender(OrderSender):
    """Extra (c) only: the order sender with its stop distance replaced by a forced one (IG's points)."""
    forced_stop_points: Decimal = Decimal(0)

    def _stop_distance(self, idea, order):
        return self.forced_stop_points, ""


class TestOrder:
    __test__ = False                    # not a pytest test class
    def __init__(self, settings: Any, client: Any, alerts: Any, quote: Callable[[], tuple[Decimal, Decimal] | None], *,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC), sleep: Callable[[float], None] = _time.sleep,
                 threaded: bool = True, trading_on: bool = False, request_restart: Callable[[str], None] | None = None):
        """`request_restart`: asks the price service to restart (extra (a)); None: a new order sender is started
        in its place, as if the service had restarted (the tests)."""
        self.s, self.client, self.alerts, self.quote, self.now, self.sleep = settings, client, alerts, quote, now, sleep
        self.folder = Path(settings.orders.folder)
        self.threaded = threaded
        self.trading_on = trading_on                    # with TRADING on, the trading engine's order sender is live
        self.thread: threading.Thread | None = None
        self.samples: deque = deque()                               # (time, spread in pips or None)
        self.next_check: datetime | None = None
        self.checks: list[str] = []
        self.request_restart = request_restart
        self.last_finished: datetime | None = None

    def _sample(self, r: dict) -> None:
        q = self.quote()
        ppp = Decimal(self.s.market.points_per_pip)
        spread = None if not q else (Decimal(str(q[1])) - Decimal(str(q[0]))) / ppp
        now = self.now()
        self.samples.append((now, spread))
        keep = timedelta(minutes=int(r.get("spread_minutes", 15)) + 1)
        while self.samples and self.samples[0][0] < now - keep:
            self.samples.popleft()

    def spread_ok(self, r: dict) -> tuple[bool, str]:
        """Every sample over the last spread_minutes under max_spread_pips, with no gap of more than 60 seconds."""
        most = Decimal(str(r["max_spread_pips"]))
        now = self.now()
        start = now - timedelta(minutes=int(r.get("spread_minutes", 15)))
        window = [(t, x) for t, x in self.samples if t >= start]
        if not self.samples or self.samples[0][0] > start + timedelta(seconds=60):
            return False, "not enough spread samples yet for the whole window"
        times = [start] + [t for t, _ in window] + [now]
        gap = max((b - a for a, b in zip(times, times[1:])), default=timedelta(0))
        if gap > timedelta(seconds=60):
            return False, f"a gap of {int(gap.total_seconds())} seconds in the spread samples"
        missing = sum(1 for _, x in window if x is None)
        if missing:
            return False, f"{missing} second(s) with no current price"
        widest = max(x for _, x in window)
        if widest >= most:
            return False, f"the spread reached {widest.quantize(Decimal('0.1'))} pips (must stay under {most})"
        return True, f"the spread stayed under {most} pips (at most {widest.quantize(Decimal('0.1'))}) for the window"

    def _busy(self) -> bool:
        return (any((self.folder / f).exists() for f in (REQUEST, RUNNING, RESTART, RECOVERING))
                or (self.thread is not None and self.thread.is_alive()))

    def _from_queue(self) -> None:
        """One at a time: the next request off the queue, once nothing else is waiting, running or restarting."""
        q = self.folder / QUEUE
        if not q.exists() or self._busy():
            return
        try:
            items = json.loads(q.read_text())
            assert isinstance(items, list)
        except Exception as e:                                      # noqa: BLE001
            q.rename(self.folder / (QUEUE + ".bad"))
            self.alerts.problem("test-order", f"The test order queue could not be read ({e}): nothing was sent.")
            return
        if not items:
            q.unlink()
            return
        r = dict(items.pop(0))
        earliest = self.now() if self.last_finished is None else max(self.now(), self.last_finished + timedelta(minutes=QUEUE_GAP_MINUTES))
        own = datetime.fromisoformat(str(r.get("not_before_utc", "1970-01-01T00:00:00Z")).replace("Z", "+00:00"))
        r["not_before_utc"] = max(own, earliest).strftime("%Y-%m-%dT%H:%M:%SZ")
        (self.folder / REQUEST).write_text(json.dumps(r) + "\n")
        if items:
            q.write_text(json.dumps(items, indent=1) + "\n")
        else:
            q.unlink()
        self.next_check, self.checks = None, []
        log.info("Test order: %s taken off the queue, not before %s.", r.get("extra", "a test order"), r["not_before_utc"])

    def tick(self) -> None:
        restart = self.folder / RESTART
        if restart.exists() and not (self.thread is not None and self.thread.is_alive()):
            restart.rename(self.folder / RECOVERING)               # before anything is sent: never twice
            r = json.loads((self.folder / RECOVERING).read_text())
            self._start(self._run_recovery, r)
            return
        self._from_queue()
        req = self.folder / REQUEST
        if not req.exists():
            return
        try:
            r = json.loads(req.read_text())
            when = datetime.fromisoformat(r["not_before_utc"].replace("Z", "+00:00"))
        except Exception as e:                                      # noqa: BLE001
            req.rename(self.folder / DONE)
            self.alerts.problem("test-order", f"The test order request could not be read ({e}): nothing was sent.")
            return
        if "max_spread_pips" in r:
            self._sample(r)
        if self.now() < when:
            return
        if "max_spread_pips" in r:
            if self.next_check is None:
                self.next_check = when
            if self.now() < self.next_check:
                return
            ok, why = self.spread_ok(r)
            self.checks.append(f"{self.now().strftime('%H:%M:%S')} UTC: {'send' if ok else 'wait'} ({why})")
            log.info("Test order spread check: %s", self.checks[-1])
            if not ok:
                give_up = datetime.fromisoformat(r["give_up_utc"].replace("Z", "+00:00"))
                if self.now() >= give_up:
                    req.rename(self.folder / DONE)
                    result = {"request": r, "sent": "nothing: the spread was never under "
                              f"{r['max_spread_pips']} pips for {r.get('spread_minutes', 15)} minutes by {r['give_up_utc']}",
                              "checks": self.checks}
                    (self.folder / RESULT).write_text(json.dumps(result, indent=1, default=str) + "\n")
                    self.alerts.problem("test-order", "The test order was NOT sent: the spread was never under "
                                        f"{r['max_spread_pips']} pips for {r.get('spread_minutes', 15)} minutes by "
                                        f"{r['give_up_utc']}. Last check: {self.checks[-1]}")
                    return
                self.next_check = self.next_check + timedelta(minutes=int(r.get("check_every_minutes", 5)))
                while self.next_check <= self.now():
                    self.next_check += timedelta(minutes=int(r.get("check_every_minutes", 5)))
                return
        req.rename(self.folder / RUNNING)                           # before anything is sent: never twice
        self._start(self._run, r)

    def _start(self, target: Callable[[dict], None], r: dict) -> None:
        if self.threaded:
            self.thread = threading.Thread(target=target, args=(r,), name="test-order", daemon=True)
            self.thread.start()
        else:
            target(r)

    def _done_name(self, r: dict) -> str:
        return f"test_request.{r['extra']}.done.json" if r.get("extra") in EXTRAS else DONE

    def _finish(self, r: dict, result: dict, current: str) -> None:
        result["finished_utc"] = self.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        (self.folder / result_name(r)).write_text(json.dumps(result, indent=1, default=str) + "\n")
        f = self.folder / current
        if f.exists():
            f.rename(self.folder / self._done_name(r))
        self.last_finished = self.now()
        label = f"AutoBot test order ({r['extra']})" if r.get("extra") in EXTRAS else "AutoBot test order"
        self.alerts.info(label + ": " + "; ".join(f"{k}: {v}" for k, v in result.items() if k != "request"))

    def _run(self, r: dict) -> None:
        result: dict = {"request": r, "started_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        if self.checks:
            result["spread_checks"] = list(self.checks)
        try:
            result.update(self._steps(r))
        except Exception as e:                                      # noqa: BLE001
            log.exception("The test order failed.")
            result["error"] = f"{type(e).__name__}: {e}"
        if result.get("restarting"):
            return                                                  # finished after the restart (_run_recovery)
        self._finish(r, result, RUNNING)

    def _steps(self, r: dict) -> dict:
        if self.trading_on:
            return {"refused": "TRADING is on: the trading engine's order sender is live, so the test order does not run "
                               "(two order senders must never share the order record)"}
        if r.get("approved_by") != "owner":
            return {"refused": "the request is not marked approved_by owner"}
        direction = r.get("direction")
        strategy = r.get("strategy", BREAKOUT)
        hold = int(r.get("hold_seconds", 60))
        extra = r.get("extra")
        if direction not in (BUY, SELL) or strategy not in SWITCH or not 10 <= hold <= 600 or extra not in (None, *EXTRAS):
            return {"refused": f"bad request: direction {direction!r}, strategy {strategy!r}, hold {hold}, extra {extra!r}"}
        if extra == HALF_CLOSE and strategy != RANGE_TRADE:
            return {"refused": f"bad request: the half close is for the range trade only, not {strategy!r}"}
        out: dict = {}
        if extra == STOP_REFUSAL:
            from ig.markets import min_stop
            from safety.refusals import min_stop_pips
            q = self.quote()
            if not q:
                return {"refused": "no current price from the stream"}
            m = min_stop(self.client, self.s.market.epic)                       # once, before the order
            ppp = Decimal(self.s.market.points_per_pip)
            min_points = min_stop_pips(self.s, m.value, m.unit, Decimal(q[1])) * ppp
            forced = (min_points / 2).quantize(Decimal("0.1"), rounding="ROUND_DOWN")
            out |= {"ig_min_stop": f"{m.value} {m.unit}", "ig_min_stop_points": str(min_points.quantize(Decimal('0.1'))),
                    "stop_sent_points": str(forced)}
            if forced <= 0:
                return out | {"refused": "IG's minimum stop is too small to send a stop inside it: nothing sent"}
            sender: OrderSender = _ForcedStopSender(self.s, self.client, self.alerts, now=self.now, sleep=self.sleep,
                                                    quote=self.quote)
            sender.forced_stop_points = forced
        else:
            sender = OrderSender(self.s, self.client, self.alerts, now=self.now, sleep=self.sleep, quote=self.quote)
        sender.start()
        out |= {"open_trades_at_start": len(sender.open_trades()),
                "available_funds_at_start": str(sender.funds.available) if sender.funds else None}
        q = self.quote()
        if not q:
            return out | {"refused": "no current price from the stream"}
        bid, offer = q
        idea = Idea(self.s.market.pair, strategy, direction, self.now(), Decimal(offer if direction == BUY else bid),
                    "test", "none", None, "test", ["a test order approved by the owner on 8 November 2026"])
        placed = sender.place(idea)
        out |= {"placed": placed.what, "reference": placed.reference, "deal_id": placed.deal_id,
                "fill": str(placed.level) if placed.level is not None else None, "reasons": placed.reasons}
        if extra == STOP_REFUSAL:
            out["ig_refused_it"] = placed.what == "refused"
            out["alerts_sent"] = [k for k, _ in getattr(self.alerts, "sent", [])][-3:] or "see Telegram"
        if not placed.ok:
            return out
        if extra == RESTART_RECOVERY:
            return out | self._restart(r, placed)
        self.sleep(hold)
        if extra == HALF_CLOSE:
            half = sender.close(placed.reference, half=True, why="extra (b): the first half")
            t = sender.trades[placed.reference]
            out |= {"half_closed": half.what, "half_close_level": str(half.level) if half.level is not None else None,
                    "half_close_reasons": half.reasons, "remaining_size": str(t.size), "deal_id_of_the_rest": t.deal_id}
            if not half.ok:
                return out
            self.sleep(hold)
        closed = sender.close(placed.reference, why="the test order's hold time is over")
        out |= {"closed": closed.what, "close_level": str(closed.level) if closed.level is not None else None,
                "close_reasons": closed.reasons,
                "available_funds_after": str(sender.funds.available) if sender.funds else None,
                "open_trades_after": len(sender.open_trades())}
        return out

    # ---- extra (a): restart recovery --------------------------------------------------------------

    def _restart(self, r: dict, placed: Any) -> dict:
        """The trade is open at IG: hand over to the next start-up, then restart the price service."""
        state = dict(r, reference=placed.reference, deal_id=placed.deal_id,
                     fill=str(placed.level) if placed.level is not None else None,
                     opened_utc=self.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        (self.folder / RESTART).write_text(json.dumps(state) + "\n")
        running = self.folder / RUNNING
        if running.exists():
            running.unlink()
        log.info("Test order (restart recovery): trade %s open; restarting the price service.", placed.reference)
        self.alerts.info(f"AutoBot test order (restart_recovery): trade {placed.deal_id} opened at {placed.level}; "
                         "the price service now restarts and must find it.")
        if self.request_restart is not None:
            self.request_restart("extra (a): restart recovery with the test trade open")
        else:                                                       # the tests: as if the service restarted
            self.tick()
        return {"restarting": True}

    def _run_recovery(self, state: dict) -> None:
        r = {k: state[k] for k in state if k not in ("reference", "deal_id", "fill", "opened_utc")}
        result: dict = {"request": r, "before_the_restart": {k: state.get(k) for k in ("reference", "deal_id", "fill",
                                                                                          "opened_utc")},
                        "recovery_started_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        try:
            result.update(self._recover_and_close(state))
        except Exception as e:                                      # noqa: BLE001
            log.exception("The test order's recovery failed.")
            result["error"] = f"{type(e).__name__}: {e}"
        self._finish(r, result, RECOVERING)

    def _recover_and_close(self, state: dict) -> dict:
        if self.trading_on:
            return {"refused": "TRADING is on: the test trade is left to IG's stop and take profit; check it at IG"}
        ref = state["reference"]
        sender = OrderSender(self.s, self.client, self.alerts, now=self.now, sleep=self.sleep, quote=self.quote)
        before = len(sender.journal.read_text().splitlines()) if sender.journal.exists() else 0
        sender.start()                       # finds its own trades at IG before anything new is allowed
        start_rows = [json.loads(x) for x in sender.journal.read_text().splitlines()[before:]]
        ready_at = next(i for i, x in enumerate(start_rows) if x["event"] == "ready")
        t = sender.trades.get(ref)
        out = {"start_up_events": [x["event"] + (f" {x.get('reference') or x.get('deal_id')}") for x in start_rows],
               "found_by_reference": t is not None and t.status == "open",
               "deal_id_at_ig": t.deal_id if t else None,
               "open_trades_at_start": len(sender.open_trades()),
               "available_funds_at_start": str(sender.funds.available) if sender.funds else None,
               "found_before_ready": any(x["event"] == "found at IG" and x.get("reference") == ref
                                         for x in start_rows[:ready_at])}
        if not out["found_by_reference"]:
            return out | {"closed": "nothing to close: the trade was not open at IG after the restart (see start_up_events)"}
        closed = sender.close(ref, why="extra (a): closed after the restart recovery")
        return out | {"closed": closed.what, "close_level": str(closed.level) if closed.level is not None else None,
                      "close_reasons": closed.reasons,
                      "available_funds_after": str(sender.funds.available) if sender.funds else None,
                      "open_trades_after": len(sender.open_trades())}
