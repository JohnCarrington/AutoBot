"""What every strategy shares: a candidate (a strategy's entry price was
reached), the idea it becomes, and the checks that must all allow it.

A strategy's setup becomes an IDEA only if, at the moment its entry price is
reached, all of these allow it (design sections 2.2 and 2.3; checked at entry
only, owner 7 November 2026):
  1. its switch in .env is on (STRATEGY_SLOW_GRIND, ...);
  2. the analyser's current state allows the strategy (section 2.2): ranging ->
     range trade; emerging trend and trend -> EMA pullback and breakout IN THE
     TREND'S DIRECTION ONLY; trend only -> slow grind, IN THE TREND'S DIRECTION
     ONLY (owner, 8 November 2026); consolidation -> none. The Bollinger
     bounce is not checked against the state: it opens in every state, either
     way (owner, 15 November 2026: "it opens without hindrance"); nor are the three session strategies, the Asian
     range breakout, the session sweep and the New York open reversal (owner, 16 November 2026: "like the bounce");
  3. the direction rule allows that direction (section 2.3): a buy needs buy
     side (price above the daily pivot and the 5-minute 100 EMA), a sell needs
     sell side. It does not apply to the session strategies (owner, 16 November 2026), the range trade, the Bollinger bounce, the
     breakout (owner, 7 November 2026), the slow grind or the level reversal
     (owner, 8 November 2026), in any state; the rule's answer is still recorded.
     The level reversal is allowed in every state except consolidation, either way.
  4. the hourly read (analyser/hourly_read.py; owner, 14 November 2026) allows it, only while the switch
     HOURLY_READ is on (off: this check is skipped). It applies only to the
     trend strategies (TREND_STRATEGIES: EMA pullback, slow grind, breakout):
       * hourly ranging: a 5-minute trend counts only once an hourly candle closes at least
         hourly_read.break_beyond_pips (3) beyond the hourly range, and such a close is what turns the read
         into a sell-off or a rally; so while the read is ranging the trend strategies open nothing;
       * hourly sell-off: the trend strategies only sell; hourly rally: they only buy;
     the level reversal and the Bollinger bounce (and the range trade) are not affected: they may trade
     against the hourly. Nothing else in the analyser's 5-minute read changes, and open trades are not affected.
  5. the Bollinger bounce's own two switches in .env (owner, 15 November 2026; both off if left out):
       * BOUNCE_ONLY_WHEN_HOURLY_RANGING: it opens only while the hourly read says ranging (whatever HOURLY_READ is);
       * BOUNCE_ONLY_NEAR_TIMES: it opens only within bounce.near_times_within_minutes (60) of one of
         bounce.near_times (10:00, 14:00, 16:00 UK), both ends included, judged at the moment it opens.
  7. the analyser governs every strategy (owner, 18 November 2026; design 2.10), only while the switch
     ANALYSER_GOVERNS_ALL is on (off if left out). Two groups: the TREND GROUP (slow grind, EMA pullback, breakout,
     Asian range breakout) and the REVERSAL GROUP (Bollinger bounce, level reversal, session sweep, New York open
     reversal, range trade). By the analyser's state (after the last finished 5-minute candle):
       * ranging: the trend group nothing; the reversal group either way;
       * emerging trend, trend: both groups only in the trend's direction;
       * possible reversal: the trend group nothing new; the reversal group either way, but against the OLD trend
         (in the possible reversal's direction) only while the 5-minute MACD histogram is at its biggest bar in the
         old trend's direction since the old trend started, or smaller than both that biggest bar and the bar
         before it, or has crossed zero (owner's answers, 18 November 2026);
       * consolidation: nothing.
     The Asian range breakout (owner, 18 November 2026): the trend group for direction only; ranging, consolidation
     and the hourly-ranging rule below do not block it (a possible reversal's "nothing new" still does).
     And while the hourly read (analyser/hourly_read.py, after the last finished hourly candle; whatever HOURLY_READ
     is) says ranging: the trend group nothing; the reversal group sells only at the top edge, buys only at the
     bottom edge, judged on the setup's furthest point (the candidate's context "furthest": from its piercing or
     rejection candle to its confirmation candle) within analyser_control.edge_within_pips of the hourly range high
     or above it (a sell), of its low or below it (a buy), and its rejection candle closing back inside the hourly
     range (the context "rejection_close"; owner, 18 November 2026). Each strategy's own state rule in 2 still applies
     inside this, except that the level reversal's "every state except consolidation, either way" and the bounce's
     and session strategies' "without hindrance" are replaced by it while the switch is on.
  6. the trend is still going (owner, 16 November 2026), only while the switch TREND_STILL_GOING is on (off if
     left out): the trend strategies (TREND_STRATEGIES: EMA pullback, slow grind, breakout) only open a sell if,
     within the last trend_still_going.within_candles (12) finished 5-minute candles, price made a new low at
     least trend_still_going.new_extreme_pips (5) below the previous low, and a buy only if it made a new high at
     least that far above the previous high. The previous low is the last swing low before that candle: a candle
     whose low is lower than the lows of the trend_still_going.swing_candles_each_side (1) candles before it and
     after it, all of them before that candle (a swing high, the mirror). Sell price, as on the chart.
"The current state" is the analyser's state after the last finished 5-minute
candle, the hourly read is the one after the last finished hourly candle, and
the direction rule uses the entry price. A candidate that fails a
check is kept as BLOCKED with the reason, never as an idea.

Ideas only: nothing here places, changes or closes a trade, or contacts IG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.direction import BUY_SIDE, SELL_SIDE, decide
from analyser.hourly_read import RALLY as HOURLY_RALLY, RANGING as HOURLY_RANGING, SELL_OFF as HOURLY_SELL_OFF
from analyser.states import CONSOLIDATION, DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP
from prices.model import plain

SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL = (
    "slow grind", "EMA pullback", "Bollinger bounce", "range trade", "breakout", "level reversal")
# The session strategies (design 3.7 to 3.9; owner, 16 November 2026).
ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL = (
    "Asian range breakout", "session sweep", "New York open reversal")
SESSION_STRATEGIES = (ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL)
SWITCH = {SLOW_GRIND: "slow_grind", EMA_PULLBACK: "ema_pullback", BOLLINGER_BOUNCE: "bollinger_bounce",
          RANGE_TRADE: "range_trade", BREAKOUT: "breakout", LEVEL_REVERSAL: "level_reversal",
          ASIAN_RANGE_BREAKOUT: "asian_range_breakout", SESSION_SWEEP: "session_sweep",
          NEW_YORK_OPEN_REVERSAL: "new_york_open_reversal"}
# Open without hindrance (owner, 15 and 16 November 2026): not checked against the analyser's state, the direction
# rule or the hourly read; in the safety rules one at a time in each direction, not held back by the most at once
# nor by one view at a time.
WITHOUT_HINDRANCE = (BOLLINGER_BOUNCE,) + SESSION_STRATEGIES
# Open at the open of the candle after their confirmation candle: live, on that candle's first price; never sent
# late (trading/engine.py).
OPEN_AT_NEXT_CANDLE = (BOLLINGER_BOUNCE,) + SESSION_STRATEGIES
# Held overnight and closed at 20:30 UK on Friday only (owner, 7 November 2026); every other
# strategy is closed at 20:30 UK every day.
OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
# May open in a big-news window and not closed before big news (owner, 7 and 8 November 2026).
NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
# Not closed on a rejection at a level (owner, 7 and 8 November 2026).
NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL, BOLLINGER_BOUNCE) + SESSION_STRATEGIES
# The direction rule (section 2.3) does not apply to these (owner, 7 and 8 November 2026).
NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL) + SESSION_STRATEGIES
BUY, SELL = "buy", "sell"
# The strategies the hourly read applies to (check 4 above; owner, 14 November 2026).
TREND_STRATEGIES = (EMA_PULLBACK, SLOW_GRIND, BREAKOUT)
# The two groups of check 7, while ANALYSER_GOVERNS_ALL is on (owner, 18 November 2026; design 2.10).
TREND_GROUP = (SLOW_GRIND, EMA_PULLBACK, BREAKOUT, ASIAN_RANGE_BREAKOUT)
REVERSAL_GROUP = (BOLLINGER_BOUNCE, LEVEL_REVERSAL, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL, RANGE_TRADE)
# The strategies whose own state rule check 7 replaces while ANALYSER_GOVERNS_ALL is on: the level reversal's
# "every state except consolidation, either way" and "without hindrance" (the bounce and the session strategies).
STATE_RULE_REPLACED = (LEVEL_REVERSAL,) + WITHOUT_HINDRANCE
# Section 2.2: which states allow which strategy: "any" direction, only in the trend's direction
# ("trend"), or only against it ("against").
ALLOWED_IN = {
    SLOW_GRIND: {TREND: "trend"},                      # trend only (owner, 8 November 2026)
    EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
    # the Bollinger bounce: every state, either way (owner, 15 November 2026); not checked
    BOLLINGER_BOUNCE: {RANGING: "any", EMERGING: "any", TREND: "any", POSSIBLE_REVERSAL: "any", CONSOLIDATION: "any"},
    RANGE_TRADE: {RANGING: "any"},
    BREAKOUT: {EMERGING: "trend", TREND: "trend"},
    # every state except consolidation, either way (owner, 8 November 2026)
    LEVEL_REVERSAL: {RANGING: "any", EMERGING: "any", TREND: "any", POSSIBLE_REVERSAL: "any"},
}
# the session strategies: every state, either way, not checked (owner, 16 November 2026: "like the bounce")
for _name in SESSION_STRATEGIES:
    ALLOWED_IN[_name] = dict(ALLOWED_IN[BOLLINGER_BOUNCE])


@dataclass
class Candidate:
    """A strategy's entry price was reached (before the checks)."""
    strategy: str
    direction: str                      # buy or sell
    time: datetime                      # the moment the entry price was reached (replay: the candle's start)
    entry_price: Decimal
    steps: list[str]                    # the reason, step by step
    context: dict = field(default_factory=dict)   # what the trade manager may need (e.g. the breakout's range)


@dataclass
class Idea:
    pair: str
    strategy: str
    direction: str
    time: datetime
    entry_price: Decimal
    state: str                          # the analyser's state at that moment
    state_direction: str
    trend_type: str | None
    direction_rule: str                 # buy side, sell side or no clear direction
    steps: list[str]
    allowed: bool = True
    blocked_by: str = ""
    context: dict = field(default_factory=dict)   # from the candidate (e.g. the breakout's consolidation range)

    def as_dict(self) -> dict:
        return {"pair": self.pair, "strategy": self.strategy, "direction": self.direction,
                "time_utc": self.time.strftime("%Y-%m-%dT%H:%M:%SZ"), "entry_price": str(self.entry_price),
                "state": self.state, "state_direction": self.state_direction, "trend_type": self.trend_type,
                "direction_rule": self.direction_rule, "steps": list(self.steps), "allowed": self.allowed,
                "blocked_by": self.blocked_by}

    def line(self) -> str:
        from prices.model import plain, uk_short
        kind = f", {self.trend_type}" if self.trend_type else ""
        head = (f"{uk_short(self.time)}  {self.strategy} {self.direction.upper()} at {plain(self.entry_price)}  "
                f"[{self.state} {self.state_direction}{kind}; {self.direction_rule}]")
        return head + ("" if self.allowed else f"  BLOCKED: {self.blocked_by}")


# ---- hours, news and the forced close per strategy (design sections 4 and 6), for the safety
# part and the trade manager. The EMA pullback has its own rules (owner, 7 November 2026).

def may_open(settings: Any, pair: str, strategy: str, t: datetime, calendar: list | None = None) -> list[str]:
    """Every reason a new trade of this strategy may not open at t (empty: hours and news allow it).
    EMA pullback: any time the market is open, big-news windows included, except after
    hours.close_all_trades_at (20:30) UK on Friday, so none is held over the weekend (owner,
    7 November 2026), and from ema_pullback.rollover_no_new_trades_from (21:55) to
    ema_pullback.rollover_no_new_trades_until (22:15) UK, the rollover (owner, 13 November 2026).
    Slow grind (owner, 8 November 2026): any time the market is open, big-news windows included,
    except from hours.close_all_trades_at (20:30) to midnight UK every day, in the first
    slow_grind.week_open_no_new_trades_minutes (15) after the week opens, and from
    slow_grind.rollover_no_new_trades_from (21:55) to slow_grind.rollover_no_new_trades_until (22:15) UK.
    Breakout: UK time from NEW_TRADES_FROM to NEW_TRADES_UNTIL; big-news windows allowed.
    Every other strategy: UK time from NEW_TRADES_FROM to NEW_TRADES_UNTIL, and not in a big-news
    no-new-trades window. The New York open reversal also not on a day with big news for the pair released at
    new_york_open_reversal.no_trade_if_big_news_at (13:30) UK (owner, 16 November 2026)."""
    from zoneinfo import ZoneInfo
    from news.calendar import no_new_trades
    from prices.calendar import MarketHours
    reasons = []
    hours = MarketHours(settings.market_hours)
    if not hours.is_open(t):
        reasons.append("the market is closed")
    tz = settings.hours.timezone
    if strategy == SLOW_GRIND:
        from datetime import timedelta
        sg = settings.slow_grind
        lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
        if lt >= settings.hours.close_all_trades_at:
            reasons.append(f"from {settings.hours.close_all_trades_at:%H:%M} UK to midnight: no new {strategy} trade")
        if sg.rollover_no_new_trades_from <= lt < sg.rollover_no_new_trades_until:
            reasons.append(f"from {sg.rollover_no_new_trades_from:%H:%M} to {sg.rollover_no_new_trades_until:%H:%M} UK "
                           f"(the rollover): no new {strategy} trade")
        if hours.is_open(t):
            opened = hours.session(t)[0]
            if t < opened + timedelta(minutes=sg.week_open_no_new_trades_minutes):
                reasons.append(f"in the first {sg.week_open_no_new_trades_minutes} minutes after the week opened: "
                               f"no new {strategy} trade")
        return reasons
    if strategy == EMA_PULLBACK:
        lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)
        if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
            reasons.append(f"after {settings.hours.close_all_trades_at:%H:%M} UK on Friday: "
                           f"no {strategy} trade is held over the weekend")
        ep = settings.ema_pullback
        if ep.rollover_no_new_trades_from <= lt.time() < ep.rollover_no_new_trades_until:
            reasons.append(f"from {ep.rollover_no_new_trades_from:%H:%M} to {ep.rollover_no_new_trades_until:%H:%M} UK "
                           f"(the rollover): no new {strategy} trade")
        return reasons
    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
    sw = settings.switches
    if not (sw.new_trades_from <= lt < sw.new_trades_until):
        reasons.append(f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK")
    if strategy == BREAKOUT:
        return reasons
    windows = no_new_trades(settings, pair, t, calendar)
    if windows:
        reasons.append("in a big-news window: " + ", ".join(sorted({w.event for w in windows})))
    if strategy == NEW_YORK_OPEN_REVERSAL:
        at = settings.new_york_open_reversal.no_trade_if_big_news_at
        if big_news_at(settings, pair, t, at, calendar):
            reasons.append(f"big news is released at {at:%H:%M} UK today: no {strategy} (owner, 16 November 2026)")
    return reasons


def forced_close_at(settings: Any, strategy: str, opened: datetime) -> datetime:
    """When a trade opened at `opened` is closed by the clock: hours.close_all_trades_at (20:30) UK,
    the first one after it opened; for the EMA pullback and the breakout, the first FRIDAY 20:30 UK
    after it opened. (A slow grind trade never opens between 20:30 and midnight UK, so it is
    always closed at 20:30 the day it opened.)"""
    from datetime import datetime as dt, timedelta, timezone
    from zoneinfo import ZoneInfo
    tz = settings.hours.timezone
    uk = ZoneInfo(tz) if isinstance(tz, str) else tz
    lt = opened.astimezone(uk)
    for k in range(0, 8):
        day = lt.date() + timedelta(days=k)
        cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
            return cut.astimezone(timezone.utc)
    raise AssertionError("no close found within a week")


def trail(settings: Any, strategy: str) -> tuple[Decimal, int] | None:
    """The trail behind the last candles as (from pips, candles): once a trade has been `from` pips in profit, after
    each finished 5-minute candle its stop is moved at IG beyond the last `candles` finished candles. The Bollinger
    bounce (bounce.trail_from_pips 12, bounce.trail_candles 3; owner, 15 November 2026) and the session strategies,
    each with its own trail_from_pips and trail_candles (12 and 3; owner, 16 November 2026); None for every other
    strategy."""
    section = {BOLLINGER_BOUNCE: "bounce", ASIAN_RANGE_BREAKOUT: "asian_range_breakout",
               SESSION_SWEEP: "session_sweep", NEW_YORK_OPEN_REVERSAL: "new_york_open_reversal"}.get(strategy)
    if section is None:
        return None
    sec = getattr(settings, section)
    return Decimal(str(sec.trail_from_pips)), int(sec.trail_candles)


def most_trail_candles(settings: Any) -> int:
    """The most finished candles any strategy's trail looks back over (the trade manager keeps at least these)."""
    return max(trail(settings, n)[1] for n in WITHOUT_HINDRANCE)


def big_news_at(settings: Any, pair: str, t: datetime, at: Any, calendar: list | None = None) -> bool:
    """Whether a BIG release for the pair (the news table) comes out at UK clock time `at` on t's UK day."""
    from datetime import datetime as dt, time as tm, timedelta, timezone
    from zoneinfo import ZoneInfo
    from news.calendar import big_news_windows
    tz = settings.hours.timezone
    uk = ZoneInfo(tz) if isinstance(tz, str) else tz
    day = t.astimezone(uk).date()
    start = dt.combine(day, tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
    end = dt.combine(day + timedelta(days=1), tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
    return any(w.release_utc.astimezone(uk).time().replace(second=0, microsecond=0) == at
               for w in big_news_windows(settings, pair, start, end, calendar))


def closed_before_big_news(strategy: str) -> bool:
    """Open trades are closed 15 minutes before big news, except the EMA pullback's, the breakout's
    and the slow grind's."""
    return strategy not in NEWS_ALLOWED


def closed_on_level_rejection(strategy: str) -> bool:
    """Section 4's close on a confirmed rejection at a level: the range trade only (not the EMA pullback, the
    breakout, the slow grind, the level reversal, nor the Bollinger bounce: owner, 15 November 2026)."""
    return strategy not in NO_LEVEL_CLOSE


def profit_lock(settings: Any, strategy: str) -> tuple[int, int] | None:
    """Section 4's profit lock as (from, at) in pips: once a trade has been `from` pips in profit it is
    closed if price comes back to `at` pips in profit. Only the slow grind has one (15, 10; owner,
    8 November 2026); None for every other strategy."""
    if strategy != SLOW_GRIND:
        return None
    return settings.slow_grind.lock_from_pips, settings.slow_grind.lock_at_pips


def big_news_day(settings: Any, pair: str, t: datetime, calendar: list | None = None) -> bool:
    """Whether the UK calendar day of t has a BIG release for the pair (the news table)."""
    from datetime import datetime as dt, time as tm, timedelta, timezone
    from zoneinfo import ZoneInfo
    from news.calendar import big_news_windows
    tz = settings.hours.timezone
    uk = ZoneInfo(tz) if isinstance(tz, str) else tz
    day = t.astimezone(uk).date()
    start = dt.combine(day, tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
    end = dt.combine(day + timedelta(days=1), tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
    return any(start <= w.release_utc < end for w in big_news_windows(settings, pair, start, end, calendar))


def take_profit_pips(settings: Any, strategy: str, opened: datetime | None = None, pair: str | None = None,
                     calendar: list | None = None, direction: str | None = None, trend_day: str | None = None) -> int:
    """Design section 4: every strategy uses TAKE_PROFIT_PIPS (100), except
    - the EMA pullback: its own ema_pullback.take_profit_pips (30) (owner, 7 November 2026);
    - the slow grind: its own slow_grind.take_profit_pips (20) (owner, 8 November 2026);
      each of these two gets TAKE_PROFIT_PIPS instead for a trade opened on a UK day with big news
      for the pair. Give `opened` and `pair`; without them the normal take profit is returned;
    - the breakout: breakout.take_profit_pips (50) on any day;
    - the level reversal: level_reversal.take_profit_pips (20) on any day (owner, 8 November 2026).
    On a trend day (analyser/trend_day.py, design 2.4; owner, 8 November 2026), an EMA pullback or slow
    grind trade in the trend day's direction gets TAKE_PROFIT_PIPS too: give `direction` (buy or sell)
    and `trend_day` (the day's check: "down", "up" or None)."""
    if strategy == BREAKOUT:
        return settings.breakout.take_profit_pips
    if strategy == LEVEL_REVERSAL:
        return settings.level_reversal.take_profit_pips
    if strategy not in (EMA_PULLBACK, SLOW_GRIND):
        return settings.switches.take_profit_pips
    if trend_day is not None and direction == {"down": SELL, "up": BUY}.get(trend_day):
        return settings.switches.take_profit_pips
    if opened is not None and pair is not None and big_news_day(settings, pair, opened, calendar):
        return settings.switches.take_profit_pips
    return settings.ema_pullback.take_profit_pips if strategy == EMA_PULLBACK else settings.slow_grind.take_profit_pips


def counts_towards_most_at_once(strategy: str) -> bool:
    """Section 6: "most at once: 5" counts every open trade except the EMA pullback's."""
    return strategy != EMA_PULLBACK


def stop_loss_pips(settings: Any, strategy: str) -> int:
    """Design section 4: the EMA pullback's own stop (STOP_LOSS_PIPS_EMA_PULLBACK), the breakout's
    (breakout.stop_loss_pips) and the slow grind's (slow_grind.stop_loss_pips, 15); every other
    strategy uses STOP_LOSS_PIPS. The level reversal's stop is not a distance from the entry but
    level_reversal.stop_beyond_furthest_pips (6) beyond the furthest point price reached: see
    stop_price(); this returns that 6. The session strategies (owner, 16 November 2026): the Asian range
    breakout's asian_range_breakout.stop_loss_pips (12), the New York open reversal's
    new_york_open_reversal.stop_loss_pips (12); the session sweep's stop is a price (stop_price()), at least
    session_sweep.min_stop_pips (12) from the entry, which this returns."""
    sw = settings.switches
    if strategy == LEVEL_REVERSAL:
        return settings.level_reversal.stop_beyond_furthest_pips
    if strategy == ASIAN_RANGE_BREAKOUT:
        return settings.asian_range_breakout.stop_loss_pips
    if strategy == NEW_YORK_OPEN_REVERSAL:
        return settings.new_york_open_reversal.stop_loss_pips
    if strategy == SESSION_SWEEP:
        return settings.session_sweep.min_stop_pips
    if strategy == BREAKOUT:
        return settings.breakout.stop_loss_pips
    if strategy == SLOW_GRIND:
        return settings.slow_grind.stop_loss_pips
    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips


LEVEL_STOP_STRATEGIES = (RANGE_TRADE, LEVEL_REVERSAL, EMA_PULLBACK)


def level_stops_on(settings: Any, strategy: str) -> bool:
    """LEVEL_STOPS (owner, 18 November 2026) applies to this strategy: the switch is on and it is the range trade, the
    level reversal or the EMA pullback."""
    return strategy in LEVEL_STOP_STRATEGIES and bool(getattr(getattr(settings, "switches", None), "level_stops", False))


def level_stop_context(settings: Any, strategy: str, direction: str, entry: Decimal, levels: Any) -> dict:
    """LEVEL_STOPS: the nearest level group beyond the entry on the stop side (the bot's level list and its grouping,
    levels.current.LevelList): a sell, the lowest group whose highest level is above the entry; a buy, the highest group
    whose lowest level is below it. It counts only if its far edge (a sell: its highest level; a buy: its lowest) is
    within level_stops.widest_stop_pips (20) of the entry (the owner's answer, 18 November 2026). Returns the idea's
    context entries: {"level_stop_edge", "level_stop_group"} or {"level_stop_none": why} (the strategy's own stop is
    then used); {} while the switch is off or for another strategy."""
    if not level_stops_on(settings, strategy) or levels is None:
        return {}
    ppp = Decimal(settings.market.points_per_pip)
    most = Decimal(settings.level_stops.widest_stop_pips) * ppp
    entry = Decimal(entry)
    sell = direction == SELL
    groups = [g for g in levels.groups if (g["high"] > entry if sell else g["low"] < entry)]
    if not groups:
        return {"level_stop_none": "no level group beyond the entry on the stop side"}
    g = min(groups, key=lambda g: g["high"]) if sell else max(groups, key=lambda g: g["low"])
    edge = g["high"] if sell else g["low"]
    if abs(edge - entry) > most:
        return {"level_stop_none": f"no level group within {plain(settings.level_stops.widest_stop_pips)} pips on the "
                                   f"stop side (the nearest's far edge {plain(edge)} is "
                                   f"{plain((abs(edge - entry) / ppp).quantize(Decimal('0.1')))} pips away)"}
    names = ", ".join(f"{m.type} {plain(m.price)}" for m in g["members"])
    return {"level_stop_edge": edge, "level_stop_group": f"{plain(g['low'])} to {plain(g['high'])} ({names})"}


def level_stop_price(settings: Any, idea: Any) -> Decimal | None:
    """LEVEL_STOPS: the stop on the chart (sell) price, level_stops.beyond_group_pips (5) beyond the group's far edge
    (the order sender adds the spread for a sell when it sends it). None: not used (switch off, another strategy, or no
    group within the widest stop: the strategy's own stop)."""
    ctx = getattr(idea, "context", None) or {}
    if not level_stops_on(settings, idea.strategy) or ctx.get("level_stop_edge") is None:
        return None
    beyond = Decimal(settings.level_stops.beyond_group_pips) * Decimal(settings.market.points_per_pip)
    edge = Decimal(ctx["level_stop_edge"])
    return edge + beyond if idea.direction == SELL else edge - beyond


def stop_price(settings: Any, idea: Any) -> Decimal | None:
    """Design section 4: the stop as a price (chart price) when a strategy sets it from its setup:
    the level reversal's, level_reversal.stop_beyond_furthest_pips beyond the furthest point price
    reached past (or short of) the level (the idea's context); the session sweep's,
    session_sweep.stop_beyond_furthest_pips (1) beyond the sweep's furthest point and at least
    session_sweep.min_stop_pips (12) from the entry (worked out by the strategy, in the idea's context).
    None for every other strategy, whose stop is stop_loss_pips() from the entry."""
    level = level_stop_price(settings, idea)          # LEVEL_STOPS (owner, 18 November 2026): replaces the own stop
    if level is not None:
        return level
    if idea.strategy not in (LEVEL_REVERSAL, SESSION_SWEEP):
        return None
    return idea.context["stop_price"]


def hourly_reasons(settings: Any, strategy: str, direction: str, hourly: Any) -> list[str]:
    """Check 4: why the hourly read does not allow this trend strategy this way (empty: allowed)."""
    if hourly is None or strategy not in TREND_STRATEGIES or not settings.switches.hourly_read:
        return []
    rng = f" ({plain(hourly.low)} to {plain(hourly.high)})" if hourly.low is not None else ""
    if hourly.state == HOURLY_RANGING:
        wait = ("a 5-minute close (ANALYSER_USES_HOURLY)" if getattr(settings.switches, "analyser_uses_hourly", False)
                else "an hourly close")
        return [f"the hourly chart is ranging{rng}: {strategy} waits for {wait} at least "
                f"{settings.hourly_read.break_beyond_pips} pips beyond the hourly range"]
    if hourly.state == HOURLY_SELL_OFF and direction == BUY:
        return [f"the hourly chart is in a sell-off: {strategy} only sells"]
    if hourly.state == HOURLY_RALLY and direction == SELL:
        return [f"the hourly chart is in a rally: {strategy} only buys"]
    return []


def bounce_reasons(settings: Any, strategy: str, t: datetime | None, hourly: Any) -> list[str]:
    """Check 5: why the Bollinger bounce's own switches do not allow it at t (empty: allowed)."""
    if strategy != BOLLINGER_BOUNCE:
        return []
    sw, reasons = settings.switches, []
    if getattr(sw, "bounce_only_when_hourly_ranging", False):
        if hourly is None:
            reasons.append("BOUNCE_ONLY_WHEN_HOURLY_RANGING is on and the hourly read is not known")
        elif hourly.state != HOURLY_RANGING:
            reasons.append(f"BOUNCE_ONLY_WHEN_HOURLY_RANGING is on and the hourly chart is in a {hourly.state}")
    if getattr(sw, "bounce_only_near_times", False):
        b = settings.bounce
        if t is None or not near_times(settings, t):
            names = ", ".join(f"{x:%H:%M}" for x in b.near_times)
            reasons.append(f"BOUNCE_ONLY_NEAR_TIMES is on and it is not within {b.near_times_within_minutes} minutes "
                           f"of {names} UK")
    return reasons


def near_times(settings: Any, t: datetime) -> bool:
    """t is within bounce.near_times_within_minutes of one of bounce.near_times (UK clock time), both ends included."""
    from datetime import datetime as dt, timedelta
    from zoneinfo import ZoneInfo
    tz = settings.hours.timezone
    uk = ZoneInfo(tz) if isinstance(tz, str) else tz
    lt = t.astimezone(uk)
    within = timedelta(minutes=int(settings.bounce.near_times_within_minutes))
    return any(abs(lt - dt.combine(lt.date(), x, tzinfo=uk)) <= within for x in settings.bounce.near_times)


def still_going_reasons(settings: Any, strategy: str, direction: str, candles: list | None) -> list[str]:
    """Check 6: why the trend is not still going for this trend strategy this way (empty: allowed). `candles`: the
    finished 5-minute candles before the entry, oldest first (the strategy runner gives them; None: not checked)."""
    if strategy not in TREND_STRATEGIES or not getattr(settings.switches, "trend_still_going", False) \
            or candles is None:
        return []
    t, side = settings.trend_still_going, settings.chart.price
    sell = direction == SELL
    n, w = int(t.within_candles), int(t.swing_candles_each_side)
    need = Decimal(t.new_extreme_pips) * Decimal(settings.market.points_per_pip)
    # a sell looks at lows, a buy at highs turned upside down, so "lower" is "further in the trade's direction"
    x = [getattr(c, f"{side}_low") if sell else -getattr(c, f"{side}_high") for c in candles]
    best = None                                         # (how far beyond, swing price, swing candle, new candle)
    for j in range(max(0, len(x) - n), len(x)):
        for k in range(j - 1 - w, w - 1, -1):           # the last swing before j, with its w candles after it before j
            if all(x[k] < x[k - i] for i in range(1, w + 1)) and all(x[k] < x[k + i] for i in range(1, w + 1)):
                beyond = x[k] - x[j]
                if best is None or beyond > best[0]:
                    best = (beyond, x[k], candles[k], candles[j])
                break
    if best is not None and best[0] >= need:
        return []
    word, extreme = ("low", "below") if sell else ("high", "above")
    pips = lambda v: plain((v / Decimal(settings.market.points_per_pip)).quantize(Decimal("0.1")))
    found = "" if best is None else (
        f" (the most: {pips(best[0])} pips {extreme} the swing {word} {plain(abs(best[1]))} of "
        f"{best[2].start:%H:%M}, at {best[3].start:%H:%M})")
    return [f"TREND_STILL_GOING is on and the trend is not still going: no new {word} at least "
            f"{plain(t.new_extreme_pips)} pips {extreme} the previous {word} in the last {n} five-minute candles{found}"]


def near_level_reasons(settings: Any, strategy: str, price: Decimal, context: dict | None) -> list[str]:
    """LR_ENTRY_NEAR_LEVEL (owner, 18 November 2026; design 3.6, rule 9): a level reversal opens only if its entry price
    is within level_reversal.entry_within_pips_of_level (6) of the level it traded (the level its rules 2, 7 and 8
    picked: the candidate's context "level"). Empty: allowed (or the switch off, or not a level reversal)."""
    if strategy != LEVEL_REVERSAL or not getattr(getattr(settings, "switches", None), "lr_entry_near_level", False) \
            or not context or context.get("level") is None:
        return []
    ppp = Decimal(settings.market.points_per_pip)
    away = (abs(Decimal(price) - Decimal(context["level"])) / ppp).quantize(Decimal("0.1"))
    most = Decimal(settings.level_reversal.entry_within_pips_of_level)
    if away <= most:
        return []
    name = context.get("level_name") or plain(context["level"])
    return [f"LR_ENTRY_NEAR_LEVEL: the entry {plain(price)} is {plain(away)} pips from the level it traded ({name}), "
            f"more than {plain(most)}"]


def governed_allowed(state: str) -> list[str]:
    """The strategies check 7 lets open in this analyser state, either way or one way (for the dashboard, while
    ANALYSER_GOVERNS_ALL is on; owner, 18 November 2026): each strategy's own state rule (2) and the table of
    design 2.10. The hourly read and the direction are checked at entry."""
    out = []
    for name in TREND_GROUP + REVERSAL_GROUP:
        arb = name == ASIAN_RANGE_BREAKOUT              # not held back by ranging or consolidation
        if (state == CONSOLIDATION and not arb) or (state == RANGING and name in TREND_GROUP and not arb):
            continue
        if state == POSSIBLE_REVERSAL and name in TREND_GROUP:
            continue
        if name not in STATE_RULE_REPLACED and state not in ALLOWED_IN[name]:
            continue                                     # its own state rule (e.g. the slow grind: trend only)
        out.append(name)
    return out


def signal_context(direction: str, rejection_start: datetime, furthest: Decimal | None,
                   rejection_close: Decimal | None = None) -> dict:
    """What a reversal-group candidate carries for the analyser control (owner, 18 November 2026; design 2.10):
    "furthest", the setup's furthest point (check 7's edge of the hourly range), and "signal", its direction and
    the start of its rejection (or reversal) candle (safety rule 11, one signal one trade)."""
    return {"furthest": furthest, "rejection_close": rejection_close,
            "rejection_candle": rejection_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "signal": f"{direction} {rejection_start.strftime('%Y-%m-%dT%H:%M:%SZ')}"}


def governs_reasons(settings: Any, strategy: str, direction: str, state: Any, hourly: Any,
                    context: dict | None) -> list[str]:
    """Check 7: why the analyser does not allow this strategy this way (empty: allowed), only while
    ANALYSER_GOVERNS_ALL is on. `state`: the analyser's state (for a possible reversal with `macd_ok` and
    `macd_why`, worked out by the strategy runner); `hourly`: the hourly read; `context`: the candidate's context
    ("furthest" for the reversal group)."""
    from analyser.states import rejection_at_edge, switch_on
    if not switch_on(settings, "analyser_governs_all"):
        return []
    trend = strategy in TREND_GROUP
    # the Asian range breakout: the trend group for direction only; ranging, consolidation and the hourly-ranging
    # rule do not block it, breaking out of the quiet Asian range being its job (owner, 18 November 2026)
    arb = strategy == ASIAN_RANGE_BREAKOUT
    group = "the trend group" if trend else "the reversal group"
    st, d = state.state, state.direction
    want = SELL if d == DOWN else BUY if d == UP else None
    out = []
    if st == CONSOLIDATION:
        if not arb:
            out.append(f"ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: {group} opens nothing")
    elif st == RANGING:
        if trend and not arb:
            out.append(f"ANALYSER_GOVERNS_ALL: the analyser's state is ranging: {group} opens nothing")
    elif st in (EMERGING, TREND):
        if direction != want:
            out.append(f"ANALYSER_GOVERNS_ALL: the {st} is {d}: {strategy} only in the trend's direction")
    elif st == POSSIBLE_REVERSAL:
        if trend:
            out.append(f"ANALYSER_GOVERNS_ALL: the analyser's state is possible reversal: {group} opens nothing new")
        elif direction == want and not getattr(state, "macd_ok", False):
            out.append(f"ANALYSER_GOVERNS_ALL: in a possible reversal {strategy} goes against the old trend only "
                       f"while the 5-minute MACD histogram is at its biggest bar in the old trend's direction, or "
                       f"past it and shrinking ({getattr(state, 'macd_why', 'the MACD is not known')})")
    if hourly is not None and hourly.state == HOURLY_RANGING and not arb:
        rng = f" ({plain(hourly.low)} to {plain(hourly.high)})" if hourly.low is not None else ""
        if trend:
            out.append(f"ANALYSER_GOVERNS_ALL: the hourly chart is ranging{rng}: {group} opens nothing")
        elif hourly.high is not None:
            far = (context or {}).get("furthest")
            close = (context or {}).get("rejection_close")
            edge = "top" if direction == SELL else "bottom"
            if far is None or close is None:
                out.append(f"ANALYSER_GOVERNS_ALL: the hourly chart is ranging{rng} and the setup's furthest point "
                           f"is not known: {strategy} opens only at the {edge} edge")
            elif not rejection_at_edge(settings, hourly, Decimal(far), Decimal(close), direction):
                out.append(f"ANALYSER_GOVERNS_ALL: the hourly chart is ranging{rng}: a {direction} opens only at the "
                           f"{edge} edge (furthest point within "
                           f"{plain(settings.analyser_control.edge_within_pips)} pips of the hourly "
                           f"{'high' if direction == SELL else 'low'} or beyond it, and the rejection candle closing "
                           f"back inside the hourly range); the setup's furthest point {plain(Decimal(far))}, its "
                           f"rejection candle's close {plain(Decimal(close))}")
    return out


def allowed(settings: Any, strategy: str, direction: str, price: Decimal, state: Any, pivot: Decimal | None,
            ema100: Decimal | None, hourly: Any = None, t: datetime | None = None,
            candles: list | None = None, context: dict | None = None,
            trend_hourly: Any = None) -> tuple[list[str], Any]:
    """Every reason the switch, the state (2.2), the direction rule (2.3) or the hourly read (check 4) does not
    allow this strategy in this direction at this price (empty: allowed), and the direction rule. `hourly`: the
    hourly read (analyser.hourly_read.HourlyRead); the strategy runner always gives it. `trend_hourly`: the hourly
    read as the analyser and the trend group see it while ANALYSER_USES_HOURLY is on (a standing 5-minute break of
    the hourly range counts as a rally or a sell-off; analyser.hourly_read.with_break; owner, 18 November 2026),
    used by check 4 and check 7's hourly-ranging rule; None: `hourly`."""
    seen = trend_hourly if trend_hourly is not None else hourly
    rule = decide(price, "the price", pivot, ema100, "5m 100 EMA", ema100 is not None)
    reasons = []
    if not getattr(settings.switches, SWITCH[strategy]):
        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
    ok_in = ALLOWED_IN[strategy]
    from analyser.states import switch_on
    if strategy in WITHOUT_HINDRANCE:
        pass                                            # not checked against the state (owner, 15 and 16 November 2026)
    elif strategy in STATE_RULE_REPLACED and switch_on(settings, "analyser_governs_all"):
        pass                                            # check 7 replaces it (owner, 18 November 2026)
    elif state.state not in ok_in:
        reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
    elif ok_in[state.state] in ("trend", "against"):
        want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
        if ok_in[state.state] == "against":
            want = {SELL: BUY, BUY: SELL}.get(want)
        if direction != want:
            how = "in" if ok_in[state.state] == "trend" else "against"
            reasons.append(f"the {state.state} is {state.direction}: {strategy} only {how} the trend's direction")
    need = BUY_SIDE if direction == BUY else SELL_SIDE
    if rule.side != need and strategy not in NO_DIRECTION_RULE:
        reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
    reasons += hourly_reasons(settings, strategy, direction, seen)
    reasons += bounce_reasons(settings, strategy, t, hourly)
    reasons += still_going_reasons(settings, strategy, direction, candles)
    reasons += governs_reasons(settings, strategy, direction, state, seen, context)
    reasons += near_level_reasons(settings, strategy, price, context)
    return reasons, rule


def check(settings: Any, pair: str, c: Candidate, state: Any, pivot: Decimal | None,
          ema100: Decimal | None, hourly: Any = None, candles: list | None = None,
          trend_hourly: Any = None) -> Idea:
    """Turn a candidate into an idea, or a blocked one with every reason. `hourly`: the hourly read; `candles`:
    the finished 5-minute candles before the entry (check 6); `trend_hourly`: see allowed()."""
    reasons, rule = allowed(settings, c.strategy, c.direction, c.entry_price, state, pivot, ema100, hourly, c.time,
                            candles, c.context, trend_hourly)
    idea = Idea(pair, c.strategy, c.direction, c.time, c.entry_price, state.state, state.direction,
                state.trend_type, rule.side, list(c.steps), context=dict(c.context))
    if reasons:
        idea.allowed, idea.blocked_by = False, "; ".join(reasons)
    else:
        exempt = c.strategy in NO_DIRECTION_RULE
        idea.steps.append(f"allowed at entry: {c.strategy} in a {state.state} {state.direction}; direction rule "
                          f"{rule.side} ({rule.reason.replace('the price', 'the entry price')})"
                          + (f"; the direction rule does not apply to {c.strategy}" if exempt else "")
                          + (f"; {hourly.line()}" if hourly is not None and (settings.switches.hourly_read or (
                              c.strategy == BOLLINGER_BOUNCE
                              and getattr(settings.switches, "bounce_only_when_hourly_ranging", False))) else "")
                          + (f"; as the analyser and the trend group see it: {trend_hourly.line()}"
                             if trend_hourly is not None and trend_hourly is not hourly else ""))
    return idea
