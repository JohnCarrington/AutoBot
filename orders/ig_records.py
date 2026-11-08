"""The owner's check of IG's own records (8 November 2026), run INSIDE the price service on its IG login
(never a second one). Read-only: it never places, changes or closes anything.

The price service calls tick() every second. Nothing happens unless a request file exists:
    orders.folder/ig_check_request.json
    {"from_utc": "2026-11-08T23:00:00Z", "to_utc": "2026-11-08T23:45:00Z", "deal_ids": ["DIAAAAYS9LEACBT"]}
It is renamed (ig_check_request.running.json) before anything is asked, so it never runs twice. Then, in its
own thread, four GETs:
  * IG's activity history, with details (GET /history/activity, VERSION 3): what IG did and when, each deal's
    reference, and the stop and take profit IG attached;
  * IG's transactions (GET /history/transactions, VERSION 2): the closed trade's open and close levels and its
    profit or loss as IG booked it;
  * IG's open positions (GET /positions, VERSION 2): whether anything is still open;
  * the account's funds (GET /accounts).
The answers go to orders.folder/ig_check_result.json (no account number), a short summary to Telegram, and the
request becomes ig_check_request.done.json.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("autobot.orders.ig_records")
UTC = timezone.utc
REQUEST, RUNNING, DONE, RESULT = ("ig_check_request.json", "ig_check_request.running.json",
                                  "ig_check_request.done.json", "ig_check_result.json")


def _ig_time(s: str) -> str:
    """IG's history dates: yyyy-MM-ddTHH:mm:ss (UTC; the UK is on GMT in November)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")


class IGRecordsCheck:
    def __init__(self, settings: Any, client: Any, alerts: Any, *, now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 threaded: bool = True):
        self.s, self.client, self.alerts, self.now, self.threaded = settings, client, alerts, now, threaded
        self.folder = Path(settings.orders.folder)
        self.thread: threading.Thread | None = None

    def tick(self) -> None:
        req = self.folder / REQUEST
        if not req.exists():
            return
        try:
            r = json.loads(req.read_text())
            frm, to = _ig_time(r["from_utc"]), _ig_time(r["to_utc"])
        except Exception as e:                                      # noqa: BLE001
            req.rename(self.folder / DONE)
            self.alerts.problem("ig-check", f"The IG records check request could not be read ({e}): nothing was asked.")
            return
        req.rename(self.folder / RUNNING)                           # before anything is asked: never twice
        if self.threaded:
            self.thread = threading.Thread(target=self._run, args=(r, frm, to), name="ig-check", daemon=True)
            self.thread.start()
        else:
            self._run(r, frm, to)

    def _get(self, path: str, version: str, what: str) -> Any:
        try:
            return self.client.request("GET", path, version, what=what,
                                       headers={"VERSION": version, "Content-Type": "application/json"}).json()
        except Exception as e:                                      # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}

    def _run(self, r: dict, frm: str, to: str) -> None:
        deals = set(r.get("deal_ids") or [])
        epic = self.s.market.epic
        result: dict = {"request": r, "asked_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        act = self._get(f"/history/activity?from={frm}&to={to}&detailed=true&pageSize=50", "3", "reading IG's activity")
        if "error" in act:
            result["activity"] = act
        else:
            rows = act.get("activities") or []
            result["activity"] = [a for a in rows if a.get("epic") == epic or a.get("dealId") in deals
                                  or any(x.get("affectedDealId") in deals for x in (a.get("details") or {}).get("actions") or [])]
        tx = self._get(f"/history/transactions?type=ALL&from={frm}&to={to}&pageSize=50", "2", "reading IG's transactions")
        result["transactions"] = tx if "error" in tx else (tx.get("transactions") or [])
        pos = self._get("/positions", "2", "reading the open positions")
        result["open_positions"] = pos if "error" in pos else [
            {"dealId": p["position"].get("dealId"), "dealReference": p["position"].get("dealReference"),
             "epic": (p.get("market") or {}).get("epic"), "direction": p["position"].get("direction"),
             "size": p["position"].get("size"), "level": p["position"].get("level"),
             "stopLevel": p["position"].get("stopLevel"), "limitLevel": p["position"].get("limitLevel")}
            for p in pos.get("positions") or []]
        try:
            bal = self.client.account_balance()
            result["funds"] = {k: bal.get(k) for k in ("balance", "available", "profitLoss", "deposit")}
        except Exception as e:                                      # noqa: BLE001
            result["funds"] = {"error": f"{type(e).__name__}: {e}"}
        result["finished_utc"] = self.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        (self.folder / RESULT).write_text(json.dumps(result, indent=1, default=str) + "\n")
        running = self.folder / RUNNING
        if running.exists():
            running.rename(self.folder / DONE)
        n = lambda x: len(x) if isinstance(x, list) else "error"    # noqa: E731
        log.info("IG records check done: %s activities, %s transactions, %s open positions.",
                 n(result["activity"]), n(result["transactions"]), n(result["open_positions"]))
        self.alerts.info(f"AutoBot IG records check: {n(result['activity'])} activities, {n(result['transactions'])} "
                         f"transactions, {n(result['open_positions'])} open positions at IG; available funds "
                         f"{result['funds'].get('available')}.")
