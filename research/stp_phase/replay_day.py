"""Replay one day through the market-phase research model (planner/phase.py) with the live planner's own inputs
(research/stp_phase/history.py exact_inputs): every 15 minutes and at each real trade entry, using only candles
finished by then. RESEARCH ONLY: reads candles and trade records, writes the output folder only.

    nice .venv/bin/python -m research.stp_phase.replay_day --day 2026-11-18 --out <folder>
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.phase import REVERSAL_PATTERN_STRATEGIES, assess_phase, classify_trade, summary
from prices.model import parse_iso
from prices.store import CandleStore
from research.stp_phase.history import exact_inputs

UTC = timezone.utc
STORE = "/opt/autobot/data/research/stp_phase_store/GBPUSD"
TRADES = "/opt/autobot/data/records/GBPUSD/trades.jsonl"


def trades_on(day: str) -> list[dict]:
    out = []
    for line in Path(TRADES).read_text().splitlines():
        r = json.loads(line)
        if r["event"] == "opened" and r["opened_utc"].startswith(day):
            closed = next((json.loads(x) for x in Path(TRADES).read_text().splitlines()
                           if json.loads(x)["event"] == "closed" and json.loads(x)["reference"] == r["reference"]), None)
            out.append({**r, "close": closed})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--step-minutes", type=int, default=15)
    a = ap.parse_args(argv)
    s = load_settings().for_pair("GBPUSD")
    store = CandleStore(Path(STORE), 10 ** 6)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    day0 = parse_iso(a.day + "T00:00:00Z")
    rows, full = [], []
    t = day0 + timedelta(seconds=5)
    while t < day0 + timedelta(hours=20):
        inp, _ = exact_inputs(s, store, t)
        v = assess_phase(s, inp)
        r = summary(v)
        r["v1_planner"] = plan_at(s, store, t).direction if t.minute == 0 else ""
        rows.append(r)
        full.append(v.as_dict())
        t += timedelta(minutes=a.step_minutes)
    trades = []
    for tr in trades_on(a.day):
        t = parse_iso(tr["opened_utc"])
        inp, _ = exact_inputs(s, store, t)
        v = assess_phase(s, inp)
        label, why = classify_trade(v, tr["direction"], tr["strategy"] in REVERSAL_PATTERN_STRATEGIES)
        c = tr.get("close") or {}
        trades.append({"opened_utc": tr["opened_utc"], "strategy": tr["strategy"], "direction": tr["direction"],
                       "pips": c.get("pips"), "result": c.get("result") or "open", "classification": label, "reason": why,
                       "phase": summary(v), "view": v.as_dict()})
    (out / "replay_rows.json").write_text(json.dumps(rows, indent=1))
    (out / "replay_full.json").write_text(json.dumps(full, indent=1, default=str))
    (out / "trades.json").write_text(json.dumps(trades, indent=1, default=str))
    for r in rows:
        print(r["as_of_utc"][11:16], r["direction"], r["v1_direction"], r["v1_planner"], r["phase"], r["opportunity"],
              r["opportunity_trade"], r["exhaustion"], r["impulse_extreme"], r["corrective_extreme"], r["first_meaningful"],
              r["corrective_destination"], r["room_pips"], r["continuation_invalidation"])
    for x in trades:
        print(x["opened_utc"], x["strategy"], x["direction"], x["pips"], x["classification"], "|", x["reason"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
