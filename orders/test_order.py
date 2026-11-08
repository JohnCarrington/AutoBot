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
from strategies.common import BREAKOUT, BUY, SELL, SWITCH, Idea

log = logging.getLogger("autobot.orders.test")
UTC = timezone.utc
REQUEST, RUNNING, DONE, RESULT = "test_request.json", "test_request.running.json", "test_request.done.json", "test_result.json"


class TestOrder:
    __test__ = False                    # not a pytest test class
    def __init__(self, settings: Any, client: Any, alerts: Any, quote: Callable[[], tuple[Decimal, Decimal] | None], *,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC), sleep: Callable[[float], None] = _time.sleep,
                 threaded: bool = True):
        self.s, self.client, self.alerts, self.quote, self.now, self.sleep = settings, client, alerts, quote, now, sleep
        self.folder = Path(settings.orders.folder)
        self.threaded = threaded
        self.thread: threading.Thread | None = None
        self.samples: deque = deque()                               # (time, spread in pips or None)
        self.next_check: datetime | None = None
        self.checks: list[str] = []

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

    def tick(self) -> None:
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
        if self.threaded:
            self.thread = threading.Thread(target=self._run, args=(r,), name="test-order", daemon=True)
            self.thread.start()
        else:
            self._run(r)

    def _run(self, r: dict) -> None:
        result: dict = {"request": r, "started_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        if self.checks:
            result["spread_checks"] = list(self.checks)
        try:
            result.update(self._steps(r))
        except Exception as e:                                      # noqa: BLE001
            log.exception("The test order failed.")
            result["error"] = f"{type(e).__name__}: {e}"
        result["finished_utc"] = self.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        (self.folder / RESULT).write_text(json.dumps(result, indent=1, default=str) + "\n")
        running = self.folder / RUNNING
        if running.exists():
            running.rename(self.folder / DONE)
        self.alerts.info("AutoBot test order: " + "; ".join(f"{k}: {v}" for k, v in result.items() if k != "request"))

    def _steps(self, r: dict) -> dict:
        if r.get("approved_by") != "owner":
            return {"refused": "the request is not marked approved_by owner"}
        direction = r.get("direction")
        strategy = r.get("strategy", BREAKOUT)
        hold = int(r.get("hold_seconds", 60))
        if direction not in (BUY, SELL) or strategy not in SWITCH or not 10 <= hold <= 600:
            return {"refused": f"bad request: direction {direction!r}, strategy {strategy!r}, hold {hold}"}
        sender = OrderSender(self.s, self.client, self.alerts, now=self.now, sleep=self.sleep, quote=self.quote)
        sender.start()
        out: dict = {"open_trades_at_start": len(sender.open_trades()),
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
        if not placed.ok:
            return out
        self.sleep(hold)
        closed = sender.close(placed.reference, why="the test order's hold time is over")
        out |= {"closed": closed.what, "close_level": str(closed.level) if closed.level is not None else None,
                "close_reasons": closed.reasons,
                "available_funds_after": str(sender.funds.available) if sender.funds else None,
                "open_trades_after": len(sender.open_trades())}
        return out
