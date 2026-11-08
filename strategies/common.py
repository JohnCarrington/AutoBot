"""What every strategy shares: a candidate (a strategy's entry price was
reached), the idea it becomes, and the checks that must all allow it.

A strategy's setup becomes an IDEA only if, at the moment its entry price is
reached, all of these allow it (design sections 2.2 and 2.3; checked at entry
only, owner 7 November 2026):
  1. its switch in .env is on (STRATEGY_SLOW_GRIND, ...);
  2. the analyser's current state allows the strategy (section 2.2): ranging ->
     range trade; emerging trend and trend -> EMA pullback and breakout IN THE
     TREND'S DIRECTION ONLY; trend only -> slow grind, IN THE TREND'S DIRECTION
     ONLY (owner, 8 November 2026); trend -> also Bollinger bounce, AGAINST THE
     TREND'S DIRECTION ONLY (owner, 7 November 2026); possible reversal ->
     Bollinger bounce, either way; consolidation -> none;
  3. the direction rule allows that direction (section 2.3): a buy needs buy
     side (price above the daily pivot and the 5-minute 100 EMA), a sell needs
     sell side. It does not apply to the range trade, the Bollinger bounce, the
     breakout (owner, 7 November 2026), the slow grind or the level reversal
     (owner, 8 November 2026), in any state; the rule's answer is still recorded.
     The level reversal is allowed in every state except consolidation, either way.
"The current state" is the analyser's state after the last finished 5-minute
candle, and the direction rule uses the entry price. A candidate that fails a
check is kept as BLOCKED with the reason, never as an idea.

Ideas only: nothing here places, changes or closes a trade, or contacts IG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.direction import BUY_SIDE, SELL_SIDE, decide
from analyser.states import DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP

SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL = (
    "slow grind", "EMA pullback", "Bollinger bounce", "range trade", "breakout", "level reversal")
SWITCH = {SLOW_GRIND: "slow_grind", EMA_PULLBACK: "ema_pullback", BOLLINGER_BOUNCE: "bollinger_bounce",
          RANGE_TRADE: "range_trade", BREAKOUT: "breakout", LEVEL_REVERSAL: "level_reversal"}
# Held overnight and closed at 20:30 UK on Friday only (owner, 7 November 2026); every other
# strategy is closed at 20:30 UK every day.
OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
# May open in a big-news window and not closed before big news (owner, 7 and 8 November 2026).
NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
# Not closed on a rejection at a level (owner, 7 and 8 November 2026).
NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
# The direction rule (section 2.3) does not apply to these (owner, 7 and 8 November 2026).
NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
BUY, SELL = "buy", "sell"
# Section 2.2: which states allow which strategy: "any" direction, only in the trend's direction
# ("trend"), or only against it ("against").
ALLOWED_IN = {
    SLOW_GRIND: {TREND: "trend"},                      # trend only (owner, 8 November 2026)
    EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
    BOLLINGER_BOUNCE: {TREND: "against", POSSIBLE_REVERSAL: "any"},
    RANGE_TRADE: {RANGING: "any"},
    BREAKOUT: {EMERGING: "trend", TREND: "trend"},
    # every state except consolidation, either way (owner, 8 November 2026)
    LEVEL_REVERSAL: {RANGING: "any", EMERGING: "any", TREND: "any", POSSIBLE_REVERSAL: "any"},
}


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
    7 November 2026).
    Slow grind (owner, 8 November 2026): any time the market is open, big-news windows included,
    except from hours.close_all_trades_at (20:30) to midnight UK every day, in the first
    slow_grind.week_open_no_new_trades_minutes (15) after the week opens, and from
    slow_grind.rollover_no_new_trades_from (21:55) to slow_grind.rollover_no_new_trades_until (22:15) UK.
    Breakout: UK time from NEW_TRADES_FROM to NEW_TRADES_UNTIL; big-news windows allowed.
    Every other strategy: UK time from NEW_TRADES_FROM to NEW_TRADES_UNTIL, and not in a big-news
    no-new-trades window."""
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


def closed_before_big_news(strategy: str) -> bool:
    """Open trades are closed 15 minutes before big news, except the EMA pullback's, the breakout's
    and the slow grind's."""
    return strategy not in NEWS_ALLOWED


def closed_on_level_rejection(strategy: str) -> bool:
    """Section 4's close on a confirmed rejection at a level, for every strategy except the EMA pullback,
    the breakout and the slow grind."""
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
                     calendar: list | None = None) -> int:
    """Design section 4: every strategy uses TAKE_PROFIT_PIPS (100), except
    - the EMA pullback: its own ema_pullback.take_profit_pips (30) (owner, 7 November 2026);
    - the slow grind: its own slow_grind.take_profit_pips (20) (owner, 8 November 2026);
      each of these two gets TAKE_PROFIT_PIPS instead for a trade opened on a UK day with big news
      for the pair. Give `opened` and `pair`; without them the normal take profit is returned;
    - the breakout: breakout.take_profit_pips (50) on any day;
    - the level reversal: level_reversal.take_profit_pips (20) on any day (owner, 8 November 2026)."""
    if strategy == BREAKOUT:
        return settings.breakout.take_profit_pips
    if strategy == LEVEL_REVERSAL:
        return settings.level_reversal.take_profit_pips
    if strategy not in (EMA_PULLBACK, SLOW_GRIND):
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
    stop_price(); this returns that 6."""
    sw = settings.switches
    if strategy == LEVEL_REVERSAL:
        return settings.level_reversal.stop_beyond_furthest_pips
    if strategy == BREAKOUT:
        return settings.breakout.stop_loss_pips
    if strategy == SLOW_GRIND:
        return settings.slow_grind.stop_loss_pips
    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips


def stop_price(settings: Any, idea: Any) -> Decimal | None:
    """Design section 4: the stop as a price (chart price) when a strategy sets it from its setup:
    the level reversal's, level_reversal.stop_beyond_furthest_pips beyond the furthest point price
    reached past (or short of) the level (the idea's context). None for every other strategy,
    whose stop is stop_loss_pips() from the entry."""
    if idea.strategy != LEVEL_REVERSAL:
        return None
    return idea.context["stop_price"]


def allowed(settings: Any, strategy: str, direction: str, price: Decimal, state: Any, pivot: Decimal | None,
            ema100: Decimal | None) -> tuple[list[str], Any]:
    """Every reason the switch, the state (2.2) or the direction rule (2.3) does not allow
    this strategy in this direction at this price (empty: allowed), and the direction rule."""
    rule = decide(price, "the price", pivot, ema100, "5m 100 EMA", ema100 is not None)
    reasons = []
    if not getattr(settings.switches, SWITCH[strategy]):
        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
    ok_in = ALLOWED_IN[strategy]
    if state.state not in ok_in:
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
    return reasons, rule


def check(settings: Any, pair: str, c: Candidate, state: Any, pivot: Decimal | None,
          ema100: Decimal | None) -> Idea:
    """Turn a candidate into an idea, or a blocked one with every reason."""
    reasons, rule = allowed(settings, c.strategy, c.direction, c.entry_price, state, pivot, ema100)
    idea = Idea(pair, c.strategy, c.direction, c.time, c.entry_price, state.state, state.direction,
                state.trend_type, rule.side, list(c.steps), context=dict(c.context))
    if reasons:
        idea.allowed, idea.blocked_by = False, "; ".join(reasons)
    else:
        exempt = c.strategy in NO_DIRECTION_RULE
        idea.steps.append(f"allowed at entry: {c.strategy} in a {state.state} {state.direction}; direction rule "
                          f"{rule.side} ({rule.reason.replace('the price', 'the entry price')})"
                          + (f"; the direction rule does not apply to {c.strategy}" if exempt else ""))
    return idea
