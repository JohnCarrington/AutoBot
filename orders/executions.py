"""STP execution acknowledgements (Phase 2 WP2, PD-1 option C; owner's approval of 27 November 2026).

A durable, one-way, idempotent record that a specific STP opportunity and structural test resulted in an ACTUAL trade
at IG. Written by the order sender (execution) only; read by STP's opportunity tracker only. STP never
writes it, never manages a position from it and never reads any financial figure: it carries no price, size or result.

File: orders.folder/<PAIR>/stp_executions.jsonl, one line per trade (the order's own deal reference), append-only.

Written only for a trade IG has CONFIRMED open: IG's deal confirmation ACCEPTED (orders/sender.py _on_confirmation), or
an order IG accounted for later, found among its open positions or in its own records (_adopt: the Phase 1 recovered
order, at IG's own open time). An authorisation, a submitted order, an unclear answer, a refusal or a paper trade is
never acknowledged.

Fields: reference, deal_id, strategy, direction, opportunity, lineage, test, key, keys (every STP key the trade
consumed), executed_utc (the confirmed execution time: the confirmation's time, or IG's own open time for a recovered
order), recorded_utc, source.

Crash safety: the order journal is written (and flushed) first and is the source of truth; at every start-up the order
sender writes the acknowledgement of any trade in its journal that carried STP context and has none yet (backfill), so
a stop between the two can never lose one. A line written twice is harmless: readers take each reference once.
Review R1 (27 November 2026): a stop in the middle of a write can leave a last line without its newline. Before each
append the file's last byte is checked and, if it is not a newline, one is written first, so the damaged fragment stays
alone on its own line (kept as evidence; readers skip it) and the new acknowledgement is never joined onto it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

FILE = "stp_executions.jsonl"
UTC = timezone.utc


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read(path: Path) -> list[dict]:
    """Every acknowledgement, once per reference, in file order; a damaged (torn) last line is skipped."""
    out, seen = [], set()
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    for x in lines:
        try:
            a = json.loads(x)
        except ValueError:
            continue
        if isinstance(a, dict) and a.get("reference") and a["reference"] not in seen:
            seen.add(a["reference"])
            out.append(a)
    return out


class ExecutionAcks:
    def __init__(self, folder: Path, now: Any):
        self.path = Path(folder) / FILE
        self.now = now
        self.seen = {a["reference"] for a in read(self.path)}

    def record(self, trade: Any, executed: datetime | None, source: str) -> bool:
        stp = getattr(trade, "stp", None) or {}
        if not stp.get("opportunity") or trade.reference in self.seen:
            return False
        row = {"reference": trade.reference, "deal_id": trade.deal_id, "strategy": trade.strategy,
               "direction": trade.direction, "opportunity": stp.get("opportunity"), "lineage": stp.get("lineage"),
               "test": stp.get("test"), "key": stp.get("key"), "keys": list(stp.get("keys") or []),
               "executed_utc": _iso(executed or trade.opened_at), "recorded_utc": _iso(self.now()), "source": source}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab+") as f:
            f.seek(0, os.SEEK_END)
            if f.tell() > 0:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":                 # a torn last line (review R1): end it first
                    f.write(b"\n")
            f.write((json.dumps(row) + "\n").encode())
            f.flush()
            os.fsync(f.fileno())
        self.seen.add(trade.reference)
        return True

    def backfill(self, trades: Iterable[Any]) -> int:
        n = 0
        for t in trades:
            if self.record(t, t.opened_at, "start-up: the order journal records it open at IG (written again after a "
                                           "stop before its acknowledgement)"):
                n += 1
        return n
