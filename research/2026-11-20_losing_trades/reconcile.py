"""Read-only reconciliation of the bot's live trades (data/records/GBPUSD/trades.jsonl and
data/orders/GBPUSD/orders.jsonl) against IG's own records (every data/orders/ig_check_result*.json
written by the price service's read-only IG check). Writes trades.csv next to this file.

Nothing here talks to IG or changes any file outside this folder.
"""
from __future__ import annotations

import csv
import glob
import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("/opt/autobot/data")
OUT = Path(__file__).resolve().parent
UTC = timezone.utc

# Price-service restarts ("Trading ON" in logs/prices.log*) and HEAD at that moment (git reflog).
VERSIONS = [
    ("2026-11-09T00:09:52", "f99efe1", "A first build"),
    ("2026-11-09T12:26:37", "2ff445f", "A first build"),
    ("2026-11-11T06:19:43", "addf1b8", "A first build"),
    ("2026-11-11T06:47:15", "dfa9075", "A first build"),
    ("2026-11-11T08:34:18", "02a8dfe", "A first build"),
    ("2026-11-11T14:56:48", "04b3a83", "A first build"),
    ("2026-11-11T17:37:51", "6ffa36f", "A first build"),
    ("2026-11-11T18:32:36", "6ffa36f", "A first build"),
    ("2026-11-12T18:07:26", "79c5dcf", "A first build"),
    ("2026-11-13T10:22:14", "d96de5f", "A first build"),
    ("2026-11-13T15:58:26", "d96de5f", "A first build"),
    ("2026-11-13T19:41:21", "e24c58f", "A first build"),
    ("2026-11-13T21:14:41", "1a65151", "A first build"),
    ("2026-11-13T21:41:35", "714d1c6", "A first build"),
    ("2026-11-14T06:19:19", "714d1c6", "A first build"),
    ("2026-11-15T00:16:58", "b5ca37a", "B hourly read"),
    ("2026-11-15T17:47:46", "9b61661", "B hourly read"),
    ("2026-11-16T23:07:38", "e595f6e", "B hourly read"),
    ("2026-11-16T23:47:07", "aea2275", "B hourly read"),
    ("2026-11-17T20:24:41", "233d054", "B hourly read"),
    ("2026-11-17T20:46:38", "cc70dc5", "B hourly read"),
    ("2026-11-18T13:36:02", "3d50353", "C analyser control"),
    ("2026-11-19T09:49:56", "d9e5d0e", "D stage 4"),
    ("2026-11-19T18:44:38", "02f6c7e", "E first-build-plus"),
]


def t(s: str) -> datetime:
    s = s.replace("Z", "")
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def version_at(opened: str) -> tuple[str, str]:
    v = ("?", "?")
    for start, commit, period in VERSIONS:
        if t(opened) >= t(start):
            v = (commit, period)
    return v


def load_ig():
    acts, txs = {}, {}
    for f in sorted(glob.glob(str(DATA / "orders" / "ig_check_result*.json"))):
        r = json.load(open(f))
        for a in r.get("activity") or [] if isinstance(r.get("activity"), list) else []:
            acts[(a.get("dealId"), a.get("date"), a.get("description"))] = a
        for x in r.get("transactions") or [] if isinstance(r.get("transactions"), list) else []:
            txs[(x.get("reference"), x.get("dateUtc"), x.get("size"))] = x
    return list(acts.values()), list(txs.values())


def main() -> None:
    acts, txs = load_ig()
    opened_by_deal = {a["dealId"]: a for a in acts if a.get("description", "").startswith("Position opened")}
    closes = {}
    amends = {}
    for a in acts:
        for act in (a.get("details") or {}).get("actions") or []:
            d = act.get("affectedDealId")
            if act.get("actionType") in ("POSITION_CLOSED", "POSITION_PARTIALLY_CLOSED"):
                closes.setdefault(d, []).append(a)
            if act.get("actionType") == "STOP_LIMIT_AMENDED":
                amends.setdefault(d, []).append(a)

    journal = [json.loads(l) for l in open(DATA / "orders" / "GBPUSD" / "orders.jsonl")]
    sending = {j["reference"]: j for j in journal if j["event"] == "sending"}
    rec_open, rec_close = {}, {}
    for l in open(DATA / "records" / "GBPUSD" / "trades.jsonl"):
        r = json.loads(l)
        if r.get("paper"):
            continue
        (rec_open if r["event"] == "opened" else rec_close)[r["reference"]] = r

    rows = []
    for ref, o in sorted(rec_open.items(), key=lambda kv: kv[1]["opened_utc"]):
        c = rec_close.get(ref, {})
        s = sending.get(ref, {})
        deal = o.get("deal_id")
        ig_o = opened_by_deal.get(deal)
        ig_c = sorted(closes.get(deal, []), key=lambda a: a["date"])
        # transactions: match on open time (±3 s) and open level; reference is NOT the open deal id
        tx = []
        if ig_o:
            for x in txs:
                if x.get("openDateUtc") and abs((t(x["openDateUtc"]) - t(ig_o["date"])).total_seconds()) <= 3 \
                        and float(x["openLevel"]) == float(ig_o["details"]["level"]):
                    tx.append(x)
        sign = 1 if o["direction"] == "buy" else -1
        ig_open_lvl = ig_o["details"]["level"] if ig_o else None
        ig_close_lvl = None
        if tx:
            # size-weighted close if partial
            tot = sum(abs(float(x["size"])) for x in tx)
            ig_close_lvl = sum(float(x["closeLevel"]) * abs(float(x["size"])) for x in tx) / tot
        elif ig_c:
            ig_close_lvl = ig_c[-1]["details"]["level"]
        ig_pips = round(sign * (ig_close_lvl - ig_open_lvl), 1) if (ig_close_lvl is not None and ig_open_lvl is not None) else None
        ig_gbp = sum(float(x["profitAndLoss"].replace("£", "").replace("£", "")) for x in tx) if tx else None
        commit, period = version_at(o["opened_utc"])
        rows.append({
            "period": period, "commit": commit,
            "opened_utc": o["opened_utc"], "closed_utc": c.get("closed_utc", "OPEN"),
            "strategy": o["strategy"], "direction": o["direction"],
            "idea_price": s.get("idea_price", o.get("entry_price")),
            "ig_open": ig_open_lvl if ig_open_lvl is not None else o.get("open_price"),
            "rule_stop_pips": s.get("stop_pips", ""), "sent_stop_distance": s.get("stop_distance", ""),
            "ig_stop_level": ig_o["details"]["stopLevel"] if ig_o else "",
            "ig_stop_distance": ig_o["details"]["stopDistance"] if ig_o else "",
            "ig_limit_level": ig_o["details"]["limitLevel"] if ig_o else "",
            "tp_pips": s.get("take_profit_pips", o.get("take_profit_pips")),
            "close_price_ig": ig_close_lvl if ig_close_lvl is not None else "",
            "close_price_bot": c.get("close_price", ""),
            "ig_pips": ig_pips if ig_pips is not None else "", "bot_pips": c.get("pips", ""),
            "ig_gbp": ig_gbp if ig_gbp is not None else "", "bot_gbp": c.get("gbp", ""),
            "how_closed": c.get("how_closed", ""), "closed_by": c.get("closed_by") or ("bot" if c else ""),
            "ig_close_channel": ig_c[-1]["channel"] if ig_c else "",
            "stop_amends": len(amends.get(deal, [])),
            "market_state": o.get("market_state", ""), "best_pips": c.get("best_pips", ""),
            "minutes_open": c.get("minutes_open", ""),
            "deal_id": deal, "reference": ref,
            "ig_open_found": bool(ig_o), "ig_tx_found": bool(tx),
            "reason": o.get("reason", "")[:200],
        })
    with open(OUT / "trades.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    miss_o = [r for r in rows if not r["ig_open_found"]]
    miss_c = [r for r in rows if r["closed_utc"] != "OPEN" and r["close_price_ig"] == ""]
    print(len(rows), "trades;", len(miss_o), "without IG open;", len(miss_c), "without IG close")
    for r in miss_o + miss_c:
        print("  missing:", r["opened_utc"], r["closed_utc"], r["strategy"], r["deal_id"])


if __name__ == "__main__":
    main()
