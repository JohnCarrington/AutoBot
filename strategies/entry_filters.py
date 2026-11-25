"""The entry filters (owner, 21 November 2026; rule 3, 23 November 2026): the rules checked once for every trade, at one point, just before it
opens (trading/engine.py, Trading._place, before the order sender's safety rules). No strategy's own code changes;
each strategy's rules, stops, take profits and trade management stay as they are. Each rule has its own switch.

RULE 1. HOURLY CONTEXT (switch HOURLY_CONTEXT, on if left out). Every strategy except the breakout and the Asian range
  breakout (owner, 21 November 2026: a breakout is meant to push through a level).
  DOWN context: the last two hourly swing highs are lower highs (the latest swing high is lower than the one before
  it), AND the last finished hourly candle closed below the hourly 50 EMA, AND the hourly 50 EMA is falling (lower
  than [entry_filters] hourly_ema_slope_candles (6) hourly candles before).
  UP context: the mirror: the latest hourly swing low is higher than the one before it, the last hourly close is
  above the 50 EMA, and the 50 EMA is rising.
  In a DOWN context no BUY opens when the entry price is within hourly_context_near_pips (5) of the daily pivot or
  the hourly 50 EMA; in an UP context no SELL opens when the entry price is within 5 pips of either.
  A swing high: an hourly candle whose high has hourly_swing_candles_each_side (2) lower hourly highs on each side
  (a swing low: 2 higher lows on each side); only finished hourly candles, so a swing is known 2 hours after it.

RULE 2. ENTRY LOCATION (switch ENTRY_NEAR_EMA8, OFF if left out since 21 November 2026, replaced by rule 2b; kept).
  A SELL opens only if the entry price is no more than ema8_max_distance_pips (5) below the 5-minute 8 EMA (at it,
  above it, or up to 5 pips below); a BUY only if it is no more than 5 pips above it. The 8 EMA on the sell price at
  the last finished 5-minute candle before the entry. The slow grind, the breakout, the Asian range breakout and the
  session sweep are exempt (the session sweep: owner, 21 November 2026, after the check of the 19 November 12:10 sell).

RULE 2b. RSI STRETCH (switch RSI_STRETCH, on if left out; owner, 21 November 2026, in place of rule 2).
  No SELL when the 5-minute RSI 3 is under rsi_sell_below (30); no BUY when it is over rsi_buy_above (70). RSI 3 on the
  sell price, Wilder's smoothing (prices/indicators.py), at the last finished 5-minute candle before the entry.
  Exempt: the slow grind, the breakout, the Asian range breakout and the session sweep.

RULE 3. COUNTER-TREND TIRING (switch COUNTER_TREND_TIRING, on if left out; owner, 23 November 2026; Johnny's rule of
  21 October 2026: "A bounce against an established trend is allowed only when the trend is tiring (MACD 35/45/30
  histogram shrinking); otherwise blocked."). The reversal-type strategies only: the Bollinger bounce (hourly), the
  Bollinger bounce 5m, the level reversal, the session sweep and the New York open reversal.
  Against the trend: the analyser's state at the time is "trend" (slow grind or strong push; "emerging trend" and
  "possible reversal" do not count) and the trade is the other way: a BUY in a trend down, a SELL in a trend up.
  Tiring: the HOURLY MACD 35/45/30 histogram (sell price, [indicators] periods) at the last finished hourly candle
  before the entry, against the hourly candle before it (1 bar):
    trend down: allowed if the histogram has crossed above zero, or is higher (closer to zero) than the bar before;
    trend up:   allowed if the histogram has crossed below zero, or is lower (closer to zero) than the bar before.
  Also allowed (owner, 23 November 2026, Johnny's addition): the 5-MINUTE MACD 35/45/30 histogram (sell price) at the
  last finished 5-minute candle before the entry has crossed zero onto the bounce's side: above zero for a buy
  (against a trend down), below zero for a sell (against a trend up). Exactly zero is not across.
  Otherwise (the hourly the same, or further from zero on the trend's side, including just crossing back onto it,
  and the 5-minute not across zero) refused.
  The owner's answers (23 November 2026): hourly chart; 1 bar; past zero counts as tiring; the trend state only.
  The 5-minute MACD not warmed up: only the hourly decides.
  Not enough hourly candles for a warmed-up MACD: not checked (recorded), as with the other rules.
  Each refusal records the strategy, the analyser state and the MACD values.
  Two changes (owner, 24 November 2026), each behind its own switch, both on if left out:
  * COUNTER_TREND_EMERGING: rule 3 also applies when the analyser's state is "emerging trend" (in its direction), not
    only "trend".
  * COUNTER_TREND_HOURLY_CONFIRMED: a histogram on the bounce's side of zero that never went to the trend's side is
    NOT tiring: the hourly has not confirmed the trend yet. Past zero counts as tiring only if the histogram was on the
    trend's side (below zero in a trend down, above in a trend up) at an hourly candle since the analyser's current
    state began (the owner's answer: since the state began), before the last finished one. Shrinking counts only while
    the histogram is on the trend's side (the owner's answer). Exactly zero is not on either side. If the state's start
    is not known, only the hourly candle before the last finished one is looked at. Everything else unchanged,
    including the 5-minute zero-cross. The slow-grind trend day is not used by rule 3 (the owner's answer: no link yet).

EMA PULLBACK R3/S3 (switch EMA_PULLBACK_NO_R3_S3, off if left out; owner, 25 November 2026). The EMA pullback only: no
  BUY when the entry price is at or above the day's R3, no SELL when it is at or below the day's S3, from the bot's
  daily pivot levels (levels/current.py). No R3 (or S3) in the levels: not checked (recorded), as with the other rules.

THE SLOW-GRIND TREND DAY (switch TREND_DAY_RSI_OFF, on if left out; owner, 21 November 2026). Johnny's trend day, not
the bot's own trend-day check (analyser/trend_day.py). It starts the first time a slow grind trade is in profit (more
than 0 pips at the price IG would close it: the sell price for a buy, the buy price for a sell) at any moment from
trend_day_from (06:00) up to trend_day_until (09:00) UK, in that trade's direction; a slow grind trade opened before
06:00 counts once it is in profit from 06:00. It lasts until trend_day_ends_at (20:30) UK, the bot's close. If a slow
grind trade in the OTHER direction is also in profit inside 06:00-09:00 that day, the trend day is cancelled for the
rest of the day (owner's answers). On a trend day rule 2b does not apply to trades in the trend's direction; trades
against it are still checked. Rule 1 (and rule 2, if switched on) unchanged. Live it is checked on every price; in a
replay on the 5-minute candles. Its start and any cancel are recorded (decisions.jsonl) and shown on the dashboard.

The owner's answers (21 November 2026): the entry price is the strategy's own entry price (the sell / chart price,
as the bot records entry_price), for buys too; "price below / above the hourly 50 EMA" is the last finished hourly
candle's close against the 50 EMA at that candle. Everything is on the chart (sell) price: the hourly candles, the
50 EMA, the 8 EMA and the daily pivot (the bot's own pivot, levels/current.py). "Within 5 pips" includes exactly 5;
"no more than 5 pips" allows exactly 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.indicators import last_candles
from analyser.states import EMERGING, TREND, switch_on
from levels.current import build as build_levels
from levels.rules import PIVOT, R3, S3
from prices.indicators import ema, macd, needs_macd, rsi
from prices.model import plain
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BREAKOUT, EMA_PULLBACK,
                               LEVEL_REVERSAL, NEW_YORK_OPEN_REVERSAL, SESSION_SWEEP, SLOW_GRIND)

HOURLY_CONTEXT = "hourly context"
HOURLY_EXEMPT = (BREAKOUT, ASIAN_RANGE_BREAKOUT)                                   # owner, 21 November 2026
ENTRY_NEAR_EMA8 = "entry near the 8 EMA"
EMA8_EXEMPT = (SLOW_GRIND, BREAKOUT, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP)          # owner, 21 November 2026
RSI_STRETCH = "RSI stretch"
RSI_EXEMPT = (SLOW_GRIND, BREAKOUT, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP)           # owner, 21 November 2026
COUNTER_TREND_TIRING = "counter-trend tiring"
COUNTER_TREND_STRATEGIES = (BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, LEVEL_REVERSAL, SESSION_SWEEP,
                            NEW_YORK_OPEN_REVERSAL)                                 # owner, 23 November 2026
EMA_PULLBACK_NO_R3_S3 = "EMA pullback R3/S3"                                      # owner, 25 November 2026
TREND_DAY_STARTED, TREND_DAY_CANCELLED = "trend day started", "trend day cancelled"
DOWN, UP = "down", "up"


@dataclass
class Context:
    """The hourly context at a moment: DOWN, UP or None, with what it was worked out from."""
    kind: str | None
    why: str
    ema50: Decimal | None = None
    ema50_before: Decimal | None = None
    close: Decimal | None = None
    swings: tuple = ()                                   # (earlier, latest) swing highs (DOWN) or lows (UP): (time, price)


@dataclass
class Verdict:
    allowed: bool
    rule: str = ""                                       # the rule that refused it ("" when allowed)
    why: str = ""                                        # one line, for the records
    details: dict = field(default_factory=dict)          # the numbers, for the records
    checked: list[str] = field(default_factory=list)     # what was checked (allowed or not), for the records


def swings(candles: list, side: str, each_side: int, high: bool) -> list:
    """[(time, price)] of every swing high (high=True) or swing low in `candles`, oldest first: a candle whose high
    has `each_side` strictly lower highs on each side (a low: strictly higher lows)."""
    vals = [getattr(c, f"{side}_high" if high else f"{side}_low") for c in candles]
    out = []
    for i in range(each_side, len(vals) - each_side):
        others = vals[i - each_side:i] + vals[i + 1:i + 1 + each_side]
        if all((v < vals[i]) if high else (v > vals[i]) for v in others):
            out.append((candles[i].start, vals[i]))
    return out


def hourly_context(settings: Any, store: Any, at: datetime) -> Context:
    f, side = settings.entry_filters, settings.chart.price
    hc = last_candles(store, "1h", at, settings.indicators.history_candles)
    k = f.hourly_ema_slope_candles
    if len(hc) < f.hourly_ema_periods + k:
        return Context(None, f"not enough finished hourly candles ({len(hc)}) for the 50 EMA and its slope: "
                             "no context")
    e = ema(hc, side, f.hourly_ema_periods)
    last, before = hc[-1], hc[-1 - k]
    e_now, e_before = e.get(last.start), e.get(before.start)
    close = getattr(last, f"{side}_close")
    if e_now is None or e_before is None:
        return Context(None, "the hourly 50 EMA is not worked out yet: no context")
    highs = swings(hc, side, f.hourly_swing_candles_each_side, True)
    lows = swings(hc, side, f.hourly_swing_candles_each_side, False)
    hh = f"{last.start:%a %d %b %H:%M}"
    base = (f"last hourly close {plain(close)} ({hh} candle), 50 EMA {e_now:.1f}, {k} candles before {e_before:.1f}")
    if len(highs) >= 2 and highs[-1][1] < highs[-2][1] and close < e_now and e_now < e_before:
        return Context(DOWN, f"DOWN context: lower high {plain(highs[-1][1])} ({highs[-1][0]:%a %H:%M}) after "
                             f"{plain(highs[-2][1])} ({highs[-2][0]:%a %H:%M}); {base}: close below it and falling",
                       e_now, e_before, close, (highs[-2], highs[-1]))
    if len(lows) >= 2 and lows[-1][1] > lows[-2][1] and close > e_now and e_now > e_before:
        return Context(UP, f"UP context: higher low {plain(lows[-1][1])} ({lows[-1][0]:%a %H:%M}) after "
                           f"{plain(lows[-2][1])} ({lows[-2][0]:%a %H:%M}); {base}: close above it and rising",
                       e_now, e_before, close, (lows[-2], lows[-1]))
    parts = []
    if len(highs) >= 2:
        parts.append(f"swing highs {plain(highs[-2][1])} then {plain(highs[-1][1])}")
    if len(lows) >= 2:
        parts.append(f"swing lows {plain(lows[-2][1])} then {plain(lows[-1][1])}")
    return Context(None, "no DOWN or UP context: " + "; ".join(parts + [base]), e_now, e_before, close)


def daily_pivot(settings: Any, store: Any, at: datetime) -> Decimal | None:
    """The daily pivot as the bot's levels had it at `at` (levels/current.py)."""
    for lv in build_levels(settings, store, at).levels:
        if lv.type == PIVOT:
            return lv.price
    return None


def ema8_at(settings: Any, store: Any, at: datetime) -> tuple[Decimal | None, Any]:
    """The 5-minute 8 EMA (sell price) at the last 5-minute candle finished by `at`, and that candle."""
    f = settings.entry_filters
    c5 = last_candles(store, "5m", at, settings.indicators.history_candles)
    if len(c5) < f.ema8_periods:
        return None, None
    return ema(c5, settings.chart.price, f.ema8_periods).get(c5[-1].start), c5[-1]


def rsi3_at(settings: Any, store: Any, at: datetime) -> tuple[Decimal | None, Any]:
    """The 5-minute RSI 3 (sell price) at the last 5-minute candle finished by `at`, and that candle."""
    c5 = last_candles(store, "5m", at, settings.indicators.history_candles)
    if not c5:
        return None, None
    return rsi(c5, settings.chart.price, settings.entry_filters.rsi_periods).get(c5[-1].start), c5[-1]


def hourly_macd(settings: Any, store: Any, at: datetime) -> tuple[Any, Any, str]:
    """(the hourly MACD 35/45/30 at the last hourly candle finished by `at`, at the hourly candle before it, why not)
    on the sell price; (None, None, why) when there are too few hourly candles for a warmed-up MACD."""
    ind = settings.indicators
    hc = last_candles(store, "1h", at, settings.indicators.history_candles)
    need = needs_macd(ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods,
                      ind.warm_up_seed_weight_percent) + 1
    if len(hc) < need:
        return None, None, f"only {len(hc)} finished hourly candles, {need} needed for the hourly MACD and the bar before"
    m = macd(hc, settings.chart.price, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    last, before = m.get(hc[-1].start), m.get(hc[-2].start)
    if last is None or before is None:
        return None, None, "the hourly MACD is not worked out yet"
    return last, before, ""


def hourly_trend_side_since(settings: Any, store: Any, at: datetime, since: datetime | None, last: Any,
                            down: bool) -> tuple[bool, str]:
    """COUNTER_TREND_HOURLY_CONFIRMED: was the hourly MACD 35/45/30 histogram on the trend's side of zero (below zero
    for a trend down, above for a trend up) at an hourly candle since `since` (the analyser's state began), before the
    last finished one (`last`)? Returns (yes, the hourly candle it was so at, or why not, for the record)."""
    ind = settings.indicators
    hc = last_candles(store, "1h", at, settings.indicators.history_candles)
    m = macd(hc, settings.chart.price, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    before_last = [c for c in hc if c.start < last.candle_utc]
    if since is None:
        window = before_last[-1:]
        span = "the hourly candle before (the state's start not known)"
    else:
        window = [c for c in before_last if c.end > since]
        span = f"since the state began at {since:%H:%M} UTC"
    for c in window:
        v = m.get(c.start)
        if v is not None and (v.histogram < 0 if down else v.histogram > 0):
            return True, f"on the trend's side at the {c.start:%H:%M} hourly candle ({v.histogram:.2f}), {span}"
    return False, f"never on the trend's side {span}" if window else f"no finished hourly candle {span}"


def five_minute_macd(settings: Any, store: Any, at: datetime) -> tuple[Any, str]:
    """(the 5-minute MACD 35/45/30 at the last 5-minute candle finished by `at`, why not) on the sell price; (None, why)
    when there are too few 5-minute candles for a warmed-up MACD."""
    ind = settings.indicators
    c5 = last_candles(store, "5m", at, settings.indicators.history_candles)
    need = needs_macd(ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods,
                      ind.warm_up_seed_weight_percent)
    if len(c5) < need:
        return None, f"only {len(c5)} finished 5-minute candles, {need} needed for the 5-minute MACD"
    m = macd(c5, settings.chart.price, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    last = m.get(c5[-1].start)
    return (last, "") if last is not None else (None, "the 5-minute MACD is not worked out yet")


def check(settings: Any, store: Any, idea: Any, trend: str | None = None) -> Verdict:
    """The rules, as their switches say, for one trade about to open. The first rule that refuses it is given.
    `trend`: the slow-grind trend day's direction now ("buy" or "sell"), or None (TrendDayWatch.direction_at)."""
    sw, f = settings.switches, settings.entry_filters
    ppp = Decimal(settings.market.points_per_pip)
    at, price, buy = idea.time, Decimal(idea.entry_price), idea.direction == "buy"
    checked: list[str] = []

    if sw.hourly_context and idea.strategy in HOURLY_EXEMPT:
        checked.append(f"hourly context: {idea.strategy} is exempt")
    elif sw.hourly_context:
        ctx = hourly_context(settings, store, at)
        against = (ctx.kind == DOWN and buy) or (ctx.kind == UP and not buy)
        if against:
            near = Decimal(f.hourly_context_near_pips)
            piv = daily_pivot(settings, store, at)
            lines = [("the daily pivot", piv)] + [("the hourly 50 EMA", ctx.ema50)]
            hits = [(name, lv, abs(price - lv) / ppp) for name, lv in lines if lv is not None and abs(price - lv) / ppp <= near]
            if hits:
                name, lv, dist = min(hits, key=lambda h: h[2])
                why = (f"{ctx.why}. A {idea.direction.upper()} at {plain(price)} is {dist:.1f} pips from {name} "
                       f"{lv:.1f} (within {plain(near)}): refused")
                return Verdict(False, HOURLY_CONTEXT, why, {
                    "context": ctx.kind, "entry_price": str(price), "line": name, "line_price": f"{lv:.1f}",
                    "pips_from_line": f"{dist:.1f}", "daily_pivot": None if piv is None else str(piv),
                    "hourly_ema50": f"{ctx.ema50:.1f}", "hourly_ema50_before": f"{ctx.ema50_before:.1f}",
                    "last_hourly_close": str(ctx.close),
                    "swings": [[f"{t:%Y-%m-%dT%H:%MZ}", str(p)] for t, p in ctx.swings]}, checked)
            checked.append(f"hourly context: {ctx.why}; the {idea.direction} is not within {plain(near)} pips of the "
                           f"daily pivot ({'none' if piv is None else plain(piv)}) or the 50 EMA ({ctx.ema50:.1f})")
        else:
            checked.append(f"hourly context: {ctx.why}")

    if sw.entry_near_ema8:
        if idea.strategy in EMA8_EXEMPT:
            checked.append(f"entry near the 8 EMA: {idea.strategy} is exempt")
        else:
            e8, c = ema8_at(settings, store, at)
            if e8 is None:
                checked.append("entry near the 8 EMA: the 5-minute 8 EMA is not worked out yet: not checked")
            else:
                limit = Decimal(f.ema8_max_distance_pips)
                beyond = (price - e8) / ppp if buy else (e8 - price) / ppp     # pips above (buy) / below (sell) it
                side = "above" if buy else "below"
                line = (f"entry {plain(price)}, 5-minute 8 EMA {e8:.1f} (at the {c.start:%H:%M} candle), "
                        f"{abs(beyond):.1f} pips {side if beyond >= 0 else ('below' if buy else 'above')} it")
                if beyond > limit:
                    why = (f"a {idea.direction.upper()} more than {plain(limit)} pips {side} the 5-minute 8 EMA: "
                           f"{line}: refused")
                    return Verdict(False, ENTRY_NEAR_EMA8, why, {
                        "entry_price": str(price), "ema8_5m": f"{e8:.1f}", "ema8_candle": f"{c.start:%Y-%m-%dT%H:%MZ}",
                        "pips_beyond_ema8": f"{beyond:.1f}", "limit_pips": str(limit)}, checked)
                checked.append(f"entry near the 8 EMA: {line}: allowed")

    if sw.rsi_stretch:
        if idea.strategy in RSI_EXEMPT:
            checked.append(f"RSI stretch: {idea.strategy} is exempt")
        elif trend is not None and trend == idea.direction:
            checked.append(f"RSI stretch: not applied: a {trend} trend day (slow grind), and this {idea.direction} is in "
                           "its direction")
        else:
            r3, c = rsi3_at(settings, store, at)
            if r3 is None:
                checked.append("RSI stretch: the 5-minute RSI 3 is not worked out yet: not checked")
            else:
                lo, hi = Decimal(f.rsi_sell_below), Decimal(f.rsi_buy_above)
                stretched = (r3 > hi) if buy else (r3 < lo)
                limit = f"over {plain(hi)}" if buy else f"under {plain(lo)}"
                td = "" if trend is None else f" (a {trend} trend day: this {idea.direction} is against it)"
                line = f"5-minute RSI 3 {r3:.1f} at the {c.start:%H:%M} candle"
                if stretched:
                    why = f"no {idea.direction.upper()} with the {line}, {limit}{td}: refused"
                    return Verdict(False, RSI_STRETCH, why, {
                        "strategy": idea.strategy, "rsi3_5m": f"{r3:.1f}", "rsi_candle": f"{c.start:%Y-%m-%dT%H:%MZ}",
                        "limit": limit, "entry_price": str(price), "trend_day": trend}, checked)
                checked.append(f"RSI stretch: {line}, not {limit}{td}: allowed")

    if getattr(sw, "counter_trend_tiring", False) and idea.strategy in COUNTER_TREND_STRATEGIES:
        state, sd = idea.state, idea.state_direction
        kind = f", {idea.trend_type}" if getattr(idea, "trend_type", None) else ""
        states = (TREND, EMERGING) if getattr(sw, "counter_trend_emerging", False) else (TREND,)
        confirm = getattr(sw, "counter_trend_hourly_confirmed", False)
        if not (state in states and ((sd == DOWN and buy) or (sd == UP and not buy))):
            checked.append(f"counter-trend tiring: the analyser says {state} {sd}{kind}: this {idea.direction} is not "
                           "against a trend")
        else:
            last, before, why_not = hourly_macd(settings, store, at)
            if last is None:
                checked.append(f"counter-trend tiring: {why_not}: not checked")
            else:
                h, hb = last.histogram, before.histogram
                down = sd == DOWN
                crossed = h > 0 if down else h < 0
                shrinking = h > hb if down else h < hb
                line = (f"a {idea.direction} against the {state} {sd}{kind}: hourly MACD 35/45/30 histogram {h:.2f} at "
                        f"the {last.candle_utc:%H:%M} candle, {hb:.2f} at the {before.candle_utc:%H:%M} candle before")
                trend_side_now = h < 0 if down else h > 0
                if confirm and crossed:
                    seen, how = hourly_trend_side_since(settings, store, at, getattr(idea, "state_since", None), last,
                                                        down)
                    if not seen:
                        crossed = False
                        line += f"; on the bounce's side of zero but {how}: the hourly has not confirmed the trend"
                    else:
                        line += f"; {how}"
                if confirm and shrinking and not trend_side_now:
                    shrinking = False
                    if "not confirmed" not in line:
                        line += "; not on the trend's side of zero, so not shrinking towards it"
                if crossed:
                    checked.append(f"counter-trend tiring: {line}: past zero, the trend is tiring: allowed")
                elif shrinking:
                    checked.append(f"counter-trend tiring: {line}: shrinking towards zero, the trend is tiring: allowed")
                else:
                    m5, why5 = five_minute_macd(settings, store, at)
                    h5 = None if m5 is None else m5.histogram
                    across5 = h5 is not None and (h5 > 0 if down else h5 < 0)
                    side5 = "above" if down else "below"
                    line5 = (f"5-minute MACD 35/45/30 histogram {h5:.2f} at the {m5.candle_utc:%H:%M} candle"
                             if m5 is not None else f"5-minute MACD: {why5}")
                    if across5:
                        checked.append(f"counter-trend tiring: {line}: not shrinking; but the {line5} has crossed "
                                       f"{side5} zero, onto the {idea.direction}'s side: allowed")
                    else:
                        why = (f"{line}: not shrinking, the trend is not tiring; the {line5} is not {side5} zero: "
                               "refused")
                        return Verdict(False, COUNTER_TREND_TIRING, why, {
                            "macd_5m_candle": None if m5 is None else f"{m5.candle_utc:%Y-%m-%dT%H:%MZ}",
                            "macd_5m_histogram": None if m5 is None else f"{h5:.2f}",
                            "macd_5m_line": None if m5 is None else f"{m5.line:.2f}",
                            "macd_5m_signal": None if m5 is None else f"{m5.signal:.2f}",
                            "strategy": idea.strategy, "analyser_state": state, "analyser_direction": sd,
                            "trend_type": getattr(idea, "trend_type", None), "entry_price": str(price),
                            "macd_timeframe": "1h", "macd_candle": f"{last.candle_utc:%Y-%m-%dT%H:%MZ}",
                            "macd_histogram": f"{h:.2f}", "macd_line": f"{last.line:.2f}",
                            "macd_signal": f"{last.signal:.2f}",
                            "macd_candle_before": f"{before.candle_utc:%Y-%m-%dT%H:%MZ}",
                            "macd_histogram_before": f"{hb:.2f}"}, checked)

    if idea.strategy == EMA_PULLBACK and switch_on(settings, "ema_pullback_no_r3_s3"):
        # EMA_PULLBACK_NO_R3_S3 (owner, 25 November 2026): no EMA pullback buy at or above the day's R3, no sell at or
        # below the day's S3 (the bot's daily pivot levels, levels/current.py), judged at the entry price
        name = R3 if buy else S3
        level = next((lv.price for lv in build_levels(settings, store, at).levels if lv.type == name), None)
        if level is None:
            checked.append(f"EMA pullback R3/S3: no {name} in the bot's levels: not checked")
        else:
            past = price >= level if buy else price <= level
            where = f"{'above' if price > level else 'below' if price < level else 'at'} the day's {name} {plain(level)}"
            line = f"the {idea.direction} entry {plain(price)} is {abs(price - level) / ppp:.1f} pips {where}"
            if past:
                return Verdict(False, EMA_PULLBACK_NO_R3_S3, f"no EMA pullback {idea.direction.upper()} at or "
                               f"{'above' if buy else 'below'} the day's {name}: {line}: refused", {
                                   "entry_price": str(price), "level": name, "level_price": str(level),
                                   "pips_from_level": f"{(price - level) / ppp:.1f}"}, checked)
            checked.append(f"EMA pullback R3/S3: {line}: allowed")
    return Verdict(True, checked=checked)


class TrendDayWatch:
    """Johnny's slow-grind trend day (see the module's docstring), one UK day at a time. `record(kind, t, **data)`
    keeps its start and cancel (the engine writes them to decisions.jsonl)."""

    def __init__(self, settings: Any, record: Any = None):
        from strategies.sessions import uk_zone
        self.s, self.uk = settings, uk_zone(settings)
        self.ppp = Decimal(settings.market.points_per_pip)
        self.record = record or (lambda kind, t, **data: None)
        self.day = None                 # the UK date the state below is for
        self.direction = None           # "buy" or "sell" once started
        self.started = None             # when
        self.cancelled = None           # when, if cancelled
        self.reference = ""             # the slow grind trade that started it
        self.info: dict = {}

    def _for(self, t: datetime) -> None:
        d = t.astimezone(self.uk).date()
        if d != self.day:
            self.day, self.direction, self.started, self.cancelled, self.reference, self.info = d, None, None, None, "", {}

    def _ends(self) -> datetime:
        f = self.s.entry_filters
        return datetime.combine(self.day, f.trend_day_ends_at, self.uk)

    def direction_at(self, t: datetime) -> str | None:
        """The trend day's direction at `t`, or None (not started, cancelled, after 20:30 UK, or another day)."""
        if self.day != t.astimezone(self.uk).date() or self.direction is None:
            return None
        if self.cancelled is not None and t >= self.cancelled:
            return None
        return self.direction if self.started <= t < self._ends() else None

    def on_bar(self, bar: Any, trades: list) -> None:
        """A price (a tick as a one-price bar) or a 5-minute candle, with the trades open at it: a slow grind trade
        in profit at it, inside 06:00-09:00 UK, starts (or, the other way, cancels) the day's trend day. A trade is
        judged only on prices from the bar it opened in onwards."""
        f = self.s.entry_filters
        self._for(bar.start)
        if self.cancelled is not None:
            return
        clock = bar.start.astimezone(self.uk).time()
        if not (f.trend_day_from <= clock < f.trend_day_until):
            return
        for t in trades:
            if t.strategy != SLOW_GRIND or not t.open or t.opened_at > bar.start:
                continue
            buy = t.direction == "buy"
            best = (bar.sell_high - t.fill) / self.ppp if buy else (t.fill - bar.buy_low) / self.ppp
            if best <= 0:
                continue
            data = {"direction": t.direction, "reference": t.reference, "strategy": t.strategy,
                    "slow_grind_opened_utc": t.opened_at, "slow_grind_fill": t.fill, "pips_in_profit": best,
                    "ends_utc": self._ends()}
            if self.direction is None:
                self.direction, self.started, self.reference = t.direction, bar.start, t.reference
                self.info = data
                self.record(TREND_DAY_STARTED, bar.start, **data,
                            why=f"the slow grind {t.direction} opened at {t.fill} was {best:.1f} pips in profit at "
                                f"{clock:%H:%M} UK (inside {f.trend_day_from:%H:%M}-{f.trend_day_until:%H:%M}): a "
                                f"{t.direction} trend day until {f.trend_day_ends_at:%H:%M} UK")
            elif t.direction != self.direction:
                self.cancelled = bar.start
                self.record(TREND_DAY_CANCELLED, bar.start, **data, started_utc=self.started,
                            started_by=self.reference,
                            why=f"a slow grind {t.direction} (opened at {t.fill}) was also in profit at {clock:%H:%M} "
                                f"UK, against the {self.direction} trend day: cancelled for the rest of the day")
                return

    def restore(self, rows: list[dict], now: datetime) -> None:
        """After a restart: today's recorded start and cancel (decisions.jsonl rows), so the day carries on."""
        self._for(now)
        for r in rows:
            t = datetime.fromisoformat(str(r["time_utc"]).replace("Z", "+00:00"))
            if t.astimezone(self.uk).date() != self.day or t > now:
                continue
            if r.get("kind") == TREND_DAY_STARTED and self.direction is None:
                self.direction, self.started, self.reference = r["direction"], t, r.get("reference", "")
                self.info = r
            elif r.get("kind") == TREND_DAY_CANCELLED:
                self.cancelled = t

    def status(self, now: datetime) -> dict | None:
        """For the dashboard: today's trend day, if one started."""
        if self.day != now.astimezone(self.uk).date() or self.direction is None:
            return None
        return {"direction": self.direction, "started_utc": self.started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reference": self.reference, "active": self.direction_at(now) is not None,
                "cancelled_utc": None if self.cancelled is None else self.cancelled.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ends_utc": self._ends().astimezone(self.uk).strftime("%H:%M UK")}
