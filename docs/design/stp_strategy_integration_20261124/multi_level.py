"""Offline check (item 4): how many watcher setups/triggers one rejection gives when several levels sit in one zone."""
from datetime import datetime, timedelta, UTC
from decimal import Decimal as D
from types import SimpleNamespace as NS
from config.settings_loader import load_settings
from prices.model import Candle
from rejection.watch import RejectionWatcher
s = load_settings().for_pair("GBPUSD")
t0 = datetime(2026, 11, 24, 18, 0, tzinfo=UTC)
def c(i, o, h, l, cl):   # sell prices in points; buy = sell + 1.2 pips
    sp = D("1.2")
    return Candle("5m", t0 + timedelta(minutes=5*i), t0 + timedelta(minutes=5*(i+1)), D(o)+sp, D(h)+sp, D(l)+sp, D(cl)+sp, D(o), D(h), D(l), D(cl))
# STP SELL zone 13117.6-13128.6 with the weekly pivot 13127.3 inside: three stp_zone levels
_L=[NS(price=D(p), type="stp_zone") for p in ("13117.6", "13127.3", "13128.6")]
lv = NS(levels=_L, group_of=lambda x: {"group": 1, "lined_up": False, "members": _L})
def run(cs, label):
    w = RejectionWatcher(s, design_only=True)
    ev = []
    for x in cs:
        ev += w.on_candle(x, None, lv)
    st = [e for e in ev if e.kind == "pierce"]
    tr = [e for e in ev if e.kind == "trigger"]
    print(label, "| setups:", len(w.setups), "| pierced per setup:", [len(x.pierced) for x in w.setups],
          "| confirmations:", sum(e.kind == "confirmation" for e in ev), "| triggers (candle):", len(tr))
# A: one green candle pierces all three levels, then red reversal, confirmation close below the reversal low
run([c(0, "13115", "13130", "13114", "13126"), c(1, "13126", "13127", "13119", "13120"), c(2, "13120", "13121", "13114", "13115"),
     c(3, "13115", "13116", "13110", "13111")], "A one candle, three levels")
# B: two consecutive green candles each reach a different level (edge, then pivot), one red reversal, confirmation
run([c(0, "13114", "13118", "13113", "13117"), c(1, "13117", "13127.5", "13116", "13126"), c(2, "13126", "13127", "13119", "13120"),
     c(3, "13120", "13121", "13114", "13115"), c(4, "13115", "13116", "13110", "13111")], "B two candles, two levels")

def detail(cs, label):
    w = RejectionWatcher(s, design_only=True); ev = []
    for x in cs: ev += w.on_candle(x, None, lv)
    print(label)
    for e in ev:
        if e.kind in ("pierce", "confirmation", "trigger"):
            print("   ", e.kind, "setup", e.setup, e.direction, e.time.strftime("%H:%M"), e.price)
detail([c(0, "13114", "13118", "13113", "13117"), c(1, "13117", "13127.5", "13116", "13126"), c(2, "13126", "13127", "13119", "13120"),
     c(3, "13120", "13121", "13114", "13115"), c(4, "13115", "13116", "13110", "13111")], "B detail")
