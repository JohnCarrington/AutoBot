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
"""

from __future__ import annotations

import json
import logging
import threading
import time as _time
from datetime import datetime, timezone
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
        if self.now() < when:
            return
        req.rename(self.folder / RUNNING)                           # before anything is sent: never twice
        if self.threaded:
            self.thread = threading.Thread(target=self._run, args=(r,), name="test-order", daemon=True)
            self.thread.start()
        else:
            self._run(r)

    def _run(self, r: dict) -> None:
        result: dict = {"request": r, "started_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
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
