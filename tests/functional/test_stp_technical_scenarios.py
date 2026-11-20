"""Functional tests for the STP technical forecast (planner/technical.py, GitHub issue #3): made-up GBP/USD markets built
from price paths into 5-minute, hourly, 4-hour, daily and weekly candles exactly as the price service builds them
(tests/planner_helpers.py). Each market is the planner scenarios' base (a week's range, a rally, then a 4-hour downtrend
ending near 12610) plus an ending that draws the chart pattern under test. No real candles, no IG, no orders.

Covered (issue #3, functional list): bearish H1 EMA20 pullback SELL; bullish mirror BUY; support bounce under a bearish
4-hour trend (countertrend); range-boundary rejection; breakout continuation; false breakout; low-confidence
abstention; intermediate target then reversal; an 8-15-pip opportunity; a volatility overshoot that does not end the
forecast's structure.
"""
import math
from datetime import timedelta
from decimal import Decimal as D
from functools import lru_cache

from planner.technical import BREAKOUT, FAILED_BREAKOUT, PULLBACK, RANGE_REVERSAL, REVERSAL, describe, technical_at
from tests.functional.test_planner_scenarios import S, START, waypoints
from tests.planner_helpers import Over, market, mirrored, section

PULLBACK_END = ((10, -70), (20, -120), (27, -100), (27.4, -90), (28, -99), (29, -101))
BOUNCE_END = ((6, -80), (12, -150), (12.5, -184), (13, -160), (14, -157))
TARGET_THEN_REVERSAL_END = PULLBACK_END + ((33, -112), (33.5, -126), (34, -112), (35, -110))


def _range_base():
    w, h = [], 0
    for _ in range(8):                                   # 64 hours between about 12580 and 12620, a flat EMA
        h += 4
        w.append((h, -30))
        h += 4
        w.append((h, 10))
    return w, h


def _range_end(kind):
    w, h = _range_base()
    tail = {"rejection": [(3, -12), (6, 6), (6.4, 11), (7, 3), (8, 1)],
            "breakout": [(3, -12), (6, 6), (7, 25), (8, 24), (9, 26)],
            "false": [(3, -12), (6, 6), (7, 20), (8, 4), (9, 2)]}[kind]
    return tuple(w + [(h + a, b) for a, b in tail])


@lru_cache(maxsize=None)
def store(ending, mirror=False):
    st = market(S, START, waypoints(list(ending)))
    return mirrored(st) if mirror else st


def at_end(st, settings=S):
    t = st.by_tf["5m"][-1].end
    return technical_at(settings, st, t)


def opp(f):
    assert f["opportunity"], f.get("no_opportunity")
    return f["opportunity"]


def texts(o):
    return " | ".join(e["text"] for e in o["evidence"])


# ---- 1-2. trend-continuation pullback and its mirror ------------------------------------------------------------------

def test_1_bearish_h1_ema20_pullback_gives_a_sell_at_the_ema_with_the_reasons():
    f = at_end(store(PULLBACK_END))
    o = opp(f)
    assert o["type"] == PULLBACK and o["trade"] == "SELL" and not o["countertrend"]
    ema = D(f["chart"]["h1_ema20"])
    assert D(o["entry_zone"]["low"]) <= ema <= D(o["entry_zone"]["high"])
    assert D(o["stop"]["price"]) > D(o["entry_zone"]["high"]) and D(o["intermediate_target"]["price"]) < D(f["price"])
    t = texts(o)
    for must in ("4-hour direction (existing STP) is BEARISH", "H1 EMA20 falling", "the pullback has reached the EMA zone",
                 "doji", "H1 structure down"):
        assert must in t
    lines = "\n".join(describe(f))
    assert "trend-continuation pullback - SELL" in lines and "Alternative:" in lines and "Structural invalidation" in lines


def test_2_the_bullish_mirror_gives_the_mirror_buy():
    a, b = opp(at_end(store(PULLBACK_END))), opp(at_end(store(PULLBACK_END, mirror=True)))
    assert (b["type"], b["trade"]) == (PULLBACK, "BUY") and b["score"] == a["score"]
    assert D(b["stop"]["price"]) < D(b["entry_zone"]["low"]) and D(b["intermediate_target"]["price"]) > D(b["entry_zone"]["high"])


# ---- 3. reversal at support against a bearish 4-hour trend --------------------------------------------------------------

def test_3_a_support_bounce_is_forecast_even_under_a_bearish_4_hour_trend_and_marked_countertrend():
    f = at_end(store(BOUNCE_END))
    assert f["h4_direction"] == "BEARISH"
    o = opp(f)
    assert (o["type"], o["trade"], o["countertrend"]) == (REVERSAL, "BUY", True)
    t = texts(o)
    assert "bullish rejection" in t and "turning from below 30" in t and "lower band" in t
    assert any(e["points"] == -1 and "countertrend" in e["text"] for e in o["evidence"])
    assert D(o["stop"]["price"]) < D(o["entry_zone"]["low"])


# ---- 4-6. range boundary, breakout, false breakout -------------------------------------------------------------------

def test_4_a_rejection_at_the_top_of_a_range_found_from_the_candles_gives_a_sell():
    f = at_end(store(_range_end("rejection")))
    assert f["chart"]["range"] and "top tested" in f["chart"]["range"]
    o = opp(f)
    assert o["trade"] == "SELL" and o["type"] in (REVERSAL, RANGE_REVERSAL)
    assert "bearish rejection" in texts(o)
    kinds = {x["type"] for x in f["candidates"]}
    zone = o["entry_zone"]["low"] + "-" + o["entry_zone"]["high"]
    assert RANGE_REVERSAL in kinds
    assert not any(x["trade"] == "BUY" and x["entry_zone"] == zone for x in f["candidates"])   # never both ways


def test_5_a_confirmed_breakout_that_holds_gives_a_buy_on_the_retest():
    f = at_end(store(_range_end("breakout")))
    o = opp(f)
    assert (o["type"], o["trade"]) == (BREAKOUT, "BUY")
    assert "confirmed H1 close" in texts(o) and "still holding" in texts(o)
    top = D(f["chart"]["range"].split("range ")[1].split("-")[1].split(" ")[0])
    assert D(o["entry_zone"]["low"]) <= top <= D(o["entry_zone"]["high"])         # the retest of the broken top
    assert D(o["structural_invalidation"]["price"]) < D(o["entry_zone"]["low"])


def test_6_a_false_breakout_back_inside_gives_a_sell():
    f = at_end(store(_range_end("false")))
    o = opp(f)
    assert o["trade"] == "SELL" and o["type"] in (FAILED_BREAKOUT, RANGE_REVERSAL)
    assert any(x["type"] == FAILED_BREAKOUT and x["trade"] == "SELL" for x in f["candidates"])
    assert D(o["stop"]["price"]) > D(o["entry_zone"]["high"])


# ---- 7. low confidence: no forcing ---------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def sideways():
    w, h = [(0, 12300)], 0
    for i in range(170):
        h += 4 + (i % 3)
        w.append((h, 12300 + round(28 * math.sin(i * 1.9) + 11 * math.sin(i * 0.37), 1)))
    return market(S, START, w)


def test_7a_a_sideways_market_without_a_set_up_gives_no_forecast_and_says_why():
    f = at_end(sideways())
    assert f["opportunity"] is None and f["no_opportunity"].startswith("no credible opportunity")


def test_7b_evidence_below_the_minimum_gives_no_forecast_but_shows_the_best_candidate():
    strict = Over(S, stp_technical=section(S.stp_technical, min_evidence=20))
    f = at_end(store(PULLBACK_END), strict)
    assert f["opportunity"] is None and "below the minimum 20" in f["no_opportunity"]
    assert f["best_candidate"]["type"] == PULLBACK


# ---- 8. intermediate target, then a reversal there ----------------------------------------------------------------------

def test_8_after_the_sell_reaches_its_intermediate_target_the_support_there_is_seen_as_a_reversal_zone():
    first = opp(at_end(store(PULLBACK_END)))
    t1 = D(first["intermediate_target"]["price"])
    st = store(TARGET_THEN_REVERSAL_END)
    later = at_end(st)
    lows = [c.sell_low for c in st.by_tf["1h"][-3:]]
    assert min(lows) <= t1                                                            # the target was reached
    buys = [x for x in later["candidates"] if x["trade"] == "BUY" and x["type"] in (REVERSAL, FAILED_BREAKOUT)]
    assert buys and any(D(x["entry_zone"].split("-")[0]) <= t1 + 1 for x in buys)    # a reaction at that support


# ---- 9. an 8-15-pip opportunity is a real opportunity -------------------------------------------------------------------

def test_9_an_opportunity_with_an_8_to_15_pip_target_is_issued():
    for st in (store(PULLBACK_END), store(BOUNCE_END)):
        o = opp(at_end(st))
        assert 8 <= D(o["intermediate_target"]["pips_from_entry"]) <= 15


# ---- 10. a volatility overshoot does not end the forecast's structure --------------------------------------------------

def test_10_a_3_pip_overshoot_of_the_zone_is_inside_the_stop_buffer_and_short_of_the_structural_invalidation():
    for st in (store(PULLBACK_END), store(BOUNCE_END), store(_range_end("false"))):
        f = at_end(st)
        o = opp(f)
        sell = o["trade"] == "SELL"
        edge = D(o["entry_zone"]["high"] if sell else o["entry_zone"]["low"])
        overshoot = edge + 3 if sell else edge - 3
        stop, struct = D(o["stop"]["price"]), D(o["structural_invalidation"]["price"])
        assert (overshoot <= stop < struct) if sell else (overshoot >= stop > struct)
        assert o["trade_invalidation"].startswith("price touches the stop")


def test_10b_the_forecast_survives_an_hour_that_overshoots_its_zone_by_3_pips():
    st = store(PULLBACK_END)
    f0 = at_end(st)
    o0 = opp(f0)
    t = st.by_tf["5m"][-1].end
    hi0 = D(o0["entry_zone"]["high"])
    over = PULLBACK_END + ((29.5, float(hi0 - 12610 + 3)), (30, -101))
    st2 = store(over)
    f1 = technical_at(S, st2, st2.by_tf["5m"][-1].end)
    assert max(c.sell_high for c in st2.by_tf["5m"] if c.start >= t) >= hi0 + 2
    assert f1["opportunity"] and f1["opportunity"]["trade"] == "SELL"
    assert D(f1["price"]) < D(o0["structural_invalidation"]["price"])
    assert timedelta(0) < st2.by_tf["5m"][-1].end - t <= timedelta(hours=2)
