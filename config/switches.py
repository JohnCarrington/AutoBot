"""The switches in .env (next to the IG secrets), checked at start-up:

  PAIRS_ON                    the pairs switched on, e.g. GBPUSD or GBPUSD,EURUSD
                              (each must have a [pairs.<PAIR>] section in settings.toml)
  NEW_TRADES_FROM             trading hours, UK time "HH:MM": new trades from ...
  NEW_TRADES_UNTIL            ... until (must be earlier than hours.close_all_trades_at
                              in settings.toml, or the same)
  STRATEGY_SLOW_GRIND         on or off
  STRATEGY_EMA_PULLBACK       on or off
  STRATEGY_BOLLINGER_BOUNCE   on or off (the hourly-pierce bounce of 15 November 2026)
  STRATEGY_BOLLINGER_BOUNCE_5M  on or off (the first build's 5-minute band and level bounce, kept and renamed;
                              owner, 19 November 2026)
  PULLBACK_ENTRY              on or off (ON if left out; owner, approved 19 November 2026): the breakout and the Asian
                              range breakout wait for a pullback to the 5-minute 8 EMA and a close back beyond it,
                              within [pullback_entry] wait_candles (6), and open at the next candle's open; a close
                              beyond the 21 EMA against them cancels (strategies/pullback.py)
  HOURLY_CONTEXT              on or off (ON if left out; owner, 21 November 2026): in an hourly DOWN context no buy opens
                              within 5 pips of the daily pivot or the hourly 50 EMA; in an UP context no sell;
                              breakout and Asian range breakout exempt ([entry_filters]; strategies/entry_filters.py,
                              rule 1)
  RSI_STRETCH                 on or off (ON if left out; owner, 21 November 2026, in place of ENTRY_NEAR_EMA8): no sell
                              when the 5-minute RSI 3 is under 30, no buy when over 70; slow grind, breakout, Asian
                              range breakout and session sweep exempt (strategies/entry_filters.py, rule 2b)
  TREND_DAY_RSI_OFF           on or off (ON if left out; owner, 21 November 2026): on Johnny's slow-grind trend day (a
                              slow grind trade in profit between 06:00 and 09:00 UK; until 20:30 UK) RSI_STRETCH does
                              not apply to trades in the trend's direction (strategies/entry_filters.py)
  COUNTER_TREND_TIRING        on or off (ON if left out; owner, 23 November 2026): a bounce (hourly or 5m Bollinger bounce,
                              level reversal, session sweep, New York open reversal) against the analyser's trend
                              opens only if the hourly MACD 35/45/30 histogram is shrinking (1 bar) or past zero,
                              or the 5-minute histogram has crossed zero onto the bounce's side
                              (strategies/entry_filters.py, rule 3)
  TREND_ENDS_IN_CONSOLIDATION on or off (ON if left out; owner, 24 November 2026): once the analyser calls a trend it
                              stays in trend until consolidation: no possible reversal from a trend, and the 100 EMA,
                              fading and ranging exits go to consolidation (analyser/states.py)
  COUNTER_TREND_EMERGING      on or off (ON if left out; owner, 24 November 2026): rule 3 also applies when the analyser
                              says "emerging trend", not only "trend"
  COUNTER_TREND_HOURLY_CONFIRMED on or off (ON if left out; owner, 24 November 2026): in rule 3 the hourly histogram past
                              zero counts as tiring only if it was on the trend's side of zero at an hourly candle since
                              the analyser's state began, and shrinking only while it is on the trend's side
  ENTRY_NEAR_EMA8             on or off (OFF if left out since 21 November 2026; was on): a sell opens only if its entry is no
                              more than 5 pips below the 5-minute 8 EMA, a buy no more than 5 pips above it; the slow
                              grind, breakout, Asian range breakout and session sweep exempt (strategies/entry_filters.py, rule 2)
  EMERGING_LADDER             on or off (ON if left out; owner, 21 November 2026): a trade opened while the analyser said
                              "emerging trend" has its stop at IG moved to +5 once +10, and to +10 once +15 (never
                              backwards; a tighter trail kept) ([emerging_ladder]; trade_manager/manager.py)
  ONE_SIGNAL_ONE_TRADE        on or off (off if left out; owner, 18 November 2026): one trade per rejection
                              candle and direction; the session sweep and New York open reversal under one view at
                              a time (safety/rules.py, rules 9 and 11)
  PLANNER_OBSERVE             on or off (off if left out): the Structural Trade Planner (planner/), OBSERVE ONLY
  STP_OPPORTUNITIES           on or off (OFF if left out; owner, 24 November 2026, OD-01/OD-02/OD-29): STP's tracker
                              keeps several opportunities, each ended only by its own conditions (planner/opportunities.py);
                              observe only by itself
  STP_BIDIRECTIONAL           on or off (OFF if left out; OD-06/OD-16/OD-17): STP proposes one opportunity per direction
                              per hourly re-plan, the 4-hour direction and condition recorded as context only
  STP_AUTHORISES_ENTRIES      on or off (OFF if left out; OD-03/OD-29): the hourly bounce, 5m bounce and level reversal
                              trade only at a live STP opportunity in their direction (stp/authorise.py); refuses every
                              gated idea unless STP_OPPORTUNITIES and STP_BIDIRECTIONAL are also on
  EMA_PULLBACK_TRADING_HOURS  on or off (off if left out; owner, 21 November 2026): new EMA pullback trades only
                              within the trading hours NEW_TRADES_FROM to NEW_TRADES_UNTIL (UK clock), as the other
                              strategies, and every open EMA pullback trade closed at hours.close_all_trades_at (20:30)
                              UK every day, not only on Friday; the 21:55-22:15 rollover pause stays as it is
  EMA_PULLBACK_ONE_AT_A_TIME  on or off (off if left out; owner, 21 November 2026): while an EMA pullback trade is
                              open, no other EMA pullback trade opens (limits.max_open_trades_per_strategy, 1, as the
                              other strategies); setups still form and are logged; a skipped one is logged as refused
  EMA_PULLBACK_TREND_ONLY     on or off (off if left out; owner, 25 November 2026): the EMA pullback opens only when the
                              analyser says "trend" in the trade's direction; "emerging trend" no longer allows it
                              (strategies/common.py, allowed)
  EMA_PULLBACK_SLOPE_DIRECTION on or off (off if left out; owner, 25 November 2026): step 0's 3-hour slope check also
                              checks direction: each hourly 8/13/20 EMA higher than ema_pullback.hourly_slope_candles
                              (3) hourly candles before for a buy, lower for a sell; the size check unchanged
                              (strategies/ema_pullback/strategy.py, HourlyTrendReader)
  EMA_PULLBACK_RECHECK_AT_OPEN on or off (off if left out; owner, 25 November 2026): the full hourly check (step 0) is
                              run again when the entry price is reached, not only at the touch candle; if it fails
                              the setup is cancelled (strategies/ema_pullback/strategy.py, EmaPullback)
  EMA_PULLBACK_ENTRY_PULLBACK_CANDLE on or off (off if left out; owner, 25 November 2026): the EMA pullback's entry is
                              when a later candle trades beyond the touch candle (above its high for a buy, below its
                              low for a sell), in place of 3 pips beyond the last 5 candles' high or low
                              (strategies/ema_pullback/strategy.py)
  ANALYSER_TREND_HOLDS_TO_100EMA on or off (off if left out; owner, 25 November 2026): an emerging trend that started
                              from a breakout is cancelled only by one close back past the 5-minute 100 EMA (above it
                              for a down trend, below it for an up trend), not by 2 closes back inside the Bollinger
                              bands; the level-rejection cancel is unchanged (analyser/states.py)
  EMA_PULLBACK_NO_R3_S3       on or off (off if left out; owner, 25 November 2026): no new EMA pullback buy when the
                              entry price is at or above the day's R3, no new sell at or below the day's S3 (the
                              bot's daily pivot levels; strategies/entry_filters.py)
  BOUNCE_ONLY_NEAR_TIMES      on or off (off if left out): while on, a Bollinger bounce opens only within
                              bounce.near_times_within_minutes (60) of bounce.near_times (10:00, 14:00,
                              16:00 UK) in settings.toml
  STRATEGY_RANGE_TRADE        on or off
  STRATEGY_BREAKOUT           on or off (never on while breakout.stop_loss_pips or
                              breakout.take_profit_pips is 0)
  STRATEGY_LEVEL_REVERSAL     on or off
  STRATEGY_ASIAN_RANGE_BREAKOUT    on or off (owner, 16 November 2026)
  STRATEGY_SESSION_SWEEP           on or off (owner, 16 November 2026)
  STRATEGY_NEW_YORK_OPEN_REVERSAL  on or off (owner, 16 November 2026)
  TRADING                     the master switch, on or off: while off everything runs and is
                              recorded, but no order is ever sent to IG
  STOP_LOSS_PIPS              the stop loss sent with every trade, in pips (whole, 1 to 100),
                              for every strategy except the EMA pullback
  STOP_LOSS_PIPS_EMA_PULLBACK the EMA pullback's stop loss, in pips (whole, 1 to 100)
  TAKE_PROFIT_PIPS            the take profit sent to IG with every trade, in pips
                              (whole, 1 to 1000); the bot may close earlier itself

Everything else is in config/settings.toml. Only these keys are read here:
the secrets in the same file are never looked at, printed or put in a message.
Each switch is documented in docs/SETTINGS.md (a test checks that).
"""

from __future__ import annotations

import re
from datetime import time
from pathlib import Path
from typing import Any, Callable

from config.env_file import parse

SWITCHES_SECTION = "switches"


def _pairs(v: str) -> tuple[str, ...]:
    names = [x.strip() for x in v.split(",")] if v.strip() else []
    if not names:
        raise ValueError("must name at least one pair, e.g. GBPUSD")
    for n in names:
        if not re.fullmatch(r"[A-Z]{6}", n):
            raise ValueError(f"{n!r} is not a pair name like GBPUSD")
    if len(set(names)) != len(names):
        raise ValueError("pairs must not repeat")
    return tuple(names)


def _time(v: str) -> time:
    m = re.fullmatch(r"(\d\d):(\d\d)", v.strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise ValueError(f'must be a UK time written "HH:MM", got {v!r}')
    return time(int(m.group(1)), int(m.group(2)))


def _pips(minimum: int, maximum: int) -> Callable[[str], int]:
    def check(v: str) -> int:
        if not re.fullmatch(r"\d+", v.strip()):
            raise ValueError(f"must be a whole number of pips, got {v!r}")
        n = int(v.strip())
        if not minimum <= n <= maximum:
            raise ValueError(f"must be between {minimum} and {maximum} pips, got {n}")
        return n
    return check


def _on_off(v: str) -> bool:
    if v.strip().lower() not in ("on", "off"):
        raise ValueError(f"must be on or off, got {v!r}")
    return v.strip().lower() == "on"


# .env key -> (name in settings.switches, check)
SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
    "PAIRS_ON": ("pairs_on", _pairs),
    "NEW_TRADES_FROM": ("new_trades_from", _time),
    "NEW_TRADES_UNTIL": ("new_trades_until", _time),
    "STRATEGY_SLOW_GRIND": ("slow_grind", _on_off),
    "STRATEGY_EMA_PULLBACK": ("ema_pullback", _on_off),
    "STRATEGY_BOLLINGER_BOUNCE": ("bollinger_bounce", _on_off),
    "STRATEGY_BOLLINGER_BOUNCE_5M": ("bollinger_bounce_5m", _on_off),
    "BOUNCE_ONLY_NEAR_TIMES": ("bounce_only_near_times", _on_off),
    "PLANNER_OBSERVE": ("planner_observe", _on_off),
    "STP_OPPORTUNITIES": ("stp_opportunities", _on_off),
    "STP_BIDIRECTIONAL": ("stp_bidirectional", _on_off),
    "STP_AUTHORISES_ENTRIES": ("stp_authorises_entries", _on_off),
    "ONE_SIGNAL_ONE_TRADE": ("one_signal_one_trade", _on_off),
    "PULLBACK_ENTRY": ("pullback_entry", _on_off),
    "EMA_PULLBACK_TRADING_HOURS": ("ema_pullback_trading_hours", _on_off),
    "EMA_PULLBACK_ONE_AT_A_TIME": ("ema_pullback_one_at_a_time", _on_off),
    "EMA_PULLBACK_TREND_ONLY": ("ema_pullback_trend_only", _on_off),
    "EMA_PULLBACK_SLOPE_DIRECTION": ("ema_pullback_slope_direction", _on_off),
    "EMA_PULLBACK_RECHECK_AT_OPEN": ("ema_pullback_recheck_at_open", _on_off),
    "EMA_PULLBACK_NO_R3_S3": ("ema_pullback_no_r3_s3", _on_off),
    "EMA_PULLBACK_ENTRY_PULLBACK_CANDLE": ("ema_pullback_entry_pullback_candle", _on_off),
    "ANALYSER_TREND_HOLDS_TO_100EMA": ("analyser_trend_holds_to_100ema", _on_off),
    "HOURLY_CONTEXT": ("hourly_context", _on_off),
    "ENTRY_NEAR_EMA8": ("entry_near_ema8", _on_off),
    "RSI_STRETCH": ("rsi_stretch", _on_off),
    "TREND_DAY_RSI_OFF": ("trend_day_rsi_off", _on_off),
    "EMERGING_LADDER": ("emerging_ladder", _on_off),
    "COUNTER_TREND_TIRING": ("counter_trend_tiring", _on_off),
    "COUNTER_TREND_EMERGING": ("counter_trend_emerging", _on_off),
    "TREND_ENDS_IN_CONSOLIDATION": ("trend_ends_in_consolidation", _on_off),
    "COUNTER_TREND_HOURLY_CONFIRMED": ("counter_trend_hourly_confirmed", _on_off),
    "STRATEGY_RANGE_TRADE": ("range_trade", _on_off),
    "STRATEGY_BREAKOUT": ("breakout", _on_off),
    "STRATEGY_LEVEL_REVERSAL": ("level_reversal", _on_off),
    "STRATEGY_ASIAN_RANGE_BREAKOUT": ("asian_range_breakout", _on_off),
    "STRATEGY_SESSION_SWEEP": ("session_sweep", _on_off),
    "STRATEGY_NEW_YORK_OPEN_REVERSAL": ("new_york_open_reversal", _on_off),
    "TRADING": ("trading", _on_off),
    "STOP_LOSS_PIPS": ("stop_loss_pips", _pips(1, 100)),
    "STOP_LOSS_PIPS_EMA_PULLBACK": ("stop_loss_pips_ema_pullback", _pips(1, 100)),
    "TAKE_PROFIT_PIPS": ("take_profit_pips", _pips(1, 1000)),
}

# Switches that may be left out of .env, and their value then (owner, 15 November 2026: both off by default).
OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "off",
                            # the breakout's and Asian range breakout's pullback entry (owner, 19 November 2026): ON
                            "PULLBACK_ENTRY": "on",
                            "EMA_PULLBACK_TRADING_HOURS": "off", "EMA_PULLBACK_ONE_AT_A_TIME": "off",
                            # the EMA pullback's trend rules (owner, 25 November 2026): all OFF
                            "EMA_PULLBACK_TREND_ONLY": "off", "EMA_PULLBACK_SLOPE_DIRECTION": "off",
                            "EMA_PULLBACK_RECHECK_AT_OPEN": "off", "EMA_PULLBACK_NO_R3_S3": "off",
                            # the EMA pullback's entry and the breakout emerging trend's cancel (owner, 25 November
                            # 2026): both OFF
                            "EMA_PULLBACK_ENTRY_PULLBACK_CANDLE": "off", "ANALYSER_TREND_HOLDS_TO_100EMA": "off",
                            # the entry filters (owner, 21 November 2026): rule 1 ON; rule 2 OFF, replaced by
                            # rule 2b (RSI_STRETCH) ON, with the slow-grind trend day (TREND_DAY_RSI_OFF) ON
                            "HOURLY_CONTEXT": "on", "ENTRY_NEAR_EMA8": "off", "RSI_STRETCH": "on",
                            "TREND_DAY_RSI_OFF": "on",
                            # Johnny's exit for emerging-trend trades (owner, 21 November 2026): ON
                            "EMERGING_LADDER": "on",
                            # rule 3, counter-trend tiring (owner, 23 November 2026): ON
                            "COUNTER_TREND_TIRING": "on",
                            # rule 3: also in an emerging trend; the hourly must have confirmed the trend (owner,
                            # 24 November 2026): ON
                            "COUNTER_TREND_EMERGING": "on", "COUNTER_TREND_HOURLY_CONFIRMED": "on",
                            # a trend ends only in consolidation (owner, 24 November 2026): ON
                            "TREND_ENDS_IN_CONSOLIDATION": "on",
                            # the STP strategy integration (owner, 24 November 2026, OD-29): all OFF until the
                            # owner's separate activation approval
                            "STP_OPPORTUNITIES": "off", "STP_BIDIRECTIONAL": "off", "STP_AUTHORISES_ENTRIES": "off"}


def read_switches(path: Path) -> tuple[dict[str, Any], list[str]]:
    """The checked switches, and a list of problems (empty if all is well)."""
    try:
        values = parse(Path(path).read_text())
    except FileNotFoundError:
        return {}, [f"The file {path} does not exist (it holds the switches)."]
    except PermissionError:
        return {}, [f"The file {path} cannot be read (it holds the switches)."]
    out: dict[str, Any] = {}
    problems: list[str] = []
    for key, (name, check) in SWITCHES.items():
        if key not in values and key in OPTIONAL:
            out[name] = check(OPTIONAL[key])
            continue
        if key not in values:
            problems.append(f"Missing switch {key} in {path}.")
            continue
        try:
            out[name] = check(values[key])
        except ValueError as e:
            problems.append(f"Invalid switch {key} in {path}: {e}.")
    return out, problems
