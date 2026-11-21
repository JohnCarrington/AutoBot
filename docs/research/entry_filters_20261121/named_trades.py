"""The named trades checked one by one with strategies/entry_filters.check at the live time and the live entry price
(data/records/GBPUSD/trades.jsonl), plus the switches-on replay's 07:55 Asian range breakout buy (PULLBACK_ENTRY moves
that entry from 07:35 to 07:55). Read-only. Run from the worktree:
    AUTOBOT_ENV_FILE=/opt/autobot/.env PYTHONPATH=. .venv/bin/python docs/research/entry_filters_20261121/named_trades.py
"""
import json, sys
from datetime import datetime, timezone
from decimal import Decimal
from config.settings_loader import load_or_exit
from config.pairs import choose_pair
from prices.store import CandleStore
from analyser.market_state import MemoStore
from strategies import entry_filters as ef
from strategies.common import Idea
s = choose_pair(load_or_exit(), "GBPUSD")
st = MemoStore(CandleStore(s.candles.folder, s.candles.compress_after_days))
recs = [json.loads(l) for l in open("/opt/autobot/data/records/GBPUSD/trades.jsonl")]
recs = [r for r in recs if r["event"] == "opened" and not r.get("paper")]
want = [("2026-11-19T07:35", "Asian range breakout"), ("2026-11-20T13:10", "level reversal"),
        ("2026-11-20T13:25", "slow grind"), ("2026-11-19T12:10", "session sweep")]
for t0, strat in want:
    r = next(r for r in recs if r["opened_utc"].startswith(t0) and r["strategy"] == strat)
    t = datetime.fromisoformat(r["opened_utc"].replace("Z", "+00:00"))
    i = Idea("GBPUSD", strat, r["direction"], t, Decimal(r["entry_price"]), "", "", None, "", [])
    v = ef.check(s, st, i)
    ctx = ef.hourly_context(s, st, t); piv = ef.daily_pivot(s, st, t); e8 = ef.ema8_at(s, st, t)[0]
    print(f"{t0} {strat} {r['direction']} entry {r['entry_price']} -> allowed={v.allowed} {v.rule}")
    print(f"   context: {ctx.why}")
    print(f"   pivot {piv}, 50 EMA {ctx.ema50:.1f}, 5m 8 EMA {e8:.1f}; entry-pivot {Decimal(r['entry_price'])-piv:+.1f}, entry-EMA50 {Decimal(r['entry_price'])-ctx.ema50:+.1f}, entry-EMA8 {Decimal(r['entry_price'])-e8:+.1f}")
    print("   ", v.why or v.checked)
t = datetime(2026, 11, 19, 7, 55, tzinfo=timezone.utc)
i = Idea("GBPUSD", "Asian range breakout", "buy", t, Decimal("13152.2"), "", "", None, "", [])
v = ef.check(s, st, i); ctx = ef.hourly_context(s, st, t); piv = ef.daily_pivot(s, st, t); e8 = ef.ema8_at(s, st, t)[0]
print(f"2026-11-19T07:55 (replay) Asian range breakout buy entry 13152.2 -> allowed={v.allowed} {v.rule}")
print(f"   context: {ctx.why}")
print(f"   pivot {piv}, 50 EMA {ctx.ema50:.1f}, 5m 8 EMA {e8:.1f}; entry-pivot {Decimal('13152.2')-piv:+.1f}, entry-EMA50 {Decimal('13152.2')-ctx.ema50:+.1f}, entry-EMA8 {Decimal('13152.2')-e8:+.1f}")
