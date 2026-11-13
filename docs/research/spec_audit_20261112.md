# Where every rule came from: an audit of the bot's specification

Friday 13 November 2026, UK. This is read-only: **nothing in the bot was changed**.

For each part of the bot, every rule in the code is listed: every condition, check, time and number, including the settings and `.env` switches that part reads. Each rule gives:

- the code, quoted with its line numbers;
- the line in `docs/DESIGN.md` it implements;
- where it came from;
- one mark:
  - **the owner's words, unchanged**;
  - **changed from the owner's words**, with both quoted;
  - **added without the owner asking**;
  - **no source found**.

The code is the committed code at `2185156` (the trend proof of 12 November included).

## All parts

| Part | Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---|---:|---:|---:|---:|---:|
| 1. EMA pullback | 23 | 1 | 7 | 0 | 31 |
| 2. Slow grind | 22 | 1 | 7 | 0 | 30 |
| 3. Breakout | 14 | 0 | 4 | 0 | 18 |
| 4. Bollinger bounce | 31 | 1 | 9 | 0 | 41 |
| 5. Range trade | 19 | 0 | 3 | 0 | 22 |
| 6. Level reversal | 15 | 1 | 5 | 0 | 21 |
| 7. The analyser's states | 38 | 3 | 28 | 0 | 69 |
| 8. The trade manager's exits | 34 | 0 | 17 | 0 | 51 |
| 9. The safety rules | 44 | 1 | 10 | 0 | 55 |
| **All** | **240** | **8** | **90** | **0** | **338** |

## Sources and marks

- **The owner's words:**
  - every message the owner sent in the 16 session transcripts on this server, from 6 November 2026 (`~/.claude/projects/`). `/mnt/transcripts` does not exist on this server.
  - Each quote says whether he typed it or pasted it. A pasted message is usually a prompt written for him (a task or "Owner decision" text); both count as the owner's words.
  - **The agreed design of 6 November** also counts as the owner's words. That is the first `docs/DESIGN.md` (commit `c803d53`, 265 lines), which the owner pasted as "the master copy of the design for the new AutoBot, as agreed with Johnny on 6 November 2026".
  - Later lines of `docs/DESIGN.md` were written by the assistant. They are quoted as the line the code implements, but the source given is the owner's message behind them.
- **AutoBot 161:** its code is not on this server. Where a rule comes from 161, the source is the audit reports of 161's code in the owner's repository `JohnCarrington/autobot_reports` (the `*_for_new_bot_*` reports), read from a copy of the public repository; the report files are named in each source. A 161 value counts as the owner's words where the owner (or the agreed design) said to take it from 161.
- **The marks:**
  - **Owner's words, unchanged:** the rule and its numbers match the owner's words as above.
  - **Changed from the owner's words:** an owner source exists, but the code does something different.
  - **Added without the owner asking:** no owner source asks for the rule or the number. This includes numbers the assistant chose. Where the owner had asked for a value to be chosen, that request is quoted, and the mark stays "added" unless the owner later accepted that exact value in his own words.
  - **No source found:** used for none.
- **Shared rules** can appear in a strategy's section and again in the safety rules or the trade manager's section. For example, the level reversal's exemption from the direction rule is 6.15 and 9.26. Each section counts its own.
- **Line numbers** are those of the current files. A quoted line whose file is not the one named at the top of its block carries its own file name. Lines shortened with "..." are marked so.
- **The check:** every quoted code line, `DESIGN.md` line and owner quote was checked against the files and the transcripts:
  - code lines: 999 of 1,004 exact, and the other 5 shortened with "...";
  - owner quotes: all 286 found;
  - `DESIGN.md` quotes: all 266 found.


## 1. EMA pullback

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 23 | 1 | 7 | 0 | 31 |

### 1.1 Indicators on the sell (bid) price
- **Code:** `strategies/ema_pullback/strategy.py:58-63`, `:108`, `:116-119`
  ```python
  58	        side = settings.chart.price
  61	        self.f = ema(self.candles, side, e.hourly_fast_ema_periods)
  108	        self.side = settings.chart.price
  116	    def _o(self, c): return getattr(c, f"{self.side}_open")
  ```
  `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** none in 3.2 (line 2 of the strategy docstring: "Sell (bid) price for every indicator")
- **Source:** owner, 2026-11-07T12:42:17.744Z, PASTED (Stage 9), "using the sell (bid) price for indicators"
- **Mark:** Owner's words, unchanged

### 1.2 Hourly trend: 8, 13, 20 EMAs in order and each rising since the previous hourly candle
- **Code:** `strategies/ema_pullback/strategy.py:61-63`, `:70`, `:77-84`
  ```python
  61	        self.f = ema(self.candles, side, e.hourly_fast_ema_periods)
  62	        self.m = ema(self.candles, side, e.hourly_mid_ema_periods)
  63	        self.sl = ema(self.candles, side, e.hourly_slow_ema_periods)
  70	        now, prev, back = done[-1].start, done[-2].start, done[-1 - n].start
  77	        if f > m > s and f > fp and m > mp and s > sp:
  78	            d = BUY
  79	        elif f < m < s and f < fp and m < mp and s < sp:
  80	            d = SELL
  ```
  `config/settings.toml:236-238`: `hourly_fast_ema_periods = 8` / `hourly_mid_ema_periods = 13` / `hourly_slow_ema_periods = 20`
- **DESIGN.md:** line 139: "hourly 8, 13 and 20 EMAs in order and all rising"
- **Source:** agreed design (c803d53) line 128, "The trend must be established on the hourly chart: hourly 8, 13 and 20 EMAs in order and all rising"; 161 (ema_pullback_audit_for_new_bot_20261106.md, "EMA8 > EMA13 > EMA20 **and** all three must be rising vs the previous H1 (one-bar delta)")
- **Mark:** Owner's words, unchanged

### 1.3 Hourly slope minimum: each EMA over the last 3 hourly candles at least 0.16 pips an hour
- **Code:** `strategies/ema_pullback/strategy.py:67`, `:85`, `:87`
  ```python
  67	        n = self.e.hourly_slope_candles
  85	        slopes = [abs(x - y) / n / self.ppp for x, y in ((f, fb), (m, mb), (s, sb))]
  87	        ok = (min(slopes) >= self.e.hourly_min_slope_pips_per_hour
  ```
  `config/settings.toml:239-240`: `hourly_slope_candles = 3` / `hourly_min_slope_pips_per_hour = 0.16`
- **DESIGN.md:** line 139: "with the slope and gap minimums from 161's service as settings"
- **Source:** agreed design (c803d53) line 128, "with the slope and gap minimums from 161's service as settings"; 161 (ema_pullback_audit_for_new_bot_20261106.md, "`DEFAULT_MIN_EMA8_SLOPE_PIPS_PER_HR = 0.16`", "`DEFAULT_SLOPE_LOOKBACK_BARS = 3`", "3-bar slope of each H1 EMA ... must have the right sign and absolute magnitude ≥ 0.16 pips/hour")
- **Mark:** Changed from the owner's words. **Owner:** (161, as the agreed design directs) "must have the right sign and absolute magnitude ≥ 0.16 pips/hour" / **Code:** takes `abs(x - y)` of the 3-candle change, so only the size is checked, not its sign

### 1.4 Hourly gap minimums: 8 to 13 at least 0.25 pips, 13 to 20 at least 0.20 pips
- **Code:** `strategies/ema_pullback/strategy.py:86-88`
  ```python
  86	        gaps = (abs(f - m) / self.ppp, abs(m - s) / self.ppp)
  87	        ok = (min(slopes) >= self.e.hourly_min_slope_pips_per_hour
  88	              and gaps[0] >= self.e.hourly_min_gap_fast_mid_pips and gaps[1] >= self.e.hourly_min_gap_mid_slow_pips)
  ```
  `config/settings.toml:241-242`: `hourly_min_gap_fast_mid_pips = 0.25` / `hourly_min_gap_mid_slow_pips = 0.20`
- **DESIGN.md:** line 139: "with the slope and gap minimums from 161's service as settings"
- **Source:** agreed design (c803d53) line 128, "with the slope and gap minimums from 161's service"; 161 (ema_pullback_audit_for_new_bot_20261106.md, "`DEFAULT_MIN_SEP_8_13_PIPS = 0.25`", "`DEFAULT_MIN_SEP_13_20_PIPS = 0.20`")
- **Mark:** Owner's words, unchanged

### 1.5 The hourly trend is read once, at the touch candle, from the last hourly candle finished by its start
- **Code:** `strategies/ema_pullback/strategy.py:66`, `:148`, `:153`
  ```python
  66	        done = [c for c in self.candles if c.end <= t]
  148	            trend = self.hourly.at(c.start)
  153	                if trend.direction != d or not trend.qualified:
  ```
- **DESIGN.md:** none (docstring line 23-24 lists it as a choice: "rule 0 is checked at the touch ... from the last finished hourly candle")
- **Source:** none found from the owner. (161 also consults H1 only when arming: ema_pullback_audit_for_new_bot_20261106.md, "The H1 trend is consulted only when arming a NEW setup (admission)"; the owner did not ask for this to be taken from 161.)
- **Mark:** Added without the owner asking

### 1.6 600 stored hourly candles are read to work out the hourly EMAs
- **Code:** `strategies/replay.py:99`
  ```python
  99	        return HourlyTrendReader(self.s, last_candles(self.memo, "1h", end, self.s.ema_pullback.hourly_history_candles))
  ```
  `config/settings.toml:244`: `hourly_history_candles = 600`
- **DESIGN.md:** none
- **Source:** none found (first appears in commit 015ce1a "Stage 9: the four strategies, as trade ideas only"; 161 used `H1_MIN_COMPLETED_CANDLES=200`, ema_pullback_audit_for_new_bot_20261106.md). Owner asked for numbers to become settings: owner, 2026-11-07T12:42:17.744Z, PASTED, "Every number the design does not give becomes a setting, listed for me."
- **Mark:** Added without the owner asking

### 1.7 The touch: price reaches the 5-minute 8 EMA (candle low at or below the last finished candle's 8 EMA, mirror for a sell)
- **Code:** `strategies/ema_pullback/strategy.py:151`, `:178`
  ```python
  151	                if not (self._l(c) <= self.prev_fast if buy else self._h(c) >= self.prev_fast):
  178	        self.prev_fast = fast
  ```
  `strategies/replay.py:133`: `fast, slow = ema(allc, side, s.ema_pullback.fast_ema_periods), ema(allc, side, s.ema_pullback.slow_ema_periods)`; `config/settings.toml:227`: `fast_ema_periods = 8`
- **DESIGN.md:** line 140: "While a 5-minute candle is forming, the live price drops to the 5-minute 8 EMA. Price may cross the 8 and even the 13 EMA."
- **Source:** agreed design (c803d53) line 129, same words: "the live price drops to the 5-minute 8 EMA. Price may cross the 8 and even the 13 EMA."
- **Mark:** Owner's words, unchanged

### 1.8 Every touch candle starts its own setup; several may run at once
- **Code:** `strategies/ema_pullback/strategy.py:113`, `:125`, `:166`
  ```python
  113	        self.setups: list[_Setup] = []
  125	        for st in list(self.setups):
  166	                self.setups.append(_Setup(d, c, entry, [
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:35:04.230Z, PASTED, "Remove every rule in the strategies that is not written in section 3, including any limit of one setup or pause per direction."
- **Mark:** Owner's words, unchanged

### 1.9 A 5-minute close below the 21 EMA (above, for a sell) cancels the setup
- **Code:** `strategies/ema_pullback/strategy.py:142-145`
  ```python
  142	            if slow is not None and ((self._c(c) < slow) if buy else (self._c(c) > slow)):   # 2.
  143	                self.setups.remove(st)
  ```
  `config/settings.toml:229`: `slow_ema_periods = 21`
- **DESIGN.md:** line 141: "If a 5-minute candle closes below the 21 EMA, the setup is cancelled."
- **Source:** agreed design (c803d53) line 130, same words
- **Mark:** Owner's words, unchanged

### 1.10 The cancel applies from the touch candle on, its own close included
- **Code:** `strategies/ema_pullback/strategy.py:158-162`
  ```python
  158	                if (self._c(c) < slow) if buy else (self._c(c) > slow):
  159	                    self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the touch candle closed "
  162	                    continue
  ```
- **DESIGN.md:** none (docstring line 25: "rule 2 applies from the touch candle on (its own close included)", listed as a choice)
- **Source:** none found from the owner (161 does the same: ema_pullback_audit_for_new_bot_20261106.md, "including the arming candle itself — qualifies")
- **Mark:** Added without the owner asking

### 1.11 Entry price: 3 pips beyond the highest high (lowest low) of the 5 completed candles immediately before the touch candle
- **Code:** `strategies/ema_pullback/strategy.py:163-165`
  ```python
  163	                before = self.done[-self.e.entry_lookback_candles:]
  164	                beyond = Decimal(self.e.entry_beyond_pips) * self.ppp
  165	                entry = (max(self._h(x) for x in before) + beyond) if buy else (min(self._l(x) for x in before) - beyond)
  ```
  `config/settings.toml:223-224`: `entry_beyond_pips = 3` / `entry_lookback_candles = 5`
- **DESIGN.md:** line 142: "The entry price is 3 pips above the highest high ... of the five completed 5-minute candles immediately before the touch candle (AutoBot 161's rule)."
- **Source:** owner, 2026-11-07T13:35:04.230Z, PASTED, "EMA pullback rule 3 goes back to AutoBot 161's rule: the entry is 3 pips beyond the highest high (buy) or lowest low (sell) of the five completed 5-minute candles immediately before the touch candle." (also owner, 2026-11-06T15:05:45.886Z, PASTED, "entry 3 pips beyond the high or low of the 5 candles before the pullback")
- **Mark:** Owner's words, unchanged

### 1.12 The trade opens as soon as price reaches the entry price
- **Code:** `strategies/ema_pullback/strategy.py:133`, `:138`
  ```python
  133	            if self._h(c) >= st.entry if buy else self._l(c) <= st.entry:   # 4.
  138	                out.append(Candidate(EMA_PULLBACK, d, c.start, price, st.steps + [
  ```
- **DESIGN.md:** line 143: "The trade opens as soon as the live price reaches the entry price."
- **Source:** agreed design (c803d53) line 132, same words
- **Mark:** Owner's words, unchanged

### 1.13 The entry is looked for from the candle after the touch; a candle that opened past the entry enters at its open
- **Code:** `strategies/ema_pullback/strategy.py:125`, `:134-135`, `:177`
  ```python
  134	                opened = self._o(c) >= st.entry if buy else self._o(c) <= st.entry
  135	                price = self._o(c) if opened else st.entry
  ```
- **DESIGN.md:** none (docstring lines 26-29, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 1.14 Order of checks on each candle: expiry, then entry reached, then the cancel on the close
- **Code:** `strategies/ema_pullback/strategy.py:128`, `:133`, `:142`
  ```python
  128	            if c.start >= st.touch.start + expire:                          # 5.
  133	            if self._h(c) >= st.entry if buy else self._l(c) <= st.entry:   # 4.
  142	            if slow is not None and ((self._c(c) < slow) if buy else (self._c(c) > slow)):   # 2.
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 1.15 The setup expires if it has not opened within 20 minutes
- **Code:** `strategies/ema_pullback/strategy.py:124`, `:128-131`
  ```python
  124	        expire = timedelta(minutes=self.e.setup_expires_after_minutes)
  128	            if c.start >= st.touch.start + expire:                          # 5.
  ```
  `config/settings.toml:222`: `setup_expires_after_minutes = 20`
- **DESIGN.md:** line 144: "If it has not opened within 20 minutes, the setup expires."
- **Source:** owner, 2026-11-06T15:05:45.886Z, PASTED, "EMA pullback: setup expires after 20 minutes"; agreed design (c803d53) line 133, same words as DESIGN.md
- **Mark:** Owner's words, unchanged

### 1.16 The 20 minutes are counted from the touch candle's start (candles starting less than 20 minutes after it)
- **Code:** `strategies/ema_pullback/strategy.py:128`
  ```python
  128	            if c.start >= st.touch.start + expire:                          # 5.
  ```
- **DESIGN.md:** none (docstring lines 27-28: "in candles starting less than 20 minutes after the touch candle started")
- **Source:** none found (161 counts from the touch itself: ema_pullback_audit_for_new_bot_20261106.md, "haven't filled within 20 minutes of the EMA8 touch")
- **Mark:** Added without the owner asking

### 1.17 The 5-minute 13 EMA (setting, not read by any rule)
- **Code:** none reads it (`grep mid_ema_periods` finds only `config/settings_loader.py:407` and tests)
  `config/settings.toml:228`: `mid_ema_periods = 13`
- **DESIGN.md:** line 146: "EMAs: 8, 13 and 21 on the 5-minute chart. No fanning rule."
- **Source:** agreed design (c803d53) line 135, "EMAs: 8, 13 and 21 on the 5-minute chart. No fanning rule."
- **Mark:** Owner's words, unchanged

### 1.18 States: emerging trend and trend, in the trend's direction only
- **Code:** `strategies/common.py:55`, `:281-287`
  ```python
  55	    EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
  285	        if direction != want:
  ```
- **DESIGN.md:** line 43: "Emerging trend | EMA pullback, breakout (3.5), in the trend's direction only"; line 44: "Trend | ... EMA pullback, breakout (3.5), in the trend's direction only"
- **Source:** owner, 2026-11-07T16:53:46.835Z, PASTED, "it trades in a trend and in an emerging trend"; agreed design (c803d53) lines 41-42, "Slow grind, EMA pullback, Bollinger band bounce in the trend's direction only"
- **Mark:** Owner's words, unchanged

### 1.19 The direction rule (daily pivot and 5-minute 100 EMA) applies
- **Code:** `strategies/common.py:49`, `:288-290`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  ```
- **DESIGN.md:** line 54: "Direction rule (applies to every strategy except the range trade, the Bollinger band bounce, the breakout, the slow grind and the level reversal)"
- **Source:** agreed design (c803d53) line 52, "Direction rule (applies to every strategy)"; line 57, "This applies to every strategy"
- **Mark:** Owner's words, unchanged

### 1.20 New trades any time the market is open, except after 20:30 UK on Friday
- **Code:** `strategies/common.py:126-127`, `:144-149`
  ```python
  126	    if not hours.is_open(t):
  127	        reasons.append("the market is closed")
  144	    if strategy == EMA_PULLBACK:
  146	        if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
  149	        return reasons
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 259: "the EMA pullback may open at any time the market is open, not only 06:00 to 20:30, except after 20:30 UK on Friday"
- **Source:** owner, 2026-11-07T16:53:46.835Z, PASTED, "it may open at any time the market is open"; owner, 2026-11-07T17:03:03.382Z, PASTED, "No new EMA pullback trade opens after 20:30 UK on Friday, so none is ever held over the weekend."
- **Mark:** Owner's words, unchanged

### 1.21 May open during a big-news window
- **Code:** `strategies/common.py:144-149` (returns before the news check at `:156-158`)
  ```python
  144	    if strategy == EMA_PULLBACK:
  149	        return reasons
  156	    windows = no_new_trades(settings, pair, t, calendar)
  ```
- **DESIGN.md:** line 264: "This does not apply to the EMA pullback or the breakout (owner, 7 November 2026) ... they may open during the window"
- **Source:** owner, 2026-11-07T16:00:31.550Z, PASTED, "The big-news window does not apply to it: it may open during the window"
- **Mark:** Owner's words, unchanged

### 1.22 Held overnight; closed by the clock only at 20:30 UK on Friday
- **Code:** `strategies/common.py:43`, `:175`
  ```python
  43	OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 213: "or 20:30 UK on Friday, when any EMA pullback trade still open is closed. It is not closed at 20:30 on other days"
- **Source:** owner, 2026-11-07T16:00:31.550Z, PASTED, "It may be held overnight. It is not closed at 20:30, except on Friday: any EMA pullback trade still open at 20:30 UK on Friday is closed then."
- **Mark:** Owner's words, unchanged

### 1.23 Not closed before big news
- **Code:** `strategies/common.py:45`, `:180-183`
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 213: "not closed before big news"
- **Source:** owner, 2026-11-07T16:00:31.550Z, PASTED, "open trades are not closed before big news"
- **Mark:** Owner's words, unchanged

### 1.24 Not closed on a rejection at a level
- **Code:** `strategies/common.py:47`, `:186-189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 213: "the close on a rejection at a level does not apply to it"
- **Source:** owner, 2026-11-07T15:36:57.885Z, PASTED, "The close on a rejection at a level does not apply to it."
- **Mark:** Owner's words, unchanged

### 1.25 No profit lock
- **Code:** `strategies/common.py:196-197`
  ```python
  196	    if strategy != SLOW_GRIND:
  197	        return None
  ```
- **DESIGN.md:** line 212: "there is no profit lock except the slow grind's (above)"
- **Source:** owner, 2026-11-07T13:35:04.230Z, PASTED, "Profit lock: replace the 15-pip lock in DESIGN.md section 4 with: a trade runs until the analyser's state becomes consolidation"; owner, 2026-11-07T14:50:02.336Z, TYPED, "Remove the consolidation exit for every strategy"; owner, 2026-11-07T16:53:46.835Z, PASTED, "12-pip stop and 30-pip take profit ... everything else as now"
- **Mark:** Owner's words, unchanged

### 1.26 Stop loss 12 pips (STOP_LOSS_PIPS_EMA_PULLBACK)
- **Code:** `strategies/common.py:257`
  ```python
  257	    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips
  ```
  `.env:28`: `STOP_LOSS_PIPS_EMA_PULLBACK=12`
- **DESIGN.md:** line 207: "The EMA pullback's stop is 12 pips (owner, 7 November 2026), its own switch in `.env` (`STOP_LOSS_PIPS_EMA_PULLBACK`)."
- **Source:** owner, 2026-11-07T15:36:57.885Z, PASTED, "EMA pullback stop loss is 12 pips. Add a separate .env setting for it, STOP_LOSS_PIPS_EMA_PULLBACK=12"
- **Mark:** Owner's words, unchanged

### 1.27 Take profit 30 pips
- **Code:** `strategies/common.py:236`
  ```python
  236	    return settings.ema_pullback.take_profit_pips if strategy == EMA_PULLBACK else settings.slow_grind.take_profit_pips
  ```
  `config/settings.toml:221`: `take_profit_pips = 30`
- **DESIGN.md:** line 208: "The EMA pullback's take profit is 30 pips (owner, 7 November 2026; `ema_pullback.take_profit_pips`"
- **Source:** owner, 2026-11-07T16:53:46.835Z, PASTED, "12-pip stop and 30-pip take profit"
- **Mark:** Owner's words, unchanged

### 1.28 Take profit 100 pips (TAKE_PROFIT_PIPS) for a trade opened on a big-news day for the pair
- **Code:** `strategies/common.py:234-235`
  ```python
  234	    if opened is not None and pair is not None and big_news_day(settings, pair, opened, calendar):
  235	        return settings.switches.take_profit_pips
  ```
  `.env:29`: `TAKE_PROFIT_PIPS=100`
- **DESIGN.md:** line 208: "an EMA pullback or slow grind trade opened on a day with big news for the pair ... gets the 100 pips of `TAKE_PROFIT_PIPS`"
- **Source:** owner, 2026-11-07T17:09:43.605Z, TYPED, "Decision 1: version 1. Every EMA pullback trade opened on a day with big news for the pair gets the 100-pip take profit from TAKE_PROFIT_PIPS instead of 30." (100: owner, 2026-11-06T15:05:45.886Z, PASTED, "take profit sent to IG: 100 pips")
- **Mark:** Owner's words, unchanged

### 1.29 "Big-news day" is the UK calendar day (midnight to midnight UK) of the opening, with a BIG release for the pair
- **Code:** `strategies/common.py:208-211`
  ```python
  208	    day = t.astimezone(uk).date()
  209	    start = dt.combine(day, tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
  211	    return any(start <= w.release_utc < end for w in big_news_windows(settings, pair, start, end, calendar))
  ```
- **DESIGN.md:** line 213: "for a trade opened on a UK calendar day with a big release for the pair"
- **Source:** owner, 2026-11-07T17:09:43.605Z, TYPED, "opened on a day with big news for the pair" (no day boundary given; "UK calendar day" first appears in DESIGN.md in commit 26f9e1c, written by the assistant)
- **Mark:** Added without the owner asking

### 1.30 Take profit 100 pips for a trade in the trend day's direction on a trend day
- **Code:** `strategies/common.py:232-233`
  ```python
  232	    if trend_day is not None and direction == {"down": SELL, "up": BUY}.get(trend_day):
  233	        return settings.switches.take_profit_pips
  ```
- **DESIGN.md:** line 70: "on a trend day, an EMA pullback or slow grind trade in the trend day's direction ... gets the 100-pip take profit of `TAKE_PROFIT_PIPS`"
- **Source:** owner, 2026-11-08T06:31:08.541Z, PASTED, "On a trend day, any EMA pullback or slow grind trade going in the trend day's direction (back towards the monthly pivot) gets the 100-pip take profit from TAKE_PROFIT_PIPS instead of its usual take profit."
- **Mark:** Owner's words, unchanged

### 1.31 Does not count towards "most at once: 5"
- **Code:** `strategies/common.py:239-241`
  ```python
  239	def counts_towards_most_at_once(strategy: str) -> bool:
  241	    return strategy != EMA_PULLBACK
  ```
- **DESIGN.md:** line 250: "EMA pullback trades do not count towards that limit (owner, 7 November 2026)."
- **Source:** owner, 2026-11-07T16:53:46.835Z, PASTED, "it does not count towards the \"most at once: 5\" limit"
- **Mark:** Owner's words, unchanged

## 2. Slow grind

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 22 | 1 | 7 | 0 | 30 |

### 2.1 Candles and EMA on the sell (bid) price
- **Code:** `strategies/slow_grind/strategy.py:57`, `:62-65`; `strategies/replay.py:132`
  ```python
  57	        self.side = settings.chart.price
  62	    def _o(self, c): return getattr(c, f"{self.side}_open")
  strategies/replay.py:132	        sg_ema = ema(allc, side, s.slow_grind.ema_periods)
  ```
  `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** none in 3.1
- **Source:** owner, 2026-11-07T12:42:17.744Z, PASTED (Stage 9), "using the sell (bid) price for indicators"
- **Mark:** Owner's words, unchanged

### 2.2 A pause: at least 2 candles in a row without a new low, closing below the 21 EMA
- **Code:** `strategies/slow_grind/strategy.py:58`, `:85`, `:112-116`
  ```python
  58	        self.need = settings.slow_grind.min_pause_candles
  85	        if len(w.row) >= self.need:                            # 3. a pause: does price break its lowest point?
  112	        if (self._c(c) < ema) if sell else (self._c(c) > ema):  # 2.
  113	            w.row.append(c)
  ```
  `config/settings.toml:200`: `min_pause_candles = 2`; `config/settings.toml:202`: `ema_periods = 21`
- **DESIGN.md:** line 130: "It counts as a pause once at least 2 candles in a row (`slow_grind.min_pause_candles`) have failed to make a new low while staying below the 21 EMA."
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "Entry: a pause of 2 candles that fail to make a new low (or high) while closing below (or above) the 21 EMA"; confirmed owner, 2026-11-08T05:01:05.500Z, TYPED, "switch the slow grind on with result 13's settings". (Agreed design (c803d53) line 122 had "at least 3 candles"; replaced by the owner's later words.)
- **Mark:** Owner's words, unchanged

### 2.3 No two-candle start (rule 1 removed)
- **Code:** `strategies/slow_grind/strategy.py:2-4` (no start condition in `_step`, lines 76-119)
  ```python
  2	Sell (bid) price, 5-minute candles. Only the rules written in 3.1 (rule 1, the
  3	two-candle start, was removed by the owner on 7 November 2026; the others keep
  ```
- **DESIGN.md:** line 126: "Rule 1, the two-candle start, was removed on 7 November 2026; the others keep their numbers."
- **Source:** owner, 2026-11-07T13:56:12.913Z, TYPED, "Slow grind: remove rule 1, the two-candle start, from docs/DESIGN.md section 3.1 and from the code."
- **Mark:** Owner's words, unchanged

### 2.4 "A new low" means below the low of the candle that made the last low (the reference); the first candle watched is the first reference
- **Code:** `strategies/slow_grind/strategy.py:82-84`, `:102`
  ```python
  82	        if w.ref is None:
  83	            w.ref, w.row = c, []
  84	            return None
  102	        if past(x(c), x(w.ref)):                               # a new low: the next reference, the row starts again
  ```
- **DESIGN.md:** none (docstring lines 13-14, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.5 A new low before the pause counts restarts the row (that candle is the new reference)
- **Code:** `strategies/slow_grind/strategy.py:102-104`
  ```python
  102	        if past(x(c), x(w.ref)):                               # a new low: the next reference, the row starts again
  103	            w.ref, w.row = c, []
  104	            return None
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:10:22.319Z, PASTED, "3 and 4. Keep: a new low before the third candle restarts the pause"
- **Mark:** Owner's words, unchanged

### 2.6 "Below the 21 EMA" is judged on the close
- **Code:** `strategies/slow_grind/strategy.py:112`
  ```python
  112	        if (self._c(c) < ema) if sell else (self._c(c) > ema):  # 2.
  ```
- **DESIGN.md:** none in 3.1 rule 2 ("staying below the 21 EMA")
- **Source:** owner, 2026-11-07T13:10:22.319Z, PASTED, "and \"below the 21 EMA\" is judged on closes"; owner, 2026-11-07T19:58:43.524Z, PASTED, "while closing below (or above) the 21 EMA"
- **Mark:** Owner's words, unchanged

### 2.7 A candle closing exactly on the EMA neither counts nor cancels; the row starts again
- **Code:** `strategies/slow_grind/strategy.py:117-118`
  ```python
  117	        else:
  118	            w.row = []                                          # closed exactly on the EMA
  ```
- **DESIGN.md:** none (docstring lines 17-18, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.8 "The lowest point of the pause" is the lowest low of the row's candles (not the reference)
- **Code:** `strategies/slow_grind/strategy.py:86`
  ```python
  86	            edge = min(self._l(r) for r in w.row) if sell else max(self._h(r) for r in w.row)
  ```
- **DESIGN.md:** line 131: "breaks below the lowest point of the pause"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "entering when price breaks the pause's lowest (or highest) point"; result 13 was tested with "pause 2, the pause's lowest point" (docs/research/slow_grind_variations_20261107.md line 218 ff.), the owner's option "the lowest low of the pause candles" (owner, 2026-11-07T19:37:07.002Z, PASTED)
- **Mark:** Owner's words, unchanged

### 2.9 The sell opens as soon as price breaks below the pause's lowest point
- **Code:** `strategies/slow_grind/strategy.py:87`, `:101`
  ```python
  87	            if past(x(c), edge):
  101	                return Candidate(SLOW_GRIND, w.direction, c.start, price, steps)
  ```
- **DESIGN.md:** line 131: "The sell opens as soon as the live price breaks below the lowest point of the pause."
- **Source:** agreed design (c803d53) line 123, "The sell opens as soon as the live price breaks below the lowest point of the pause."
- **Mark:** Owner's words, unchanged

### 2.10 A candle that opened past the pause's lowest point enters at its open
- **Code:** `strategies/slow_grind/strategy.py:88-89`
  ```python
  88	                opened = past(self._o(c), edge)
  89	                price = self._o(c) if opened else edge
  ```
- **DESIGN.md:** none (docstring lines 21-22, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.11 The candle that opened the trade becomes the next reference
- **Code:** `strategies/slow_grind/strategy.py:100`
  ```python
  100	                w.ref, w.row = c, []
  ```
- **DESIGN.md:** none (docstring lines 22-23, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.12 Order of checks on each candle: the break first, then the new low, then the cancel on the close
- **Code:** `strategies/slow_grind/strategy.py:85`, `:102`, `:105`
  ```python
  85	        if len(w.row) >= self.need:                            # 3. a pause: does price break its lowest point?
  102	        if past(x(c), x(w.ref)):                               # a new low: the next reference, the row starts again
  105	        if (self._c(c) > ema) if sell else (self._c(c) < ema):  # 4.
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.13 A close above the 21 EMA cancels the setup; no time limit
- **Code:** `strategies/slow_grind/strategy.py:105-111`
  ```python
  105	        if (self._c(c) > ema) if sell else (self._c(c) < ema):  # 4.
  110	            w.ref, w.row = None, []
  111	            return None
  ```
  `config/settings.toml:202`: `ema_periods = 21`
- **DESIGN.md:** line 132: "If a candle closes above the 21 EMA, the setup is cancelled. No time limit"
- **Source:** agreed design (c803d53) line 124, "If a candle closes above the 21 EMA, the setup is cancelled. No time limit: a long pause becomes consolidation in the analyser."
- **Mark:** Owner's words, unchanged

### 2.14 After a cancel nothing carries over: the next candle is the next reference
- **Code:** `strategies/slow_grind/strategy.py:110`, `:82-83`
  ```python
  110	            w.ref, w.row = None, []
  82	        if w.ref is None:
  83	            w.ref, w.row = c, []
  ```
- **DESIGN.md:** none (docstring lines 24-25, listed as a choice)
- **Source:** none found
- **Mark:** Added without the owner asking

### 2.15 One row (pause) per direction at a time
- **Code:** `strategies/slow_grind/strategy.py:59`, `:51`
  ```python
  51	    row: list = field(default_factory=list)   # candles in a row without a new low, closing below the EMA
  59	        self.watch = {SELL: _Watch(SELL), BUY: _Watch(BUY)}
  ```
- **DESIGN.md:** none (docstring lines 26-27: "so in each direction there is one row at a time, by the meaning of \"in a row\", not by a limit")
- **Source:** owner, 2026-11-07T13:35:04.230Z, PASTED, "Remove every rule in the strategies that is not written in section 3, including any limit of one setup or pause per direction."
- **Mark:** Changed from the owner's words. **Owner:** "including any limit of one setup or pause per direction" / **Code:** keeps a single watch (one reference, one row) per direction

### 2.16 States: trend only (either type), in the trend's direction only
- **Code:** `strategies/common.py:54`, `:281-287`
  ```python
  54	    SLOW_GRIND: {TREND: "trend"},                      # trend only (owner, 8 November 2026)
  285	        if direction != want:
  ```
- **DESIGN.md:** line 133: "Only in a trend (either type, slow grind or strong push), in the trend's direction (2.2); not in an emerging trend."
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "Trend only, in the trend's direction."
- **Mark:** Owner's words, unchanged

### 2.17 No direction rule, no other direction filter
- **Code:** `strategies/common.py:49`, `:289`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  ```
- **DESIGN.md:** line 133: "The direction rule (2.3) does not apply, and there is no other direction filter."
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "No direction filter, and regardless of open EMA pullback trades."
- **Mark:** Owner's words, unchanged

### 2.18 Stop loss 15 pips
- **Code:** `strategies/common.py:255-256`
  ```python
  255	    if strategy == SLOW_GRIND:
  256	        return settings.slow_grind.stop_loss_pips
  ```
  `config/settings.toml:205`: `stop_loss_pips = 15`
- **DESIGN.md:** line 134: "Stop loss 15 pips (`slow_grind.stop_loss_pips`)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "Stop 15 pips"
- **Mark:** Owner's words, unchanged

### 2.19 Take profit 20 pips
- **Code:** `strategies/common.py:236`
  ```python
  236	    return settings.ema_pullback.take_profit_pips if strategy == EMA_PULLBACK else settings.slow_grind.take_profit_pips
  ```
  `config/settings.toml:206`: `take_profit_pips = 20`
- **DESIGN.md:** line 134: "take profit 20 pips (`slow_grind.take_profit_pips`)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "take profit 20 pips, or 100 on a big-news day"
- **Mark:** Owner's words, unchanged

### 2.20 Take profit 100 pips (TAKE_PROFIT_PIPS) on a big-news day for the pair
- **Code:** `strategies/common.py:234-235`
  ```python
  234	    if opened is not None and pair is not None and big_news_day(settings, pair, opened, calendar):
  235	        return settings.switches.take_profit_pips
  ```
  `.env:29`: `TAKE_PROFIT_PIPS=100`
- **DESIGN.md:** line 134: "or 100 pips (`TAKE_PROFIT_PIPS`) for a trade opened on a UK day with big news for the pair"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "take profit 20 pips, or 100 on a big-news day"
- **Mark:** Owner's words, unchanged

### 2.21 "Big-news day" is the UK calendar day of the opening, with a BIG release for the pair
- **Code:** `strategies/common.py:208-211`
  ```python
  208	    day = t.astimezone(uk).date()
  209	    start = dt.combine(day, tm(0, 0), tzinfo=uk).astimezone(timezone.utc)
  211	    return any(start <= w.release_utc < end for w in big_news_windows(settings, pair, start, end, calendar))
  ```
- **DESIGN.md:** line 210: "for a trade opened on a UK calendar day with a big release for the pair"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "or 100 on a big-news day" (no day boundary given; "UK calendar day" was written by the assistant, commit 26f9e1c)
- **Mark:** Added without the owner asking

### 2.22 Take profit 100 pips for a trade in the trend day's direction on a trend day
- **Code:** `strategies/common.py:232-233`
  ```python
  232	    if trend_day is not None and direction == {"down": SELL, "up": BUY}.get(trend_day):
  233	        return settings.switches.take_profit_pips
  ```
- **DESIGN.md:** line 134: "or in the trend day's direction on a trend day (2.4)"
- **Source:** owner, 2026-11-08T06:31:08.541Z, PASTED, "On a trend day, any EMA pullback or slow grind trade going in the trend day's direction (back towards the monthly pivot) gets the 100-pip take profit from TAKE_PROFIT_PIPS"
- **Mark:** Owner's words, unchanged

### 2.23 Profit lock 15/10: once 15 pips in profit, closed if price comes back to 10 pips in profit
- **Code:** `strategies/common.py:196-198`
  ```python
  196	    if strategy != SLOW_GRIND:
  197	        return None
  198	    return settings.slow_grind.lock_from_pips, settings.slow_grind.lock_at_pips
  ```
  `config/settings.toml:209-210`: `lock_from_pips = 15` / `lock_at_pips = 10`
- **DESIGN.md:** line 210: "**Profit lock 15/10:** once the trade has been 15 pips in profit (`slow_grind.lock_from_pips`), it is closed if price comes back to 10 pips in profit (`slow_grind.lock_at_pips`)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "once 15 pips up, close if it comes back to 10 up"
- **Mark:** Owner's words, unchanged

### 2.24 No new trade from 20:30 UK to midnight, every day
- **Code:** `strategies/common.py:133-134`
  ```python
  133	        if lt >= settings.hours.close_all_trades_at:
  134	            reasons.append(f"from {settings.hours.close_all_trades_at:%H:%M} UK to midnight: no new {strategy} trade")
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 260: "except: from 20:30 UK to midnight every day"
- **Source:** owner, 2026-11-08T05:01:05.500Z, TYPED, "holding rule 2: closed at 20:30 UK every day, and no new trade from 20:30 to midnight UK"
- **Mark:** Owner's words, unchanged

### 2.25 No new trade in the first 15 minutes after the week opens (Sunday)
- **Code:** `strategies/common.py:138-142`
  ```python
  139	            opened = hours.session(t)[0]
  140	            if t < opened + timedelta(minutes=sg.week_open_no_new_trades_minutes):
  ```
  `config/settings.toml:214`: `week_open_no_new_trades_minutes = 15`
- **DESIGN.md:** line 260: "in the first 15 minutes after the market opens on Sunday (`slow_grind.week_open_no_new_trades_minutes`)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "Opens at any time the market is open, except the first 15 minutes after the Sunday open, 21:55 to 22:15 UK"
- **Mark:** Owner's words, unchanged

### 2.26 No new trade from 21:55 to 22:15 UK
- **Code:** `strategies/common.py:135-137`
  ```python
  135	        if sg.rollover_no_new_trades_from <= lt < sg.rollover_no_new_trades_until:
  ```
  `config/settings.toml:215-216`: `rollover_no_new_trades_from = "21:55"` / `rollover_no_new_trades_until = "22:15"`
- **DESIGN.md:** line 260: "and from 21:55 to 22:15 UK (`slow_grind.rollover_no_new_trades_from`, `slow_grind.rollover_no_new_trades_until`)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "except the first 15 minutes after the Sunday open, 21:55 to 22:15 UK"
- **Mark:** Owner's words, unchanged

### 2.27 Otherwise new trades any time the market is open (not only 06:00 to 20:30), big-news windows included
- **Code:** `strategies/common.py:126-127`, `:129`, `:143`
  ```python
  126	    if not hours.is_open(t):
  127	        reasons.append("the market is closed")
  129	    if strategy == SLOW_GRIND:
  143	        return reasons
  ```
- **DESIGN.md:** line 135: "New trades at any time the market is open, big-news windows included"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "Opens at any time the market is open" and "News as the EMA pullback: may open during the window, not closed before big news."
- **Mark:** Owner's words, unchanged

### 2.28 Closed at 20:30 UK every day
- **Code:** `strategies/common.py:175`
  ```python
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 135: "Any slow grind trade still open at 20:30 UK is closed, every day"
- **Source:** owner, 2026-11-08T05:01:05.500Z, TYPED, "holding rule 2: closed at 20:30 UK every day"
- **Mark:** Owner's words, unchanged

### 2.29 Not closed before big news
- **Code:** `strategies/common.py:45`, `:183`
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 135: "not closed before big news"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "News as the EMA pullback: may open during the window, not closed before big news."
- **Mark:** Owner's words, unchanged

### 2.30 Not closed on a rejection at a level
- **Code:** `strategies/common.py:47`, `:189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 134: "no close on a rejection at a level (section 4)"
- **Source:** owner, 2026-11-07T19:58:43.524Z, PASTED, "No close on a rejection at a level."
- **Mark:** Owner's words, unchanged

## 3. Breakout

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 14 | 0 | 4 | 0 | 18 |

Note: "one breakout trade open at a time" (DESIGN.md line 187) is enforced in the safety rules, not in the files of this section, so it is not listed here.

### 3.1 Only when the analyser moves into an emerging trend out of a range or a consolidation
- **Code:** `strategies/breakout/strategy.py:33-34, 95-97`
  ```python
  33	# The analyser's reasons for these changes (analyser/states.py), by the state left.
  34	BREAKOUT_REASONS = {CONSOLIDATION: "broke out of the consolidation", RANGING: "broke out of the range"}
  95	        left = getattr(change, "previous_state", None) if change is not None else None
  96	        if (left in BREAKOUT_REASONS and change.state == EMERGING
  97	                and str(change.reason).startswith(BREAKOUT_REASONS[left])):
  ```
- **DESIGN.md:** line 182: "It looks for a trade only at the moment the analyser moves into an emerging trend because price broke out of a range (two closes beyond the same band, section 2.5) or because a 5-minute candle closed outside the Bollinger band out of a consolidation: that candle is the breakout candle."
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "Owner decision: switch the breakout on with this setup, exactly as tested: - It looks for a trade when the analyser moves into an emerging trend because price broke out of a range, or because a candle closed outside the band out of a consolidation." (First version: owner, 2026-11-07T17:48:56Z, PASTED, "only at the moment the analyser moves from consolidation to an emerging trend because a candle closed outside the Bollinger band".) What counts as a range/consolidation breakout is decided in the analyser (other section).
- **Mark:** Owner's words, unchanged

### 3.2 Entry: buy above the breakout candle's high, sell below its low
- **Code:** `strategies/breakout/strategy.py:72, 98, 104`
  ```python
  72	            hit = self._h(c) > st.price if buy else self._l(c) < st.price
  98	            d = BUY if change.direction == UP else SELL
  104	            price = self._h(c) if d == BUY else self._l(c)
  ```
- **DESIGN.md:** line 183: "A buy (breakout up) opens as soon as price breaks above the breakout candle's high; a sell (breakout down) as soon as price breaks below its low."
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "A buy opens when price breaks above that breakout candle's high; a sell when it breaks below its low."
- **Mark:** Owner's words, unchanged

### 3.3 Setup expires if not broken within 3 candles
- **Code:** `strategies/breakout/strategy.py:51, 91-94`
  ```python
  51	        self.limit = settings.breakout.trigger_within_candles
  91	            st.waited += 1
  92	            if st.waited >= self.limit:
  93	                self.setups.remove(st)
  94	                self.notes.append((c.start, st.direction, f"expired: {plain(st.price)} not broken within {self.limit} candles"))
  ```
  `config/settings.toml:252`: `trigger_within_candles = 3`
- **DESIGN.md:** line 184: "If price does not break it within 3 candles after the breakout candle (`breakout.trigger_within_candles`), the setup expires."
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "If price does not break it within 3 candles, the setup expires."
- **Mark:** Owner's words, unchanged

### 3.4 A candle that opened past the trigger enters at its open (stored candles)
- **Code:** `strategies/breakout/strategy.py:74-75`
  ```python
  74	                opened = self._o(c) > st.price if buy else self._o(c) < st.price
  75	                px = self._o(c) if opened else st.price
  ```
- **DESIGN.md:** none
- **Source:** none found (no owner message on gap entries; module docstring line 17-18 "a candle that opened past the price enters at its open").
- **Mark:** Added without the owner asking

### 3.5 Only in the direction of the day's move: entry price above (buy) / below (sell) the open of the 00:00 UK 5-minute candle
- **Code:** `strategies/breakout/strategy.py:66-68, 77, 81-84`
  ```python
  66	        lt = c.start.astimezone(self.uk)
  67	        if lt.time() == clock(0, 0):
  68	            self.day_open = (lt.date(), self._o(c))
  77	                op = self.day_open[1] if self.day_open and self.day_open[0] == lt.date() else None
  81	                if not (px > op if buy else px < op):
  82	                    self.notes.append((c.start, st.direction, f"broken at {plain(px)}, but {'not above' if buy else 'not below'} "
  83	                                                              f"the day's open {plain(op)}: no trade"))
  84	                    continue
  ```
  `config/settings.toml:20`: `timezone = "Europe/London"`
- **DESIGN.md:** line 185: "a buy only when the entry price is above that day's 00:00 UK open, a sell only when it is below (the open of the 5-minute candle starting at 00:00 UK, sell price)."
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "It only takes a breakout in the direction of the day's move so far: a buy only when price is above that day's 00:00 UK open, a sell only when it is below." (tested as filter 5 in owner, 2026-11-07T19:20:22Z, PASTED, "The day's move so far: price on the trade's side of that day's open.")
- **Mark:** Owner's words, unchanged

### 3.6 No trade on a day whose 00:00 UK candle was not seen
- **Code:** `strategies/breakout/strategy.py:77-80`
  ```python
  77	                op = self.day_open[1] if self.day_open and self.day_open[0] == lt.date() else None
  78	                if op is None:
  79	                    self.notes.append((c.start, st.direction, "broken, but the day's 00:00 UK open was not seen: no trade"))
  80	                    continue
  ```
- **DESIGN.md:** none (only the module docstring, strategy.py line 13-14)
- **Source:** none found
- **Mark:** Added without the owner asking

### 3.7 Highs, lows and opens on the sell (bid) price
- **Code:** `strategies/breakout/strategy.py:50, 59-61`
  ```python
  50	        self.side = settings.chart.price
  59	    def _o(self, c): return getattr(c, f"{self.side}_open")
  60	    def _h(self, c): return getattr(c, f"{self.side}_high")
  61	    def _l(self, c): return getattr(c, f"{self.side}_low")
  ```
  `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** line 116: "Every indicator, for the analyser and the strategies, is worked out from the sell (bid) price"; line 185 "sell price".
- **Source:** owner, 2026-11-06T21:22:13Z, PASTED, "My IG chart is set to the sell (bid) price ... Change the levels, and every indicator worked out for the analyser and strategies, to use the sell (bid) price". (Agreed design (c803d53) line 180 had "All levels use the buy (OFR) price"; the owner changed it in the message quoted.)
- **Mark:** Owner's words, unchanged

### 3.8 Allowed at entry only in an emerging trend or a trend, in the trend's direction
- **Code:** `strategies/common.py:58, 278-287`
  ```python
  58	    BREAKOUT: {EMERGING: "trend", TREND: "trend"},
  278	    ok_in = ALLOWED_IN[strategy]
  279	    if state.state not in ok_in:
  280	        reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
  281	    elif ok_in[state.state] in ("trend", "against"):
  282	        want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
  ...
  285	        if direction != want:
  ```
- **DESIGN.md:** line 43: "Emerging trend | EMA pullback, breakout (3.5), in the trend's direction only"; line 44: "Trend | ... EMA pullback, breakout (3.5), in the trend's direction only"
- **Source:** no owner message names the states the breakout is allowed in at entry; the owner only defined when it looks for a setup (owner, 2026-11-07T17:48:56Z, PASTED, "only at the moment the analyser moves from consolidation to an emerging trend"). Added in commit b2514d8 (2026-11-07 17:53, "new breakout strategy (off)").
- **Mark:** Added without the owner asking

### 3.9 The direction rule (2.3) does not apply
- **Code:** `strategies/common.py:49, 289`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  ```
- **DESIGN.md:** line 185: "The direction rule (2.3) does not apply to it."; line 59.
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "The direction rule does not apply to it."
- **Mark:** Owner's words, unchanged

### 3.10 Its switch STRATEGY_BREAKOUT
- **Code:** `strategies/common.py:39-40, 276-277`
  ```python
  39	SWITCH = {SLOW_GRIND: "slow_grind", EMA_PULLBACK: "ema_pullback", BOLLINGER_BOUNCE: "bollinger_bounce",
  40	          RANGE_TRADE: "range_trade", BREAKOUT: "breakout", LEVEL_REVERSAL: "level_reversal"}
  276	    if not getattr(settings.switches, SWITCH[strategy]):
  277	        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
  ```
  `.env:22`: `STRATEGY_BREAKOUT=on`
- **DESIGN.md:** line 361: "**Switches in `.env`** ..."
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "Its .env switch is STRATEGY_BREAKOUT"; owner, 2026-11-07T19:24:52Z, PASTED, "Owner decision: switch the breakout on".
- **Mark:** Owner's words, unchanged

### 3.11 The bot refuses to start with STRATEGY_BREAKOUT on while its stop or take profit is 0
- **Code:** `config/settings_loader.py:671-673`
  ```python
  671	    if sw["breakout"] and not (v["breakout"]["stop_loss_pips"] and v["breakout"]["take_profit_pips"]):
  672	        raise SettingsError(f"Switch STRATEGY_BREAKOUT in {where} is on, but breakout.stop_loss_pips and "
  673	                            "breakout.take_profit_pips are not both chosen (0 means not chosen) in settings.toml.")
  ```
  `config/settings.toml:254-255`: `# 10 November 2026, with the bounce and range trade's STOP_LOSS_PIPS). 0 would mean` / `# "not chosen": the bot refuses to start with STRATEGY_BREAKOUT on while either is 0.`
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "Its stop loss and take profit are settings, not yet chosen ... it stays off until the owner chooses the stop and take profit." (the owner asked for the switch to stay off, not for a start-up refusal)
- **Mark:** Added without the owner asking

### 3.12 Stop loss 12 pips
- **Code:** `strategies/common.py:253-254`
  ```python
  253	    if strategy == BREAKOUT:
  254	        return settings.breakout.stop_loss_pips
  ```
  `config/settings.toml:256`: `stop_loss_pips = 12`
- **DESIGN.md:** line 186: "Stop loss 12 pips (`breakout.stop_loss_pips`; owner, 10 November 2026)"; line 207, 209.
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "Put changes 1, 2 and 3 live exactly as tested: the 12-pip stop for the bounce, range trade and breakout". (DESIGN.md's "owner, 10 November 2026" comes from commit 0e1492b, 2026-11-10 15:36; no owner message of 10 November asking for it was found in owner_messages.txt. First value: owner, 2026-11-07T19:24:52Z, PASTED, "Stop loss 6 pips".)
- **Mark:** Owner's words, unchanged

### 3.13 Take profit 50 pips, on any day
- **Code:** `strategies/common.py:226-227`
  ```python
  226	    if strategy == BREAKOUT:
  227	        return settings.breakout.take_profit_pips
  ```
  `config/settings.toml:257`: `take_profit_pips = 50`
- **DESIGN.md:** line 186: "take profit 50 pips (`breakout.take_profit_pips`)"; line 208: "The breakout's is 50 pips (`breakout.take_profit_pips`) ... on any day."
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "Stop loss 6 pips, take profit 50 pips (breakout.stop_loss_pips = 6, breakout.take_profit_pips = 50)."
- **Mark:** Owner's words, unchanged

### 3.14 New trades only from 06:00 to 20:30 UK
- **Code:** `strategies/common.py:150-155`
  ```python
  150	    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
  151	    sw = settings.switches
  152	    if not (sw.new_trades_from <= lt < sw.new_trades_until):
  153	        reasons.append(f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK")
  154	    if strategy == BREAKOUT:
  155	        return reasons
  ```
  `.env:19-20`: `NEW_TRADES_FROM=06:00`, `NEW_TRADES_UNTIL=20:30`
- **DESIGN.md:** line 187: "New trades only from 06:00 to 20:30 UK"
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "New trades only from 06:00 to 20:30 UK."
- **Mark:** Owner's words, unchanged

### 3.15 May open during a big-news window
- **Code:** `strategies/common.py:45, 154-155`
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  154	    if strategy == BREAKOUT:
  155	        return reasons
  ```
- **DESIGN.md:** line 187: "it may open during a big-news window"; line 264.
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "Hours, news and the Friday rules as for the EMA pullback." (the EMA pullback may open in a big-news window); not repealed by owner, 2026-11-07T19:24:52Z, PASTED, which kept "It may be held overnight and through news".
- **Mark:** Owner's words, unchanged

### 3.16 Not closed before big news
- **Code:** `strategies/common.py:180-183`
  ```python
  180	def closed_before_big_news(strategy: str) -> bool:
  181	    """Open trades are closed 15 minutes before big news, except the EMA pullback's, the breakout's
  182	    and the slow grind's."""
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 209: "not closed before big news"
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "It may be held overnight and through news"
- **Mark:** Owner's words, unchanged

### 3.17 Held overnight; closed at 20:30 UK on Friday only
- **Code:** `strategies/common.py:43, 174-176`
  ```python
  43	OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
  174	        cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  176	            return cut.astimezone(timezone.utc)
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 209: "or 20:30 UK on Friday, when any breakout trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight)"
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "It may be held overnight and through news, and is closed at 20:30 UK on Friday."
- **Mark:** Owner's words, unchanged

### 3.18 No close on a rejection at a level
- **Code:** `strategies/common.py:47, 186-189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  186	def closed_on_level_rejection(strategy: str) -> bool:
  ...
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 186: "No close on a rejection at a level."
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "No close on a rejection at a level."
- **Mark:** Owner's words, unchanged

## 4. Bollinger bounce

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 31 | 1 | 9 | 0 | 41 |

Note: the bounce's limit of one trade per direction (settings `[limits] bollinger_bounce_extra_opposite_direction_trades = 1`) and the trade manager's mechanics of the band close are in the safety and trade-manager sections, not listed here.

### 4.1 Allowed only in a trend (against its direction) and in a possible reversal (either way); not in an emerging trend
- **Code:** `strategies/common.py:56, 281-287`
  ```python
  56	    BOLLINGER_BOUNCE: {TREND: "against", POSSIBLE_REVERSAL: "any"},
  281	    elif ok_in[state.state] in ("trend", "against"):
  282	        want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
  283	        if ok_in[state.state] == "against":
  284	            want = {SELL: BUY, BUY: SELL}.get(want)
  ```
- **DESIGN.md:** line 44: "Bollinger band bounce against the trend's direction only (owner, 7 November 2026)"; line 45: "Possible reversal | Bollinger band bounce"; line 49: "The Bollinger band bounce does not trade in an emerging trend"
- **Source:** owner, 2026-11-07T17:38:00Z, TYPED, "Use version 3 for the bounce; update DESIGN, code and tests", version 3 being (owner, 2026-11-07T17:35:26Z, PASTED) "Possible reversal, plus emerging trend and trend but only against the trend's direction, and only in trend (not emerging trend)."
- **Mark:** Owner's words, unchanged

### 4.2 The direction rule (2.3) does not apply
- **Code:** `strategies/common.py:49, 289`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  ```
- **DESIGN.md:** line 59: "This applies to every strategy except the range trade, the Bollinger band bounce and the breakout (owner, 7 November 2026)"
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "The direction rule does not apply to the Bollinger bounce at all, in any state." (Agreed design (c803d53) line 57 had "This applies to every strategy, including bounces in a possible reversal"; the owner changed it.)
- **Mark:** Owner's words, unchanged

### 4.3 Its switch STRATEGY_BOLLINGER_BOUNCE
- **Code:** `strategies/common.py:39, 276-277`
  ```python
  39	SWITCH = {SLOW_GRIND: "slow_grind", EMA_PULLBACK: "ema_pullback", BOLLINGER_BOUNCE: "bollinger_bounce",
  276	    if not getattr(settings.switches, SWITCH[strategy]):
  277	        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
  ```
  `.env:24`: `STRATEGY_BOLLINGER_BOUNCE=on`
- **DESIGN.md:** line 361: "**Switches in `.env`** ..."
- **Source:** owner, 2026-11-07T07:53:05Z, PASTED, "Move these into .env ... each strategy on or off (slow grind, EMA pullback, Bollinger bounce, range trade)"
- **Mark:** Owner's words, unchanged

### 4.4 Worked out on the sell (bid) price
- **Code:** `rejection/watch.py:139, 146-149`
  ```python
  139	        self.side = settings.chart.price
  146	    def _o(self, c): return getattr(c, f"{self.side}_open")
  147	    def _h(self, c): return getattr(c, f"{self.side}_high")
  148	    def _l(self, c): return getattr(c, f"{self.side}_low")
  149	    def _c(self, c): return getattr(c, f"{self.side}_close")
  ```
  `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** line 116: "Every indicator, for the analyser and the strategies, is worked out from the sell (bid) price"
- **Source:** owner, 2026-11-06T21:31:50Z, PASTED, "Stage 6: the shared rejection part ... Use the sell (bid) price, like the levels."
- **Mark:** Owner's words, unchanged

### 4.5 Bollinger band: 20 periods, 2 standard deviations
- **Code:** `rejection/watch.py:213-217` (the band passed in)
  ```python
  213	        if band is not None:
  214	            if direction == SELL and self._h(c) > band.upper:
  ```
  `config/settings.toml:289-290`: `bollinger_periods = 20`, `bollinger_std_devs = 2`
- **DESIGN.md:** line 109: "| Bollinger bands | 20 periods, 2 standard deviations | Trend or range |"
- **Source:** agreed design (c803d53) line 104, "| Bollinger bands | 20 periods, 2 standard deviations | Trend or range |"
- **Mark:** Owner's words, unchanged

### 4.6 The band needs a real pierce (high above the upper band for a sell; low below the lower band for a buy)
- **Code:** `rejection/watch.py:213-217`
  ```python
  213	        if band is not None:
  214	            if direction == SELL and self._h(c) > band.upper:
  215	                out.append({"what": "upper Bollinger band", "price": band.upper, "level": None})
  216	            if direction == BUY and self._l(c) < band.lower:
  217	                out.append({"what": "lower Bollinger band", "price": band.lower, "level": None})
  ```
- **DESIGN.md:** line 150: "The Bollinger band needs a real pierce."
- **Source:** owner, 2026-11-06T21:42:54Z, TYPED, "This applies to levels only; the Bollinger band still needs a real pierce."; agreed design (c803d53) line 139, "Price pierces a level or the Bollinger band."
- **Mark:** Owner's words, unchanged

### 4.7 For a level, coming within 3 pips counts as a pierce
- **Code:** `rejection/watch.py:218-219`
  ```python
  218	        if version == BOUNCE and levels is not None:
  219	            near = Decimal(self.s.rejection.near_level_within_pips) * Decimal(self.s.market.points_per_pip)
  ```
  `config/settings.toml:415`: `near_level_within_pips = 3`
- **DESIGN.md:** line 150: "For a level, a candle that comes within 3 pips of it counts the same as a pierce (a setting)."
- **Source:** owner, 2026-11-06T21:42:54Z, TYPED, "a candle that comes within 3 pips of a level counts the same as a pierce of that level. Make the 3 pips a setting."
- **Mark:** Owner's words, unchanged

### 4.8 No rule about the side the candle opened on (the "near-side" rule removed for the strategies)
- **Code:** `rejection/watch.py:223`
  ```python
  223	                from_side = self.design_only or (self._o(c) <= lv.price if direction == SELL else self._o(c) >= lv.price)
  ```
- **DESIGN.md:** none (3.3 line 150 has no side rule)
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Remove every rule in the strategies that is not written in section 3 ... List each one you remove." (Earlier the same day, owner, 2026-11-07T13:10:22Z, PASTED, "Bounce: keep the near-side rule for levels"; the 13:35 message came after it; removal listed in commit 325c701.)
- **Mark:** Owner's words, unchanged

### 4.9 When a candle "reaches" a level: for a sell, high at least level - 3 pips and low at or below the level (buy mirrored)
- **Code:** `rejection/watch.py:224, 228`
  ```python
  224	                if direction == SELL and from_side and self._h(c) >= lv.price - near and self._l(c) <= lv.price:
  228	                if direction == BUY and from_side and self._l(c) <= lv.price + near and self._h(c) >= lv.price:
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Where the code needs a choice that section 3 does not make, do not invent one. List it for me, and use the simplest behaviour that adds no rule until I decide." (listed as a choice in strategies/bollinger_bounce/strategy.py lines 15-17; no owner decision on it found)
- **Mark:** Added without the owner asking

### 4.10 Any level in the bot's level list can start a setup
- **Code:** `rejection/watch.py:220`; `strategies/replay.py:170`
  ```python
  220	            for lv in levels.levels:
  strategies/replay.py:170	            events = self.watcher.on_candle(c, band, build(s, self.memo, c.start))
  ```
- **DESIGN.md:** line 150: "Price pierces a level or the Bollinger band."
- **Source:** agreed design (c803d53) line 139, "Price pierces a level or the Bollinger band."
- **Mark:** Owner's words, unchanged

### 4.11 No limit of one setup per direction: every pierce starts its own setup
- **Code:** `rejection/watch.py:199-208`
  ```python
  199	        for version in (BOUNCE, RANGE):
  200	            for direction in (SELL, BUY):
  201	                if not self.design_only and any(st.version == version and st.direction == direction
  202	                                                for st in self._active.values()):
  203	                    continue
  204	                pierced = self._pierced(version, direction, c, band, levels)
  ...
  207	                elif pierced:
  208	                    self._start(version, direction, c, pierced, levels)
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:10:22Z, PASTED, "Remove the limit of one setup per direction at a time."; owner, 2026-11-07T13:35:04Z, PASTED, "including any limit of one setup or pause per direction".
- **Mark:** Owner's words, unchanged

### 4.12 A fresh pierce does not restart a waiting setup's reversal count
- **Code:** `rejection/watch.py:291`
  ```python
  291	            again = [] if self.design_only else self._pierced(st.version, st.direction, c, band, levels)
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Remove every rule in the strategies that is not written in section 3". (Earlier, owner, 2026-11-07T13:10:22Z, PASTED, "keep ... the restart on a fresh pierce"; superseded by the 13:35 message; removal listed in commit 325c701.)
- **Mark:** Owner's words, unchanged

### 4.13 Reversal candle: the first red candle (close below open) after the pierce, no size rule, within 3 candles, else expired
- **Code:** `rejection/watch.py:118-119, 279-283, 298-302`
  ```python
  118	def _red(c: Candle, side: str) -> bool:
  119	    return getattr(c, f"{side}_close") < getattr(c, f"{side}_open")
  279	        if st.stage == "reversal":
  280	            limit = (self.s.bounce.reversal_candle_within_candles_of_pierce if st.version == BOUNCE
  282	            if turn(c, self.side):
  283	                st.reversal, st.stage, st.waited = c, ("confirmation" if st.version == BOUNCE else "trigger"), 0
  298	            st.waited += 1
  299	            if st.waited >= limit:
  300	                self._emit(st, EXPIRED, c.start, None,
  ```
  `config/settings.toml:181`: `reversal_candle_within_candles_of_pierce = 3`
- **DESIGN.md:** line 151: "The reversal candle is the first red candle after the pierce, with no size rule. If none appears within 3 candles, the setup expires."
- **Source:** agreed design (c803d53) line 140, same words; owner, 2026-11-06T15:05:45Z, PASTED, "bounce: reversal candle within 3 candles of the pierce".
- **Mark:** Owner's words, unchanged

### 4.14 Confirmation: a later candle closes below the reversal candle's low within 3 candles; a wick does not count
- **Code:** `rejection/watch.py:314-316, 322-328`
  ```python
  314	            if (self._c(c) < self._l(r)) if sell else (self._c(c) > self._h(r)):
  315	                st.confirmation, st.stage, st.waited = c, "trigger", 0
  316	                st.trigger_price = self._l(c) if sell else self._h(c)
  322	            st.waited += 1
  323	            limit = self.s.bounce.confirmation_candle_within_candles_of_reversal
  324	            if st.waited >= limit:
  ```
  `config/settings.toml:182`: `confirmation_candle_within_candles_of_reversal = 3`
- **DESIGN.md:** line 152: "A later confirmation candle closes below the reversal candle's low, within 3 candles of it, or the setup expires. A wick below without a close does not count."
- **Source:** agreed design (c803d53) line 141, same words; owner, 2026-11-06T15:05:45Z, PASTED, "confirmation candle within 3 candles of the reversal candle".
- **Mark:** Owner's words, unchanged

### 4.15 Trigger: the sell opens as soon as price goes below the confirmation candle's low (no time limit after confirmation)
- **Code:** `rejection/watch.py:334, 348-349, 395-399`
  ```python
  334	            through = self._l(c) < st.trigger_price if sell else self._h(c) > st.trigger_price
  348	            if through:
  349	                self._trigger(st, c.start, st.trigger_price, "during this candle", False)
  395	            if st.stage == "trigger":
  396	                tp = st.trigger_price if st.trigger_price is not None else (self._l(r) if sell else self._h(r))
  397	                st.trigger_price = tp
  398	                if (price < tp) if sell else (price > tp):
  399	                    self._trigger(st, t, price, f"live price {plain(price)}", True)
  ```
- **DESIGN.md:** line 153: "The sell opens as soon as the live price goes below the confirmation candle's low."
- **Source:** agreed design (c803d53) line 142, "The sell opens as soon as the live price goes below the confirmation candle's low."
- **Mark:** Owner's words, unchanged

### 4.16 Cancelled if price goes above the reversal candle's high at any point
- **Code:** `rejection/watch.py:306, 311-313, 345-347, 387-393`
  ```python
  306	        beyond_reversal = self._h(c) > self._h(r) if sell else self._l(c) < self._l(r)
  311	            if beyond_reversal:
  312	                self._cancel(st, c)
  313	                return
  387	            if ((price > self._h(r)) if sell else (price < self._l(r))) and not wide:
  ```
- **DESIGN.md:** line 154: "If price goes above the reversal candle's high at any point, the setup is cancelled."
- **Source:** agreed design (c803d53) line 143, same words.
- **Mark:** Owner's words, unchanged

### 4.17 One stored candle past both the trigger and the cancel price: a trigger only if it opened past the trigger, otherwise cancelled
- **Code:** `rejection/watch.py:335-344`
  ```python
  335	            if through and beyond_reversal:
  336	                # Both in one candle: from candles alone the order is unknown.
  337	                o = self._o(c)
  338	                first_through = (o < st.trigger_price) if sell else (o > st.trigger_price)
  339	                if first_through:
  340	                    self._trigger(st, c.start, st.trigger_price, "the candle opened past the trigger price", False)
  341	                else:
  342	                    self._cancel(st, c, "this candle went both ways; from candles alone the order is unknown, "
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "use the simplest behaviour that adds no rule until I decide" (listed as a choice in strategies/bollinger_bounce/strategy.py lines 21-23; no owner decision on it found)
- **Mark:** Added without the owner asking

### 4.18 Spread spikes: a candle whose spread is over the limit cannot start or cancel a setup (live price too)
- **Code:** `rejection/watch.py:163-174, 205-206, 307-309, 381, 387`
  ```python
  165	        return max(c.buy_open - c.sell_open, c.buy_high - c.sell_high,
  166	                   c.buy_low - c.sell_low, c.buy_close - c.sell_close)
  174	        return self.spread(c) > self.max_spread()
  205	                if pierced and self.spike(c):
  206	                    self._ignored(0, version, direction, c, "a new pierce")
  307	        if beyond_reversal and self.spike(c):
  308	            self._ignored(st.id, st.version, st.direction, c, "a cancel")
  381	        wide = spread is not None and spread > self.max_spread()
  387	            if ((price > self._h(r)) if sell else (price < self._l(r))) and not wide:
  ```
- **DESIGN.md:** line 167: "Spread spikes are ignored: when IG's spread on a candle is abnormally wide ... that candle's sell-price highs and lows cannot start a setup or cancel one."
- **Source:** owner, 2026-11-06T21:48:50Z, TYPED, "Decision on spread spikes: ignore them. When IG's spread on a candle is abnormally wide, that candle's sell-price highs and lows must not start a setup or cancel one."
- **Mark:** Owner's words, unchanged

### 4.19 The spread limit: 3 pips
- **Code:** `rejection/watch.py:168-169`
  ```python
  168	    def max_spread(self) -> Decimal:
  169	        return Decimal(self.s.rejection.max_spread_pips) * Decimal(self.s.market.points_per_pip)
  ```
  `config/settings.toml:420`: `max_spread_pips = 3`
- **DESIGN.md:** line 167: "(over 3 pips, a setting ...)"
- **Source:** owner, 2026-11-06T21:48:50Z, TYPED, "Make the spread limit a setting, choose a starting value from the real candles ... and tell me what you chose and why." (value chosen by the assistant; settings line 419 "STARTING VALUE"; no later owner acceptance of 3 found)
- **Mark:** Added without the owner asking

### 4.20 The reversal candle's size against the piercing candle is recorded, never a filter
- **Code:** `rejection/watch.py:267-272`; `strategies/bollinger_bounce/strategy.py:57-59`
  ```python
  271	        st.size = {"piercing_body": pb, "reversal_body": rb, "piercing_range": pr, "reversal_range": rr,
  272	                   "body_ratio": (rb / pb) if pb else None, "range_ratio": (rr / pr) if pr else None}
  strategies/bollinger_bounce/strategy.py:57	        if st.size and st.size.get("body_ratio") is not None:
  strategies/bollinger_bounce/strategy.py:58	            steps.append(f"recorded, not used: reversal/piercing candle body {st.size['body_ratio']:.2f}x, "
  ```
- **DESIGN.md:** line 165: "The bot records, for each bounce, how big the reversal candle was compared with the piercing candle, for later review. It never filters on it."
- **Source:** agreed design (c803d53) line 145, same words.
- **Mark:** Owner's words, unchanged

### 4.21 Reversal watch windows: 10:00, 11:00, 13:00, 14:00, 16:00, 17:00 UK, 20 minutes before to 20 minutes after
- **Code:** `rejection/watch.py:61-74`
  ```python
  64	    rw = settings.reversal_watch
  66	    for t in rw.times:
  67	        at = datetime.combine(day, t, tzinfo=UK).astimezone(UTC)
  68	        out.append((at - timedelta(minutes=rw.minutes_before), at + timedelta(minutes=rw.minutes_after)))
  ```
  `config/settings.toml:176-178`: `times = ["10:00", "11:00", "13:00", "14:00", "16:00", "17:00"]`, `minutes_before = 20`, `minutes_after = 20`
- **DESIGN.md:** line 216: "**Reversal watch times:** 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00 UK, from 20 minutes before to 20 minutes after."
- **Source:** owner, 2026-11-06T15:05:45Z, PASTED, "reversal watch times: 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00, from 20 minutes before to 20 minutes after each"; agreed design (c803d53) line 167.
- **Mark:** Owner's words, unchanged

### 4.22 The watch-window / lined-up "counts" mark does not filter bounce entries (recorded only)
- **Code:** `rejection/watch.py:254-256`; `strategies/bollinger_bounce/strategy.py:60-62`
  ```python
  254	        st.in_watch_window = in_watch_window(self.s, c.start)
  255	        has_band = any(p["level"] is None for p in pierced)
  256	        st.counts = has_band or st.in_watch_window or any(g["lined_up"] for g in st.lined_up)
  strategies/bollinger_bounce/strategy.py:60	        if version == "bounce":
  strategies/bollinger_bounce/strategy.py:61	            steps.append(f"reversal watch window: {'inside' if st.in_watch_window else 'outside'}; the setup "
  strategies/bollinger_bounce/strategy.py:62	                         f"{'counts' if st.counts else 'does not count'} (a mark for the trade manager, not a filter)")
  ```
- **DESIGN.md:** line 216: "In those windows a rejection at any level counts; outside them, only at levels where several line up." (section 4, trade management; 3.3 has no such rule)
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "The strategies must be exactly as specified in docs/DESIGN.md section 3, with no additions." (agreed design (c803d53) line 167 and owner, 2026-11-06T21:31:50Z, PASTED, "inside them any level counts, outside them only levels where several line up" describe the rejection part, written under trade management, not 3.3)
- **Mark:** Owner's words, unchanged

### 4.23 Stop loss 12 pips (STOP_LOSS_PIPS)
- **Code:** `strategies/common.py:257`
  ```python
  257	    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips
  ```
  `.env:27`: `STOP_LOSS_PIPS=12`
- **DESIGN.md:** line 207: "a fixed 12 pips for every strategy except ... that is the Bollinger bounce and the range trade ... (`STOP_LOSS_PIPS=12`)"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "Put changes 1, 2 and 3 live exactly as tested: the 12-pip stop for the bounce, range trade and breakout". (Agreed design (c803d53) line 162: "a fixed 6 pips for every strategy"; changed by the owner.)
- **Mark:** Owner's words, unchanged

### 4.24 Take profit 100 pips (TAKE_PROFIT_PIPS)
- **Code:** `strategies/common.py:230-231`
  ```python
  230	    if strategy not in (EMA_PULLBACK, SLOW_GRIND):
  231	        return settings.switches.take_profit_pips
  ```
  `.env:29`: `TAKE_PROFIT_PIPS=100`
- **DESIGN.md:** line 208: "a fixed 100 pips sent to IG as a safety net, for every strategy except the EMA pullback, the breakout and the slow grind."
- **Source:** agreed design (c803d53) line 163, "**Take profit:** a fixed 100 pips sent to IG as a safety net."
- **Mark:** Owner's words, unchanged

### 4.25 Half the trade closed at the opposite band
- **Code:** `trade_manager/manager.py:203-204`
  ```python
  203	    if strategy == BOLLINGER_BOUNCE:
  204	        return Decimal(settings.bounce.close_percent_at_opposite_band) / 100
  ```
  `config/settings.toml:186`: `close_percent_at_opposite_band = 50`
- **DESIGN.md:** line 156: "Half the trade closes when price reaches the opposite Bollinger band; the rest goes on to the bounce's normal exits"; line 219.
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "the bounce closed half at the opposite band with the rest left to its normal exits."
- **Mark:** Owner's words, unchanged

### 4.26 Closed on a confirmed rejection at a level against it
- **Code:** `strategies/common.py:47, 186-189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 214: "If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open"
- **Source:** agreed design (c803d53) line 165, "If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open".
- **Mark:** Owner's words, unchanged

### 4.27 Closed 15 minutes before big news
- **Code:** `strategies/common.py:180-183`
  ```python
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 264: "Open trades closed 15 minutes before."
- **Source:** agreed design (c803d53) line 200, "Open trades closed 15 minutes before."
- **Mark:** Owner's words, unchanged

### 4.28 New trades only from 06:00 to 20:30 UK and not in a big-news window
- **Code:** `strategies/common.py:150-158`
  ```python
  152	    if not (sw.new_trades_from <= lt < sw.new_trades_until):
  156	    windows = no_new_trades(settings, pair, t, calendar)
  157	    if windows:
  158	        reasons.append("in a big-news window: " + ", ".join(sorted({w.event for w in windows})))
  ```
  `.env:19-20`: `NEW_TRADES_FROM=06:00`, `NEW_TRADES_UNTIL=20:30`
- **DESIGN.md:** line 258: "new trades from 06:00 to 20:30"; line 264: "Big news: no new trades from 15 minutes before to 30 minutes after."
- **Source:** agreed design (c803d53) lines 199-200, "new trades from 06:00 to 20:30" / "no new trades from 15 minutes before to 30 minutes after".
- **Mark:** Owner's words, unchanged

### 4.29 Closed at 20:30 UK every day
- **Code:** `strategies/common.py:174-176`
  ```python
  174	        cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 258: "Any trade open at 20:30 is closed. Nothing held overnight."
- **Source:** agreed design (c803d53) line 199, "Any trade open at 20:30 is closed. Nothing held overnight."
- **Mark:** Owner's words, unchanged

### 4.30 Pace and target: applies only to a bounce while trend trades (EMA pullback, slow grind, breakout) are open in the other direction
- **Code:** `trading/against_trend.py:35, 65-67, 108-112`; `trading/engine.py:232-233`
  ```python
  35	TREND_STRATEGIES = (SLOW_GRIND, EMA_PULLBACK, BREAKOUT)
  67	    return [t for t in trades if t.open and t.direction != direction and t.strategy in TREND_STRATEGIES]
  108	    if idea.strategy != BOLLINGER_BOUNCE:
  109	        return None
  110	    opp = trend_trades_against(trades, idea.direction)
  111	    if not opp:
  112	        return None
  ```
- **DESIGN.md:** line 160: "While the bot has open trend trades (EMA pullback, slow grind, breakout), no bounce may open against them unless ..."; line 163 "A bounce with no open trend trade against it is not affected."
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "While the bot has open trend trades (EMA pullback, slow grind, breakout), no Bollinger bounce may open against them, unless ..."
- **Mark:** Owner's words, unchanged

### 4.31 Significant levels: a 00, the weekly pivot, S2, S3, R2, R3
- **Code:** `trading/against_trend.py:36, 81-84, 90-92`
  ```python
  36	LEVEL_TYPES = ("S2", "S3", "R2", "R3")
  82	    hundred = 100 * ppp
  83	    lo = (price / hundred).to_integral_value(ROUND_FLOOR) * hundred
  84	    out = [("00", lo), ("00", lo + hundred)]
  90	    for lv in build(settings, store, t).levels:
  91	        if lv.type in LEVEL_TYPES:
  ```
- **DESIGN.md:** line 160: "a 00, the weekly pivot ..., S2, S3, R2 or R3"
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "a significant level in their direction: a 00, the weekly pivot (from the previous week's candle), S2, S3, R2 or R3"
- **Mark:** Owner's words, unchanged

### 4.32 Weekly pivot: (high + low + close) / 3 of the last finished weekly candle (week starting Sunday), sell price, to a tenth
- **Code:** `trading/against_trend.py:85-89`
  ```python
  85	    wk = [c for c in store.read_range("1w", t - timedelta(days=21), t) if c.end <= t]
  86	    if wk:
  87	        w = wk[-1]
  88	        out.append(("weekly pivot", ((Decimal(w.sell_high) + Decimal(w.sell_low) + Decimal(w.sell_close)) / 3)
  89	                    .quantize(Decimal("0.1"))))
  ```
  `config/settings.toml:486`: `week_starts_day = "Sunday"`
- **DESIGN.md:** line 160: "the weekly pivot (the standard one from the previous week's candle, (high + low + close) ÷ 3)"
- **Source:** owner, 2026-11-11T11:51:55Z, TYPED, "use whichever matches the standard weekly pivot from the previous Monday-to-Friday week."; owner, 2026-11-11T16:53:52Z, PASTED, "the weekly pivot (from the previous week's candle)".
- **Mark:** Changed from the owner's words  **Owner:** "the standard weekly pivot from the previous Monday-to-Friday week" / **Code:** uses the stored weekly candle that starts on Sunday (settings line 486), so the prices from the Sunday 21:00 UK open are included.

### 4.33 "In their direction": beyond the price at least one of the open trend trades opened at
- **Code:** `trading/against_trend.py:118-119`
  ```python
  118	    fills = [Decimal(x.fill) for x in opp]
  119	    ahead = [(n, p) for n, p in levels_at(settings, store, ext, t) if (p < max(fills) if buy else p > min(fills))]
  ```
- **DESIGN.md:** line 160: "\"In their direction\" means beyond the price at least one of those trades opened at."
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "a significant level in their direction" (no owner words define it; the definition is from docs/research/pace_and_target_20261111.md, which the owner asked to be built "exactly as tested").
- **Mark:** Added without the owner asking

### 4.34 The high or low the bounce turned from: the extreme of its setup candles, pierce to confirmation
- **Code:** `strategies/bollinger_bounce/strategy.py:40-43`; `trading/against_trend.py:70-76`
  ```python
  40	    last = setup.confirmation or setup.reversal or setup.pierce
  41	    own = [c for c in (setup.pierce, setup.reversal, setup.confirmation) if c is not None]
  42	    return {"setup_from": setup.pierce.start, "setup_last": last.start,
  43	            "setup_high": max(Decimal(c.sell_high) for c in own), "setup_low": min(Decimal(c.sell_low) for c in own)}
  trading/against_trend.py:75	    prices = [Decimal(c.sell_low if buy else c.sell_high) for c in cs] + [ctx["setup_low" if buy else "setup_high"]]
  trading/against_trend.py:76	    return min(prices) if buy else max(prices)
  ```
- **DESIGN.md:** line 163: "the high or low is the extreme of the setup's candles from the pierce to the confirmation"
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "with the high or low the bounce turned from within 5 pips of it" (the span pierce-to-confirmation is not in the owner's words).
- **Mark:** Added without the owner asking

### 4.35 At the level: within 5 pips
- **Code:** `trading/against_trend.py:121-122, 125-126`
  ```python
  121	    within = Decimal(str(b.against_trend_level_within_pips))
  122	    hits = [x for x in near if x[0] <= within]
  125	    if not hits:
  126	        return Verdict(False, NOT_AT_LEVEL, against, ext, None, shown, rate)
  ```
  `config/settings.toml:194`: `against_trend_level_within_pips = 5`
- **DESIGN.md:** line 160: "within 5 pips of it (`bounce.against_trend_level_within_pips`)"
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "within 5 pips of it ... Make the 5 pips, the 5 pips an hour and the 2 hours settings."
- **Mark:** Owner's words, unchanged

### 4.36 Pace: under 5 pips an hour over the last 2 hours (net close-to-close move / 2, finished candles, at the start of the bounce's candle)
- **Code:** `trading/against_trend.py:96-102, 124, 130-131`
  ```python
  98	    fin = [c for c in store.read_range("5m", t - timedelta(hours=2 * hours), t) if c.end <= t]
  99	    before = [c for c in fin if c.end <= t - timedelta(hours=hours)]
  102	    return abs(Decimal(fin[-1].sell_close) - Decimal(before[-1].sell_close)) / ppp / hours
  124	    rate = pips_per_hour(settings, store, t, b.against_trend_pace_hours)
  130	    if rate >= Decimal(str(b.against_trend_max_pips_per_hour)):
  131	        return Verdict(False, TOO_FAST, against, ext, level, shown, rate)
  ```
  `config/settings.toml:195-196`: `against_trend_max_pips_per_hour = 5`, `against_trend_pace_hours = 2`
- **DESIGN.md:** line 161: "valid only if price has moved under 5 pips an hour on average over the last 2 hours ... the net move from the close 2 hours earlier to the last close, divided by 2."
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "the bounce is valid only if price has moved under 5 pips an hour on average over the last 2 hours."
- **Mark:** Owner's words, unchanged

### 4.37 Pace cannot be read (no candle 2 hours earlier): the bounce is refused
- **Code:** `trading/against_trend.py:100-101, 128-129`
  ```python
  100	    if not fin or not before:
  101	        return None
  128	    if rate is None:
  129	        return Verdict(False, PACE_UNKNOWN, against, ext, level, shown, rate)
  ```
- **DESIGN.md:** line 163: "with no candle 2 hours earlier (after a gap or the weekend) it cannot be read and the bounce is refused."
- **Source:** none found in the owner's words.
- **Mark:** Added without the owner asking

### 4.38 A valid bounce closes every trade open in the opposite direction, whatever its strategy; an invalid one is refused
- **Code:** `trading/engine.py:202-204, 210-211, 249-251`
  ```python
  202	        verdict = self._against_trend(idea, candle.start)
  203	        if verdict is not None and not verdict.valid:
  204	            return
  210	        if verdict is not None:
  211	            self._close_against(idea, r, opened_at, verdict)
  249	        for mt in list(self.manager.trades.values()):
  250	            if mt.open and mt.direction != idea.direction and mt.reference != r.reference:
  251	                self.manager.close_now(mt.reference, price, why, opened_at)
  ```
- **DESIGN.md:** line 161: "It then opens, and **closes every trade open in the opposite direction at that moment**, whatever its strategy, in profit or not. Otherwise it is refused and the trend trades are held."
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "Then it opens, and closes every open trade in the opposite direction at that moment. Otherwise it is refused and the trend trades are held."
- **Mark:** Owner's words, unchanged

### 4.39 Those closes are priced like the bounce's entry (sell price for a bounce sell, buy fill for a bounce buy)
- **Code:** `trading/engine.py:245-246`
  ```python
  245	        fill = self.sender.trades[r.reference].level
  246	        price = idea.entry_price if idea.direction == "sell" else fill
  ```
- **DESIGN.md:** line 163: "The closes are priced like the bounce's own entry"
- **Source:** none found in the owner's words.
- **Mark:** Added without the owner asking

### 4.40 Bounce setups triggering the same way in the same candle are one bounce, judged by the first
- **Code:** `strategies/bollinger_bounce/strategy.py:51, 63`
  ```python
  51	    first: dict = {}
  63	        ctx = dict(first.setdefault((e.time, e.direction), setup_context(st))) if version == "bounce" else {}
  ```
- **DESIGN.md:** line 163: "Bounce setups that trigger the same way in the same candle are one bounce, judged by the first"
- **Source:** none found in the owner's words (code comment line 49: "as tested in docs/research/pace_and_target_20261111.md").
- **Mark:** Added without the owner asking

### 4.41 If the rule cannot be checked (an error), the bounce is refused
- **Code:** `trading/engine.py:222-231`
  ```python
  222	        try:
  223	            v = check(self.s, self.store, idea, candle_start, list(self.manager.trades.values()))
  224	        except Exception as e:                              # noqa: BLE001  (never open it unchecked)
  ...
  230	            v = Verdict(False, f"the rule could not be checked ({e})", [f"{x.strategy} {x.direction} {x.reference}"
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

## 5. Range trade

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 19 | 0 | 3 | 0 | 22 |

### 5.1 Every price the watcher reads is the sell (chart) price
- **Code:** `rejection/watch.py:139,146-149`
  ```python
  139	        self.side = settings.chart.price
  146	    def _o(self, c): return getattr(c, f"{self.side}_open")
  147	    def _h(self, c): return getattr(c, f"{self.side}_high")
  148	    def _l(self, c): return getattr(c, f"{self.side}_low")
  ```
  `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** line 116: "Every indicator, for the analyser and the strategies, is worked out from the sell (bid) price"
- **Source:** owner, 2026-11-06T21:22:13Z, PASTED, "My IG chart is set to the sell (bid) price, so the design was wrong to say levels use the buy price. Change the levels, and every indicator worked out for the analyser and strategies, to use the sell (bid) price"; owner, 2026-11-06T21:31:50Z, PASTED, "Stage 6: the shared rejection part ... Use the sell (bid) price, like the levels." (agreed design (c803d53) line 180 had "All levels use the buy (OFR) price"; the owner's later words replace it.)
- **Mark:** Owner's words, unchanged

### 5.2 A candle pierces the upper Bollinger band (a real pierce: high above the band)
- **Code:** `rejection/watch.py:213-217`
  ```python
  213	        if band is not None:
  214	            if direction == SELL and self._h(c) > band.upper:
  215	                out.append({"what": "upper Bollinger band", "price": band.upper, "level": None})
  216	            if direction == BUY and self._l(c) < band.lower:
  217	                out.append({"what": "lower Bollinger band", "price": band.lower, "level": None})
  ```
- **DESIGN.md:** line 171: "1. One candle pierces the upper Bollinger band."
- **Source:** agreed design (c803d53) line 149, "1. One candle pierces the upper Bollinger band."; owner, 2026-11-06T21:42:54Z, TYPED, "the Bollinger band still needs a real pierce."
- **Mark:** Owner's words, unchanged

### 5.3 Every pierce starts its own setup (no limit of one setup per version and direction; design_only watcher)
- **Code:** `rejection/watch.py:199-203`
  ```python
  199	        for version in (BOUNCE, RANGE):
  200	            for direction in (SELL, BUY):
  201	                if not self.design_only and any(st.version == version and st.direction == direction
  202	                                                for st in self._active.values()):
  203	                    continue
  ```
- **DESIGN.md:** none (3.4 lines 171-174 have no limit)
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Remove every rule in the strategies that is not written in section 3, including any limit of one setup or pause per direction."
- **Mark:** Owner's words, unchanged

### 5.4 The next candle must be red: the rejection candle (else expired); limit 1 candle
- **Code:** `rejection/watch.py:279-283,298-302`
  ```python
  279	        if st.stage == "reversal":
  280	            limit = (self.s.bounce.reversal_candle_within_candles_of_pierce if st.version == BOUNCE
  281	                     else self.s.range_trade.rejection_candle_within_candles)
  282	            if turn(c, self.side):
  283	                st.reversal, st.stage, st.waited = c, ("confirmation" if st.version == BOUNCE else "trigger"), 0
  298	            st.waited += 1
  299	            if st.waited >= limit:
  300	                self._emit(st, EXPIRED, c.start, None,
  ```
  `rejection/watch.py:118-119`: `def _red(c, side): return getattr(c, f"{side}_close") < getattr(c, f"{side}_open")`
  `config/settings.toml:282`: `rejection_candle_within_candles = 1`
- **DESIGN.md:** line 172: "2. The next candle is a red rejection candle."
- **Source:** agreed design (c803d53) line 150, "2. The next candle is a red rejection candle."
- **Mark:** Owner's words, unchanged

### 5.5 Trigger: during the candle after the rejection candle, price goes below the rejection candle's low (live price; else expired); limit 1 candle
- **Code:** `rejection/watch.py:331-334,348-357,395-399`
  ```python
  331	        if st.stage == "trigger":
  332	            if st.version == RANGE and st.trigger_price is None:
  333	                st.trigger_price = self._l(r) if sell else self._h(r)
  334	            through = self._l(c) < st.trigger_price if sell else self._h(c) > st.trigger_price
  348	            if through:
  349	                self._trigger(st, c.start, st.trigger_price, "during this candle", False)
  351	            if st.version == RANGE:
  352	                st.waited += 1
  353	                if st.waited >= self.s.range_trade.trigger_within_candles:
  395	            if st.stage == "trigger":
  396	                tp = st.trigger_price if st.trigger_price is not None else (self._l(r) if sell else self._h(r))
  398	                if (price < tp) if sell else (price > tp):
  399	                    self._trigger(st, t, price, f"live price {plain(price)}", True)
  ```
  `config/settings.toml:284`: `trigger_within_candles = 1`
- **DESIGN.md:** line 173: "3. The sell opens as soon as the live price, during the candle after that, goes below the rejection candle's low."
- **Source:** agreed design (c803d53) line 151, "3. The sell opens as soon as the live price, during the candle after that, goes below the rejection candle's low."
- **Mark:** Owner's words, unchanged

### 5.6 Cancelled if price goes above the rejection candle's high first (finished candle or live price)
- **Code:** `rejection/watch.py:305-306,345-347,387-393`
  ```python
  305	        r = st.reversal
  306	        beyond_reversal = self._h(c) > self._h(r) if sell else self._l(c) < self._l(r)
  345	            if beyond_reversal:
  346	                self._cancel(st, c)
  387	            if ((price > self._h(r)) if sell else (price < self._l(r))) and not wide:
  393	                self._end(st, "cancelled")
  ```
- **DESIGN.md:** line 174: "4. If price goes above the rejection candle's high first, the setup is cancelled."
- **Source:** agreed design (c803d53) line 152, "4. If price goes above the rejection candle's high first, the setup is cancelled."
- **Mark:** Owner's words, unchanged

### 5.7 A candle that goes both past the trigger and past the cancel price: a trigger only if it opened past the trigger price, otherwise cancelled
- **Code:** `rejection/watch.py:335-344`
  ```python
  335	            if through and beyond_reversal:
  336	                # Both in one candle: from candles alone the order is unknown.
  337	                o = self._o(c)
  338	                first_through = (o < st.trigger_price) if sell else (o > st.trigger_price)
  339	                if first_through:
  340	                    self._trigger(st, c.start, st.trigger_price, "the candle opened past the trigger price", False)
  341	                else:
  342	                    self._cancel(st, c, "this candle went both ways; from candles alone the order is unknown, "
  ```
- **DESIGN.md:** none
- **Source:** none found from the owner; first written in commit 4f7b4e0 (2026-11-06 21:53, "Stage 6: the shared rejection part"); listed for the owner as a choice in `strategies/range_trade/strategy.py:9-11` ("Choices section 3.4 does not make (listed for the owner) ... a candle going both past the trigger and the cancel price counts as a trigger only if it opened past the trigger price"). Owner, 2026-11-07T13:35:04Z, PASTED, asked "List it for me, and use the simplest behaviour that adds no rule until I decide"; no later decision found.
- **Mark:** Added without the owner asking

### 5.8 Spread spikes ignored: a wide-spread candle cannot start a setup or cancel one; a live price with a wide spread cannot cancel
- **Code:** `rejection/watch.py:205-206,307-309,381,387`
  ```python
  205	                if pierced and self.spike(c):
  206	                    self._ignored(0, version, direction, c, "a new pierce")
  307	        if beyond_reversal and self.spike(c):
  308	            self._ignored(st.id, st.version, st.direction, c, "a cancel")
  309	            beyond_reversal = False
  381	        wide = spread is not None and spread > self.max_spread()
  387	            if ((price > self._h(r)) if sell else (price < self._l(r))) and not wide:
  ```
- **DESIGN.md:** line 178: "Spread spikes are ignored in the same way as for the bounce (3.3)."; line 167: "that candle's sell-price highs and lows cannot start a setup or cancel one."
- **Source:** owner, 2026-11-06T21:48:50Z, TYPED, "Decision on spread spikes: ignore them. When IG's spread on a candle is abnormally wide, that candle's sell-price highs and lows must not start a setup or cancel one."
- **Mark:** Owner's words, unchanged

### 5.9 The spread-spike limit: 3 pips
- **Code:** `rejection/watch.py:168-174`
  ```python
  168	    def max_spread(self) -> Decimal:
  169	        return Decimal(self.s.rejection.max_spread_pips) * Decimal(self.s.market.points_per_pip)
  174	        return self.spread(c) > self.max_spread()
  ```
  `config/settings.toml:420`: `max_spread_pips = 3`
- **DESIGN.md:** line 167: "(over 3 pips, a setting; this happens at the 22:00 rollover and at news)"
- **Source:** owner, 2026-11-06T21:48:50Z, TYPED, "Make the spread limit a setting, choose a starting value from the real candles ... and tell me what you chose and why." The value 3 was chosen by the assistant (commit 4f7b4e0; settings comment "STARTING VALUE"); no owner message accepting 3 found.
- **Mark:** Added without the owner asking

### 5.10 How a candle's spread is measured: the widest of its four buy-minus-sell gaps (open, high, low, close)
- **Code:** `rejection/watch.py:163-166`
  ```python
  163	    def spread(self, c: Candle) -> Decimal:
  164	        """The candle's spread: the widest of its four buy-minus-sell gaps (open, high, low, close)."""
  165	        return max(c.buy_open - c.sell_open, c.buy_high - c.sell_high,
  166	                   c.buy_low - c.sell_low, c.buy_close - c.sell_close)
  ```
- **DESIGN.md:** none
- **Source:** none found from the owner (owner, 2026-11-06T21:48:50Z, TYPED, says only "When IG's spread on a candle is abnormally wide"); written in commit 4f7b4e0.
- **Mark:** Added without the owner asking

### 5.11 A buy is the mirror image at the lower band (pierce down, green rejection candle, trigger above its high, cancel below its low)
- **Code:** `rejection/watch.py:216-217,278,333,306`
  ```python
  216	            if direction == BUY and self._l(c) < band.lower:
  278	        turn = _red if sell else _green
  333	                st.trigger_price = self._l(r) if sell else self._h(r)
  306	        beyond_reversal = self._h(c) > self._h(r) if sell else self._l(c) < self._l(r)
  ```
- **DESIGN.md:** line 122: "All rules below are written for one direction; the other is the mirror image."
- **Source:** agreed design (c803d53) line 115, "All rules below are written for one direction; the other is the mirror image."
- **Mark:** Owner's words, unchanged

### 5.12 Allowed only in the ranging state, either direction
- **Code:** `strategies/common.py:57,278-280`
  ```python
  57	    RANGE_TRADE: {RANGING: "any"},
  278	    ok_in = ALLOWED_IN[strategy]
  279	    if state.state not in ok_in:
  280	        reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
  ```
- **DESIGN.md:** line 42: "| Ranging | Range trade; level reversal (3.6), either way |"
- **Source:** agreed design (c803d53) line 40, "| Ranging | Range trade |" (owner, 2026-11-07T14:57:26Z, TYPED, "Rerun ... with the range trade allowed in every state except consolidation" was a rerun only; no change asked.)
- **Mark:** Owner's words, unchanged

### 5.13 The direction rule does not apply to the range trade
- **Code:** `strategies/common.py:49,289-290`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  290	        reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
  ```
- **DESIGN.md:** line 54: "### 2.3 Direction rule (applies to every strategy except the range trade, ...)"
- **Source:** owner, 2026-11-07T14:41:12Z, TYPED, "the direction rule applies to every strategy except the range trade"
- **Mark:** Owner's words, unchanged

### 5.14 Its .env switch (STRATEGY_RANGE_TRADE, on)
- **Code:** `strategies/common.py:276-277`
  ```python
  276	    if not getattr(settings.switches, SWITCH[strategy]):
  277	        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
  ```
  `.env`: `STRATEGY_RANGE_TRADE=on`
- **DESIGN.md:** line 361: "each strategy on or off (... `STRATEGY_RANGE_TRADE` ...)"
- **Source:** owner, 2026-11-07T07:53:05Z, PASTED, "Move these into .env ... each strategy on or off (slow grind, EMA pullback, Bollinger bounce, range trade) ... tell me exactly which lines I need to add to it myself." (the owner writes his .env himself); agreed design (c803d53) line 18 lists the range trade among the strategies.
- **Mark:** Owner's words, unchanged

### 5.15 Stop loss 12 pips (STOP_LOSS_PIPS)
- **Code:** `strategies/common.py:250,257`
  ```python
  250	    sw = settings.switches
  257	    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips
  ```
  `.env`: `STOP_LOSS_PIPS=12`
- **DESIGN.md:** line 207: "a fixed 12 pips for every strategy except ... that is the Bollinger bounce and the range trade"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "Put changes 1, 2 and 3 live exactly as tested: the 12-pip stop for the bounce, range trade and breakout"
- **Mark:** Owner's words, unchanged

### 5.16 Take profit 100 pips (TAKE_PROFIT_PIPS)
- **Code:** `strategies/common.py:230-231`
  ```python
  230	    if strategy not in (EMA_PULLBACK, SLOW_GRIND):
  231	        return settings.switches.take_profit_pips
  ```
  `.env`: `TAKE_PROFIT_PIPS=100`
- **DESIGN.md:** line 208: "a fixed 100 pips sent to IG as a safety net, for every strategy except the EMA pullback, the breakout and the slow grind"
- **Source:** agreed design (c803d53) line 163, "Take profit: a fixed 100 pips sent to IG as a safety net. A setting."
- **Mark:** Owner's words, unchanged

### 5.17 New trades only from 06:00 to 20:30 UK
- **Code:** `strategies/common.py:150-153`
  ```python
  150	    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
  151	    sw = settings.switches
  152	    if not (sw.new_trades_from <= lt < sw.new_trades_until):
  153	        reasons.append(f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK")
  ```
  `.env`: `NEW_TRADES_FROM=06:00`, `NEW_TRADES_UNTIL=20:30`
- **DESIGN.md:** line 258: "new trades from 06:00 to 20:30"
- **Source:** agreed design (c803d53) line 199, "Trading hours (UK clock time): new trades from 06:00 to 20:30."
- **Mark:** Owner's words, unchanged

### 5.18 No new trade in a big-news window
- **Code:** `strategies/common.py:156-158`
  ```python
  156	    windows = no_new_trades(settings, pair, t, calendar)
  157	    if windows:
  158	        reasons.append("in a big-news window: " + ", ".join(sorted({w.event for w in windows})))
  ```
- **DESIGN.md:** line 264: "Big news: no new trades from 15 minutes before to 30 minutes after."
- **Source:** agreed design (c803d53) line 200, "Big news: no new trades from 15 minutes before to 30 minutes after."
- **Mark:** Owner's words, unchanged

### 5.19 Closed at 20:30 UK every day
- **Code:** `strategies/common.py:43,172-176`
  ```python
  43	OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
  172	    for k in range(0, 8):
  173	        day = lt.date() + timedelta(days=k)
  174	        cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 258: "Any trade open at 20:30 is closed. Nothing held overnight."
- **Source:** agreed design (c803d53) line 199, "Any trade open at 20:30 is closed. Nothing held overnight."
- **Mark:** Owner's words, unchanged

### 5.20 Closed 15 minutes before big news
- **Code:** `strategies/common.py:45,180-183`
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  180	def closed_before_big_news(strategy: str) -> bool:
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 264: "Open trades closed 15 minutes before."
- **Source:** agreed design (c803d53) line 200, "Open trades closed 15 minutes before."
- **Mark:** Owner's words, unchanged

### 5.21 Closed on a confirmed rejection at a level against the trade
- **Code:** `strategies/common.py:47,186-189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  186	def closed_on_level_rejection(strategy: str) -> bool:
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 214: "If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open"
- **Source:** agreed design (c803d53) line 165, "If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open"
- **Mark:** Owner's words, unchanged

### 5.22 Closed in full (100%) when price reaches the opposite Bollinger band
- **Code:** `trade_manager/manager.py:197-202,261-262`
  ```python
  197	def band_close_share(settings: Any, strategy: str) -> Decimal:
  201	    if strategy == RANGE_TRADE:
  202	        return Decimal(settings.range_trade.close_percent_at_opposite_band) / 100
  261	            if t.band_close >= 1:
  262	                return finish(CLOSE, price, "the opposite Bollinger band")
  ```
  `config/settings.toml:279`: `close_percent_at_opposite_band = 100`
- **DESIGN.md:** line 176: "The whole trade closes when price reaches the other band (owner, 11 November 2026 ...; `range_trade.close_percent_at_opposite_band` 100)."
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "the range trade closed in full at the opposite band" (agreed design (c803d53) line 154 had "Half the trade closes when price reaches the other band."; the owner's later words replace it.)
- **Mark:** Owner's words, unchanged

## 6. Level reversal

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 15 | 1 | 5 | 0 | 21 |

### 6.1 Its .env switch (STRATEGY_LEVEL_REVERSAL, on)
- **Code:** `strategies/common.py:276-277`
  ```python
  276	    if not getattr(settings.switches, SWITCH[strategy]):
  277	        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
  ```
  `.env`: `STRATEGY_LEVEL_REVERSAL=on`
- **DESIGN.md:** line 191: "**Switched on** (`STRATEGY_LEVEL_REVERSAL=on`)."
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Owner decision: add a new strategy, the level reversal, switched on ... give it its own settings and .env switch STRATEGY_LEVEL_REVERSAL"
- **Mark:** Owner's words, unchanged

### 6.2 Setups come from the shared rejection part's bounce version: pierce, first red reversal candle within 3, a close below its low within 3, cancelled above its high, spread spikes ignored (5.8)
- **Code:** `strategies/level_reversal/strategy.py:73-76`
  ```python
  73	        for e in events:
  74	            if e.version != "bounce" or e.kind != "trigger" or (e.time, e.direction) in seen:
  75	                continue
  76	            cand = self._candidate(watcher, e)
  ```
  `rejection/watch.py:280,314-316,323`
  ```python
  280	            limit = (self.s.bounce.reversal_candle_within_candles_of_pierce if st.version == BOUNCE
  314	            if (self._c(c) < self._l(r)) if sell else (self._c(c) > self._h(r)):
  316	                st.trigger_price = self._l(c) if sell else self._h(c)
  323	            limit = self.s.bounce.confirmation_candle_within_candles_of_reversal
  ```
  `config/settings.toml:181-182`: `reversal_candle_within_candles_of_pierce = 3`, `confirmation_candle_within_candles_of_reversal = 3`
- **DESIGN.md:** line 193: "found by the shared rejection part exactly as for the Bollinger band bounce (3.3 steps 1 to 3 and 5)"
- **Source:** owner, 2026-11-08T05:21:30Z, PASTED, "Level reversal: ... when price arrives at the level and a rejection confirms there"; owner, 2026-11-08T05:48:07Z, PASTED, "Entry when price breaks past the confirmation candle, as in the research."; agreed design (c803d53) lines 140-143, "If none appears within 3 candles, the setup expires ... within 3 candles of it, or the setup expires ... If price goes above the reversal candle's high at any point, the setup is cancelled."
- **Mark:** Owner's words, unchanged

### 6.3 A level counts as reached when the candle comes within 3 pips of it, from either side (design_only: no rule about the side the candle opened on)
- **Code:** `rejection/watch.py:219,223-224`
  ```python
  219	            near = Decimal(self.s.rejection.near_level_within_pips) * Decimal(self.s.market.points_per_pip)
  223	                from_side = self.design_only or (self._o(c) <= lv.price if direction == SELL else self._o(c) >= lv.price)
  224	                if direction == SELL and from_side and self._h(c) >= lv.price - near and self._l(c) <= lv.price:
  ```
  `config/settings.toml:415`: `near_level_within_pips = 3`
- **DESIGN.md:** line 193: "price reaches the level or comes within 3 pips of it"; line 240: "A candle that comes within 3 pips of a level counts the same as a pierce of that level"
- **Source:** owner, 2026-11-06T21:42:54Z, TYPED, "a candle that comes within 3 pips of a level counts the same as a pierce of that level. Make the 3 pips a setting."; owner, 2026-11-07T13:35:04Z, PASTED, "Remove every rule in the strategies that is not written in section 3" (the earlier owner, 2026-11-07T13:10:22Z, PASTED, "Bounce: keep the near-side rule for levels" was followed by this).
- **Mark:** Owner's words, unchanged

### 6.4 The candle must also reach down to the level (sell: its low at or below the level; buy: its high at or above it), so a candle wholly beyond the level does not count
- **Code:** `rejection/watch.py:224,228`
  ```python
  224	                if direction == SELL and from_side and self._h(c) >= lv.price - near and self._l(c) <= lv.price:
  228	                if direction == BUY and from_side and self._l(c) <= lv.price + near and self._h(c) >= lv.price:
  ```
- **DESIGN.md:** none
- **Source:** none found from the owner; present since commit 4f7b4e0 (2026-11-06 21:53, "Stage 6: the shared rejection part").
- **Mark:** Added without the owner asking

### 6.5 Only S2, R2 and round numbers
- **Code:** `strategies/level_reversal/strategy.py:53-56`
  ```python
  53	    def kind(self, what: str, price: Decimal) -> str | None:
  55	        if what not in self.lr.level_types:
  56	            return None
  ```
  `config/settings.toml:263`: `level_types = ["S2", "R2", "round_number"]`
- **DESIGN.md:** line 193: "Only rejections at **round numbers ending in 00** (not 50), **S2** and **R2**"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "It trades rejections at round 00 numbers, S2 and R2 only"; owner, 2026-11-08T06:05:31Z, TYPED, "Keep S2 in the level types."
- **Mark:** Owner's words, unchanged

### 6.6 Round numbers only on a multiple of 100 pips (the 00s, not the 50s)
- **Code:** `strategies/level_reversal/strategy.py:57-60`
  ```python
  57	        if what == ROUND_NUMBER:
  58	            pips = price / self.ppp
  59	            if pips % self.lr.round_numbers_every_pips != 0:
  60	                return None
  ```
  `config/settings.toml:264`: `round_numbers_every_pips = 100`
- **DESIGN.md:** line 193: "round numbers ending in 00 (not 50)"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "round 00 numbers"
- **Mark:** Owner's words, unchanged

### 6.7 The allowance past the level: 12 pips at R2 and S2, 5 pips at round numbers
- **Code:** `strategies/level_reversal/strategy.py:64-66,96-99`
  ```python
  66	        return getattr(self.lr, f"allowance_pips_{what.lower()}")
  96	            past = (furthest - p["price"]) if sell else (p["price"] - furthest)
  97	            allowance = self.allowance(p["what"])
  98	            if past > Decimal(allowance) * self.ppp:
  99	                continue
  ```
  `config/settings.toml:268-270`: `allowance_pips_r2 = 12`, `allowance_pips_s2 = 12`, `allowance_pips_round_number = 5`
- **DESIGN.md:** line 194: "**12 pips at R2 and S2, 5 pips at round numbers**"
- **Source:** owner, 2026-11-08T06:05:31Z, TYPED, "the level reversal's allowance past the level is 12 pips at R2 and S2, and stays 5 pips at round 00s. ... Make each allowance its own setting"
- **Mark:** Owner's words, unchanged

### 6.8 "Furthest point" measured over the candles from the piercing candle to the confirmation candle
- **Code:** `strategies/level_reversal/strategy.py:87-90`
  ```python
  87	        span = [c for c in self.candles if st.pierce.start <= c.start <= st.confirmation.start]
  88	        if not span:
  89	            return None
  90	        furthest = max(self._h(c) for c in span) if sell else min(self._l(c) for c in span)
  ```
- **DESIGN.md:** line 194: "measured as the furthest price reached from the piercing candle to the confirmation candle."
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Stop 6 pips beyond the furthest point price reached" and "A rejection counts when price reverses within 5 pips past the level" (no span given); the span was written by the assistant in commit 45628cc (2026-11-08 05:58).
- **Mark:** Added without the owner asking

### 6.9 If several of these levels were reached, the first that passes the allowance is the level, S2 and R2 before round numbers
- **Code:** `strategies/level_reversal/strategy.py:91-95`
  ```python
  91	        order = sorted(st.pierced, key=lambda p: p["what"] == ROUND_NUMBER)      # S2 and R2 first
  92	        for p in order:
  93	            name = self.kind(p["what"], p["price"])
  94	            if name is None:
  95	                continue
  ```
- **DESIGN.md:** line 199: "the first that passes rule 2 is the level (S2 and R2 before round numbers)"
- **Source:** none from the owner; listed as "Choices the owner's rules do not make" in `strategies/level_reversal/strategy.py:21-24`; commit 45628cc.
- **Mark:** Added without the owner asking

### 6.10 Entry as soon as price breaks below the confirmation candle's low (buy: above its high), on the live price
- **Code:** `rejection/watch.py:316,395-399`
  ```python
  316	                st.trigger_price = self._l(c) if sell else self._h(c)
  395	            if st.stage == "trigger":
  398	                if (price < tp) if sell else (price > tp):
  399	                    self._trigger(st, t, price, f"live price {plain(price)}", True)
  ```
  `strategies/level_reversal/strategy.py:110`: `return Candidate(LEVEL_REVERSAL, SELL if sell else BUY, e.time, e.price, steps,`
- **DESIGN.md:** line 195: "3. The sell opens as soon as price breaks below the confirmation candle's low (a buy, above its high)."
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Entry when price breaks past the confirmation candle, as in the research."
- **Mark:** Owner's words, unchanged

### 6.11 Stop 6 pips beyond the furthest point
- **Code:** `strategies/level_reversal/strategy.py:100-101`; `strategies/common.py:251-252,265-267`
  ```python
  100	            beyond = Decimal(self.lr.stop_beyond_furthest_pips) * self.ppp
  101	            stop = furthest + beyond if sell else furthest - beyond
  strategies/common.py:251	    if strategy == LEVEL_REVERSAL:
  strategies/common.py:252	        return settings.level_reversal.stop_beyond_furthest_pips
  strategies/common.py:265	    if idea.strategy != LEVEL_REVERSAL:
  strategies/common.py:266	        return None
  strategies/common.py:267	    return idea.context["stop_price"]
  ```
  `config/settings.toml:273`: `stop_beyond_furthest_pips = 6`
- **DESIGN.md:** line 196: "**Stop 6 pips beyond the furthest point** price reached"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Stop 6 pips beyond the furthest point price reached"
- **Mark:** Owner's words, unchanged

### 6.12 Take profit 20 pips, on any day
- **Code:** `strategies/common.py:228-229`
  ```python
  228	    if strategy == LEVEL_REVERSAL:
  229	        return settings.level_reversal.take_profit_pips
  ```
  `config/settings.toml:274`: `take_profit_pips = 20`
- **DESIGN.md:** line 196: "**take profit 20 pips** (`level_reversal.take_profit_pips`)"; line 208: "the level reversal's 20 pips ... on any day"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "take profit 20 pips."
- **Mark:** Owner's words, unchanged

### 6.13 Several setups triggering on the same candle and direction give one idea
- **Code:** `strategies/level_reversal/strategy.py:72-79`
  ```python
  72	        seen = set()
  74	            if e.version != "bounce" or e.kind != "trigger" or (e.time, e.direction) in seen:
  77	            if cand is not None:
  78	                seen.add((e.time, e.direction))
  ```
- **DESIGN.md:** line 199: "several setups triggering on the same candle and direction give one trade."
- **Source:** none from the owner; listed as a choice in `strategies/level_reversal/strategy.py:25`; commit 45628cc.
- **Mark:** Added without the owner asking

### 6.14 In every analyser state except consolidation, either way
- **Code:** `strategies/common.py:60`
  ```python
  60	    LEVEL_REVERSAL: {RANGING: "any", EMERGING: "any", TREND: "any", POSSIBLE_REVERSAL: "any"},
  ```
- **DESIGN.md:** line 197: "5. In every analyser state except consolidation, either way (2.2)"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation."
- **Mark:** Owner's words, unchanged

### 6.15 The direction rule does not apply to the level reversal
- **Code:** `strategies/common.py:49,289`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  ```
- **DESIGN.md:** line 197: "the direction rule (2.3) does not apply."
- **Source:** agreed design (c803d53) line 52, "### 2.3 Direction rule (applies to every strategy)"; owner, 2026-11-08T05:48:07Z, PASTED (the level reversal decision) does not mention the direction rule; no owner message exempting the level reversal found. Exemption written in commit 45628cc (2026-11-08 05:58).
- **Mark:** Changed from the owner's words  **Owner:** "Direction rule (applies to every strategy)" / **Code:** the level reversal is exempt from the direction rule.

### 6.16 New trades only from 06:00 to 20:30 UK
- **Code:** `strategies/common.py:150-153` (as 5.17)
  ```python
  152	    if not (sw.new_trades_from <= lt < sw.new_trades_until):
  ```
  `.env`: `NEW_TRADES_FROM=06:00`, `NEW_TRADES_UNTIL=20:30`
- **DESIGN.md:** line 198: "New trades from 06:00 to 20:30 UK"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "New trades 06:00 to 20:30 UK"
- **Mark:** Owner's words, unchanged

### 6.17 Closed at 20:30 UK every day
- **Code:** `strategies/common.py:43,175` (as 5.19)
  ```python
  43	OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 198: "closed at 20:30 UK"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "closed at 20:30"
- **Mark:** Owner's words, unchanged

### 6.18 No new trade in a big-news window
- **Code:** `strategies/common.py:156-158` (as 5.18)
  ```python
  156	    windows = no_new_trades(settings, pair, t, calendar)
  ```
- **DESIGN.md:** line 198: "not opened in a big-news window ... like the other strategies (section 6)"
- **Source:** agreed design (c803d53) line 200, "Big news: no new trades from 15 minutes before to 30 minutes after." (the owner's level reversal decision of 2026-11-08T05:48:07Z is silent on news)
- **Mark:** Owner's words, unchanged

### 6.19 Closed 15 minutes before big news
- **Code:** `strategies/common.py:45,183` (as 5.20)
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  183	    return strategy not in NEWS_ALLOWED
  ```
- **DESIGN.md:** line 198: "closed 15 minutes before big news, like the other strategies (section 6)"
- **Source:** agreed design (c803d53) line 200, "Open trades closed 15 minutes before."
- **Mark:** Owner's words, unchanged

### 6.20 No close on a rejection at a level
- **Code:** `strategies/common.py:47,189`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  189	    return strategy not in NO_LEVEL_CLOSE
  ```
- **DESIGN.md:** line 198: "no close on a rejection at a level (section 4)"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "no close on a rejection at a level."
- **Mark:** Owner's words, unchanged

### 6.21 Keeps the last 300 candles to measure the furthest point
- **Code:** `strategies/level_reversal/strategy.py:39,48`
  ```python
  39	KEEP_CANDLES = 300          # more than any setup lasts (pierce, reversal and confirmation within a few candles)
  48	        self.candles: deque = deque(maxlen=KEEP_CANDLES)
  ```
- **DESIGN.md:** none
- **Source:** none from the owner; commit 45628cc.
- **Mark:** Added without the owner asking

## 7. The analyser's states

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 38 | 3 | 28 | 0 | 69 |

Sources used: owner_messages.txt; agreed design `git show c803d53:docs/DESIGN.md`; 161 report
`autobot_reports/nms_audit_for_new_bot_20261106.md` (NMS). The owner's instruction to take
values from 161: agreed design (c803d53) line 97, "Words such as flat, narrow, close together, widening and fanning become
settings, starting from NMS's values on 161 where they exist"; owner, 2026-11-07T09:48:55Z, PASTED, "Every number the
design does not give becomes a setting. Start from AutoBot 161's NMS values in the audit report where they exist".

### 7.1 Worked out on the 5-minute candles, sell price
- **Code:** `analyser/features.py:90-93`
  ```python
  90	    m, ind, side = settings.market_states, settings.indicators, settings.chart.price
  93	    g = lambda c, f: getattr(c, f"{side}_{f}")  # noqa: E731
  ```
  `analyser/market_state.py:80` `warm = last_candles(store, "5m", week_open, ...)`; `config/settings.toml:146`: `price = "sell"`
- **DESIGN.md:** line 116: "Every indicator, for the analyser and the strategies, is worked out from the sell (bid) price"
- **Source:** owner, 2026-11-06T21:22:13Z, PASTED, "My IG chart is set to the sell (bid) price ... Change the levels, and every indicator worked out for the analyser and strategies, to use the sell (bid) price"; owner, 2026-11-07T11:26:26Z, PASTED, "ranging, consolidation and trend are decided on the 5-minute candles exactly as before"
- **Mark:** Owner's words, unchanged

### 7.2 Indicators the states use: Bollinger 20/2, EMAs 7, 13, 21, 100
- **Code:** `analyser/features.py:94-95`
  ```python
  94	    bands = bollinger(candles, side, ind.bollinger_periods, ind.bollinger_std_devs)
  95	    emas = {p: ema(candles, side, p) for p in (7, 13, 21, 100)}
  ```
  `config/settings.toml:289-290`: `bollinger_periods = 20`, `bollinger_std_devs = 2`; `:294` `ema_periods = [7, 13, 21, 100, 200]`
- **DESIGN.md:** lines 108-109: "| EMAs | 7, 13, 21, plus 100 and 200 |", "| Bollinger bands | 20 periods, 2 standard deviations |"
- **Source:** agreed design (c803d53) lines 103-104, "EMAs | 7, 13, 21, plus 100 and 200", "Bollinger bands | 20 periods, 2 standard deviations"
- **Mark:** Owner's words, unchanged

### 7.3 Starts fresh at each weekly open in consolidation, no direction
- **Code:** `analyser/states.py:124`
  ```python
  124	        self.now = MarketState(CONSOLIDATION, NONE, None, week_open, ["start of the trading week: watch and wait"])
  ```
  `analyser/market_state.py:76-77` `def _week_of(...): return self.hours.session(as_of)[0]`
- **DESIGN.md:** none
- **Source:** none found for the weekly start or the starting state; owner, 2026-11-07T09:48:55Z, PASTED, asked only "On start-up it replays recent candles and must reach exactly the same state as if it had never stopped"
- **Mark:** Added without the owner asking

### 7.4 Indicators warmed up on 2000 candles before the week's open
- **Code:** `analyser/market_state.py:80`
  ```python
  80	        warm = last_candles(store, "5m", week_open, self.s.market_states.indicator_warm_up_candles)
  ```
  `config/settings.toml:402`: `indicator_warm_up_candles = 2000`
- **DESIGN.md:** none
- **Source:** none found (assistant's value, commit 4fccb1f)
- **Mark:** Added without the owner asking

### 7.5 Ranging: band width 6 to 18 pips
- **Code:** `analyser/states.py:187`; `analyser/features.py:122`
  ```python
  187	        ok = (f.width is not None and m.ranging_min_band_pips <= f.width <= m.ranging_max_band_pips
  analyser/features.py:122	        width = (b.upper - b.lower) / ppp if b else None
  ```
  `config/settings.toml:356-357`: `ranging_min_band_pips = 6`, `ranging_max_band_pips = 18`
- **DESIGN.md:** line 48: "close together is a band width of at least 6 and at most 18 pips"
- **Source:** owner, 2026-11-07T15:20:10Z, TYPED, "Change the ranging numbers to: band width at least 6 and at most 18 pips"
- **Mark:** Owner's words, unchanged

### 7.6 Ranging: upper and lower band each flat, under 0.2 pips a candle
- **Code:** `analyser/states.py:186-189`
  ```python
  186	        flat = m.ranging_band_flat_max_pips_per_candle
  188	              and f.upper_slope is not None and abs(f.upper_slope) < flat
  189	              and f.lower_slope is not None and abs(f.lower_slope) < flat
  ```
  `config/settings.toml:358`: `ranging_band_flat_max_pips_per_candle = 0.2`
- **DESIGN.md:** line 48: "flat is the upper band and the lower band each moving less than 0.2 pips a candle"
- **Source:** owner, 2026-11-07T15:03:49Z, PASTED, "\"Flat\" must apply to the upper and the lower band, not only the middle"; owner, 2026-11-07T15:20:10Z, TYPED, "the upper and lower band slopes each below 0.2 pips a candle"
- **Mark:** Owner's words, unchanged

### 7.7 Slope: band move per candle over 6 candles
- **Code:** `analyser/features.py:112-117,168-169`
  ```python
  112	        def slope(attr: str, n: int) -> Decimal | None:
  117	            return (getattr(b, attr) - getattr(pb, attr)) / n / ppp
  168	            slope("middle", m.flat_slope_candles), slope("upper", m.flat_slope_candles),
  169	            slope("lower", m.flat_slope_candles), ...
  ```
  `config/settings.toml:350`: `flat_slope_candles = 6`
- **DESIGN.md:** line 48: "measured over 6 candles"
- **Source:** owner, 2026-11-07T15:08:44Z, PASTED, "measured over the existing 6-candle window"; 161 (nms_audit_for_new_bot_20261106.md, "`CHOP_SLOPE_LOOKBACK = int(float(os.getenv(\"CHOP_SLOPE_LOOKBACK\", \"6\")))`")
- **Mark:** Owner's words, unchanged

### 7.8 Ranging: price has reached both bands (check)
- **Code:** `analyser/features.py:127-129`; `analyser/states.py:190`
  ```python
  127	        recent = out[max(0, i - m.ranging_both_bands_candles + 1):] if out else []
  128	        both = (reached_up or any(f.reached_upper for f in recent)) and \
  129	               (reached_dn or any(f.reached_lower for f in recent))
  analyser/states.py:190	              and f.both_bands_recently and f.weave
  ```
- **DESIGN.md:** line 48: "price bounces between the upper and lower band"
- **Source:** agreed design (c803d53) line 46, "price bounces between the upper and lower band"; owner, 2026-11-07T15:03:49Z, PASTED, "Keep ... the check that price reached both bands, as the nearest match to \"bounces between the upper and lower band\""
- **Mark:** Owner's words, unchanged

### 7.9 Ranging: both bands reached within 24 candles
- **Code:** `analyser/features.py:127` (above)
  `config/settings.toml:360`: `ranging_both_bands_candles = 24`
- **DESIGN.md:** line 48: "price bounces between the bands when both bands have been reached within 24 candles"
- **Source:** settings comment `config/settings.toml:359` "(new)"; set in commit 4fccb1f by the assistant. Owner, 2026-11-07T15:08:44Z, PASTED, "keep the EMA weave, the 100 EMA flat check and both bands reached" (keeps the check; no number). DESIGN.md line 48's "(owner, 7 November 2026)" was written by the assistant; no owner message gives 24.
- **Mark:** Added without the owner asking

### 7.10 "On or near" a band: within 1 pip
- **Code:** `analyser/features.py:92,120-121,159-160`
  ```python
  92	    near = Decimal(m.near_band_pips) * ppp
  120	        reached_up = b is not None and h >= b.upper - near
  121	        reached_dn = b is not None and lo <= b.lower + near
  159	                on_up += g(x, "close") >= bx.upper - near
  160	                on_dn += g(x, "close") <= bx.lower + near
  ```
  `config/settings.toml:374`: `near_band_pips = 1`
- **DESIGN.md:** line 82: "Price moves to the bottom of the Bollinger band and stays on or near it" (no number)
- **Source:** settings comment `config/settings.toml:373` "(new)"; none found from the owner
- **Mark:** Added without the owner asking

### 7.11 Ranging: EMAs weave (7/13/21 order changed)
- **Code:** `analyser/features.py:78-85,162-163`; `analyser/states.py:190`
  ```python
  81	    if e7 < e13 < e21:
  82	        return "down"
  83	    if e7 > e13 > e21:
  84	        return "up"
  85	    return None
  162	        weave_window = stacks[max(0, i - m.weave_candles):i + 1]
  163	        weave = len(set(weave_window)) > 1
  ```
- **DESIGN.md:** line 48: "The EMAs weave back and forth instead of staying stacked"
- **Source:** agreed design (c803d53) line 46, "The EMAs weave back and forth instead of staying stacked"; owner, 2026-11-07T15:08:44Z, PASTED, "keep the EMA weave"
- **Mark:** Owner's words, unchanged

### 7.12 Weave window: 12 candles
- **Code:** `analyser/features.py:162` (above)
  `config/settings.toml:362`: `weave_candles = 12`
- **DESIGN.md:** none (no number)
- **Source:** settings comment `config/settings.toml:361` "(new)"; none found from the owner
- **Mark:** Added without the owner asking

### 7.13 Ranging: 100 EMA flat (check)
- **Code:** `analyser/states.py:191`
  ```python
  191	              and f.ema100_move is not None and f.ema100_move < m.ema100_flat_max_pips)
  ```
- **DESIGN.md:** line 48: "and the 100 EMA is flat"
- **Source:** agreed design (c803d53) line 46, "and the 100 EMA is flat"; owner, 2026-11-07T15:08:44Z, PASTED, "keep ... the 100 EMA flat check"
- **Mark:** Owner's words, unchanged

### 7.14 100 EMA flat: moved under 3 pips over 12 candles
- **Code:** `analyser/features.py:161,170`
  ```python
  161	        e100b = back(m.ema100_flat_candles)
  170	            (abs(e100 - e100b.ema100) / ppp) if (e100 is not None and e100b is not None and e100b.ema100 is not None)
  ```
  `config/settings.toml:364-365`: `ema100_flat_max_pips = 3`, `ema100_flat_candles = 12`
- **DESIGN.md:** none (no number)
- **Source:** settings comment `config/settings.toml:363` "(new)"; none found from the owner
- **Mark:** Added without the owner asking

### 7.15 Consolidation: bands narrow, 14 pips or less OR narrowing 6 candles in a row
- **Code:** `analyser/states.py:168`; `analyser/features.py:124-125`
  ```python
  168	        narrow = f.width is not None and (f.width <= m.narrow_band_max_pips or f.narrowing_for >= m.narrowing_candles)
  analyser/features.py:124	        narrowing = (prev.narrowing_for + 1 if prev is not None and prev.width is not None and width is not None
  analyser/features.py:125	                     and width < prev.width else 0)
  ```
  `config/settings.toml:345-346`: `narrow_band_max_pips = 14`, `narrowing_candles = 6`
- **DESIGN.md:** line 52: "narrow Bollinger bands" (no number)
- **Source:** owner, 2026-11-07T10:24:09Z, PASTED, "replace the 8-pip band width with \"band width 14 pips or less, OR the bands have narrowed for 6 candles in a row\""
- **Mark:** Owner's words, unchanged

### 7.16 Consolidation: middle band flat, under 0.5 pips a candle
- **Code:** `analyser/states.py:123,169-170`
  ```python
  123	        self.flat = self.m.flat_max_pips_per_candle
  169	        ok = (narrow and f.mid_slope is not None
  170	              and abs(f.mid_slope) < self.flat and f.no_close_outside ...
  ```
  `config/settings.toml:349`: `flat_max_pips_per_candle = 0.5`
- **DESIGN.md:** line 52: "no direction"; line 102: "starting from NMS's values on 161 where they exist"
- **Source:** 161 (nms_audit_for_new_bot_20261106.md, "`CHOP_SLOPE_MAX_PIPS_PER_BAR = float(os.getenv(\"CHOP_SLOPE_MAX_PIPS_PER_BAR\", \"0.5\"))`"); agreed design (c803d53) line 97; owner, 2026-11-07T10:24:09Z, PASTED, "Keep the other checks."
- **Mark:** Owner's words, unchanged

### 7.17 Consolidation: no candle closed outside the bands for 6 candles
- **Code:** `analyser/features.py:126,130-133`
  ```python
  126	        outside = b is not None and (cl > b.upper or cl < b.lower)
  130	        qn = m.consolidation_quiet_candles
  132	        no_outside = len(window) == qn - 1 and b is not None and not outside and \
  133	            not any(f.closed_outside for f in window)
  ```
  `config/settings.toml:370`: `consolidation_quiet_candles = 6`
- **DESIGN.md:** line 52: "price between them touching neither band"
- **Source:** owner, 2026-11-07T10:24:09Z, PASTED, "Replace \"neither band reached for 6 candles\" with \"no candle has closed outside the bands for 6 candles\""
- **Mark:** Owner's words, unchanged

### 7.18 Consolidation: average body at most 3 pips (over the same 6 candles)
- **Code:** `analyser/features.py:134-135`; `analyser/states.py:171`
  ```python
  134	        bodies = [abs(g(x, "close") - g(x, "open")) / ppp for x in candles[max(0, i - qn + 1):i + 1]]
  135	        avg_body = sum(bodies) / len(bodies) if len(bodies) == qn else None
  analyser/states.py:171	              and f.avg_body <= m.consolidation_max_body_pips and f.colour_ratio is not None
  ```
  `config/settings.toml:371`: `consolidation_max_body_pips = 3`
- **DESIGN.md:** line 52: "small candles"
- **Source:** agreed design (c803d53) line 50, "small candles" (no number); settings comment `config/settings.toml:368` "(new)"; owner, 2026-11-07T10:24:09Z, PASTED, "Keep the other checks." (no number given)
- **Mark:** Added without the owner asking

### 7.19 Consolidation: green and red body sizes within 2 times of each other
- **Code:** `analyser/features.py:136-141`; `analyser/states.py:172`
  ```python
  140	        lo_side, hi_side = min(greens, reds), max(greens, reds)
  141	        colour_ratio = (hi_side / lo_side) if lo_side else (Decimal(1) if hi_side == 0 else None)
  analyser/states.py:172	              and f.colour_ratio <= m.consolidation_colour_max_ratio)
  ```
  `config/settings.toml:372`: `consolidation_colour_max_ratio = 2`
- **DESIGN.md:** line 52: "green and red roughly the same size"
- **Source:** agreed design (c803d53) line 50, "green and red roughly the same size" (no number); settings comment `config/settings.toml:369` "(new: 2 means one side at most twice the other)"
- **Mark:** Added without the owner asking

### 7.20 Base state: ranging checked before consolidation; otherwise consolidation without its checks
- **Code:** `analyser/states.py:197-202`
  ```python
  198	        r, rwhy = self.ranging(f)
  199	        if r:
  200	            return RANGING, rwhy
  201	        c, cwhy = self.consolidation(f)
  202	        return CONSOLIDATION, (cwhy if c else "no direction any more: watch and wait")
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.21 Condition changes need 2 candles in a row (flip-flop protection)
- **Code:** `analyser/states.py:473-484`, used at `:349`, `:365`, `:394-398`
  ```python
  477	        if self._pending is not None and self._pending[:2] == target[:2]:
  478	            self._pending_count += 1
  479	        else:
  480	            self._pending, self._pending_count = target, 1
  481	        if self._pending_count >= self.m.persistence_candles:
  ```
  `config/settings.toml:377`: `persistence_candles = 2`
- **DESIGN.md:** line 99: "Every state is protected from flip-flopping."
- **Source:** agreed design (c803d53) line 94, "Every state is protected from flip-flopping"; 161 (nms_audit_for_new_bot_20261106.md, "`PERSISTENCE_BARS = 2`")
- **Mark:** Owner's words, unchanged

### 7.22 Emerging trend starts at once on a confirmed rejection at a strong level (from consolidation or ranging)
- **Code:** `analyser/states.py:275-281,373-374`
  ```python
  280	                if self.strong_levels(stp):        # only a strong level may start or replace an emerging trend
  281	                    yield e, stp
  373	        for e, stp in important_rejection(CONFIRMATION):
  374	            return self._start_emerging(f, _move(e.direction), f"rejected at a level: {e.note}", stp)
  ```
- **DESIGN.md:** line 74: "moves to emerging trend at the moment the level is rejected, without waiting for any strategy"
- **Source:** agreed design (c803d53) line 69, "moves to emerging trend at the moment the level is rejected"; owner, 2026-11-07T09:48:55Z, PASTED, "including the rejection at a level starting an emerging trend"
- **Mark:** Owner's words, unchanged

### 7.23 Strong levels: pivot, R1-R3, S1-S3, round 00/50, previous day high/low, or a turning level lined up with one
- **Code:** `analyser/states.py:417-426`
  ```python
  417	        strong = set(self.m.strong_level_types)
  418	        out = [p for p in setup.pierced if p["what"] in strong]
  420	            if p["what"] in ("turning_high", "turning_low"):
  423	                    if name in g["levels"] and any(m.split(" ")[0] in strong for m in g["levels"]):
  ```
  `config/settings.toml:408`: `strong_level_types = ["pivot", "R1", "R2", "R3", "S1", "S2", "S3", "round_number", "previous_day_high", "previous_day_low"]`
- **DESIGN.md:** line 74: "Price pushes into a strong level, such as the daily pivot" (list not in DESIGN.md)
- **Source:** owner, 2026-11-07T11:15:12Z, PASTED, "A turning level on its own can no longer start or replace an emerging trend. Only the pivot, R1 to R3, S1 to S3, round numbers 00 and 50, the previous day's high or low, or a turning level that lines up with one of those can"; owner, 2026-11-07T11:31:35Z, TYPED, "Keep the strong-level rule."
- **Mark:** Owner's words, unchanged

### 7.24 Breakout from consolidation: one close beyond a band starts an emerging trend at once
- **Code:** `analyser/states.py:375-381`
  ```python
  375	        if st == CONSOLIDATION and f.upper is not None:
  376	            if f.c > f.upper:
  377	                return self._start_emerging(f, UP, ...
  379	            if f.c < f.lower:
  380	                return self._start_emerging(f, DOWN, ...
  ```
- **DESIGN.md:** line 52: "When price breaks out, the analyser moves to emerging trend."
- **Source:** agreed design (c803d53) line 50, "When price breaks out, the analyser moves to emerging trend."; owner, 2026-11-07T17:48:56Z, PASTED, "the analyser moves from consolidation to an emerging trend because a candle closed outside the Bollinger band"
- **Mark:** Owner's words, unchanged

### 7.25 Breakout from ranging: 2 closes in a row beyond the same band
- **Code:** `analyser/states.py:382-390`
  ```python
  383	            way = UP if f.c > f.upper else DOWN if f.c < f.lower else None
  385	            self.breakout_run = (way, run + 1 if way is not None and way == run_dir else (1 if way else 0))
  386	            if way is not None and self.breakout_run[1] >= self.m.persistence_candles:
  ```
- **DESIGN.md:** line 182: "because price broke out of a range (two closes beyond the same band, section 2.5)"
- **Source:** none found asking for it (in commit 4fccb1f). Later owner prompts refer to it as existing: owner, 2026-11-12T18:11:03Z, PASTED, "Two closes in a row beyond the same band, the same as the range breakout already uses"
- **Mark:** Added without the owner asking

### 7.26 An opposite confirmed rejection at a strong level replaces an emerging trend
- **Code:** `analyser/states.py:309-314`
  ```python
  309	            if st == EMERGING:
  310	                for e, stp in important_rejection(CONFIRMATION):
  311	                    if _move(e.direction) == _opposite(d):
  312	                        return self._start_emerging(f, _move(e.direction),
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T10:24:09Z, PASTED, "A confirmed rejection at an important level (pivot, R2, S2, round number, turning level) in the opposite direction to the current emerging trend replaces it with an emerging trend the other way"; narrowed by owner, 2026-11-07T11:15:12Z, PASTED, "can no longer start or replace an emerging trend. Only the pivot, R1 to R3, ..."
- **Mark:** Owner's words, unchanged

### 7.27 Emerging trend cancelled only by 2 closes in a row back beyond the level / back inside the bands
- **Code:** `analyser/states.py:437-451`
  ```python
  439	        if kind == "level":
  440	            back = f.c > level if d == DOWN else f.c < level
  443	            back = f.lower is not None and f.lower < f.c < f.upper
  445	        self.back_count = self.back_count + 1 if back else 0
  446	        if self.back_count < self.m.persistence_candles:
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T10:11:51Z, PASTED, "remove the 3-pip cancel. An emerging trend that started from a rejection at a level is only cancelled if two candles in a row close back beyond that level. One that started from a breakout is only cancelled if two candles in a row close back inside the Bollinger bands."
- **Mark:** Owner's words, unchanged

### 7.28 The cancel level: the strong level nearest the piercing candle's edge
- **Code:** `analyser/states.py:428-435`
  ```python
  431	        edge = getattr(setup.pierce, f"{side}_high" if d == DOWN else f"{side}_low")
  432	        cands = self.strong_levels(setup) or \
  433	                [p for p in setup.pierced if p["what"] not in ("upper Bollinger band", "lower Bollinger band")]
  434	        best = min(cands, key=lambda p: abs(p["price"] - edge))
  ```
- **DESIGN.md:** none
- **Source:** none found (owner said only "that level", 2026-11-07T10:11:51Z)
- **Mark:** Added without the owner asking

### 7.29 Emerging trend ends in consolidation (held 2 candles); not by ranging or the 100 EMA
- **Code:** `analyser/states.py:345-350`
  ```python
  345	            if st == EMERGING:
  348	                c_ok, c_why = self.consolidation(f)
  349	                return self._persist(f, (CONSOLIDATION, NONE, f"the emerging {d} trend settled into "
  350	                                                              f"consolidation: {c_why}") if c_ok else None)
  ```
- **DESIGN.md:** line 52: "Consolidation (this includes a trend running out of steam)"
- **Source:** owner, 2026-11-07T10:45:48Z, TYPED, "Allow consolidation to end an emerging trend"
- **Mark:** Owner's words, unchanged

### 7.30 Trend proof: in an emerging trend, a new extreme on the outer band
- **Code:** `analyser/states.py:208-211,330-335`
  ```python
  210	        on_band = f.reached_lower if d == DOWN else f.reached_upper
  211	        ok = (new_extreme and bounce_failed_before and on_band and f.stack == d
  331	                ok, why = self.proof(f, d, True, bounce_failed_before) if st == EMERGING else (False, "")
  334	                    return self._change(f, TREND, d, STRONG_PUSH if self.push(f, d) else SLOW_GRIND,
  ```
- **DESIGN.md:** line 85: "It becomes clear when the first bounce fails under the EMAs and middle band and price makes a new low on the lower band."
- **Source:** agreed design (c803d53) line 80, same words
- **Mark:** Owner's words, unchanged

### 7.31 Trend proof: the failed bounce on an earlier candle, after the last new extreme
- **Code:** `analyser/states.py:256-258,402-404`
  ```python
  256	        # design 2.5: the bounce fails first, on an EARLIER candle, then a new extreme; a candle that is
  257	        # both a failed bounce and the new extreme does not prove the trend (owner, 12 November 2026)
  258	        bounce_failed_before = self.failed_bounce
  404	        self.failed_bounce = False
  ```
- **DESIGN.md:** line 85 (as 7.30)
- **Source:** owner, 2026-11-12T11:37:00Z, TYPED, "The failed bounce must come first, on an earlier candle, and the new high (or low) afterwards, never both on the same candle. Change nothing else."; owner, 2026-11-12T11:57:25Z, TYPED, "Owner's decision: A, keep the rule."
- **Mark:** Owner's words, unchanged

### 7.32 What a failed bounce is: a counter-coloured candle whose high stays at or under the higher of the 21 EMA and middle band (low for an uptrend)
- **Code:** `analyser/states.py:264-273`
  ```python
  265	            cap = max(x for x in (f.ema21, f.middle) if x is not None) if (f.ema21 or f.middle) else None
  268	                if watched == DOWN and f.green and f.h <= cap + tol:
  270	                if watched == UP and f.red:
  271	                    floor_ = min(x for x in (f.ema21, f.middle) if x is not None)
  272	                    if f.l >= floor_ - tol:
  ```
- **DESIGN.md:** line 81: "Small bounces fail at or below the short EMAs and the middle of the Bollinger band"; line 85: "fails under the EMAs and middle band"
- **Source:** agreed design (c803d53) line 76, "Small bounces fail at or below the short EMAs and the middle of the Bollinger band"; line 80, "the first bounce fails under the EMAs and middle band"
- **Mark:** Changed from the owner's words. **Owner:** "fail at or below the short EMAs and the middle of the Bollinger band" / "fails under the EMAs and middle band". **Code:** only the 21 EMA; the bounce's high may reach the HIGHER of the 21 EMA and middle band plus 1 pip (low: the lower of them minus 1 pip).

### 7.33 Failed bounce allowance: 1 pip
- **Code:** `analyser/states.py:266`
  ```python
  266	            tol = Decimal(self.m.failed_bounce_within_pips) * self.ppp
  ```
  `config/settings.toml:385`: `failed_bounce_within_pips = 1`
- **DESIGN.md:** none
- **Source:** settings comment `config/settings.toml:383-384` "(new)"; none found from the owner
- **Mark:** Added without the owner asking

### 7.34 Trend proof: 7/13/21 EMAs stacked in the trend's direction for at least 3 candles
- **Code:** `analyser/states.py:211-212`; `analyser/features.py:106`
  ```python
  211	        ok = (... f.stack == d
  212	              and f.stacked_for >= m.ema_stacked_candles
  analyser/features.py:106	        run = run + 1 if stacks and st is not None and stacks[-1] == st else (1 if st else 0)
  ```
  `config/settings.toml:382`: `ema_stacked_candles = 3`
- **DESIGN.md:** line 79: "They flatten, cross and turn down in order, then start to spread apart."
- **Source:** agreed design (c803d53) line 74, "They flatten, cross and turn down in order"; 161 (nms_audit_for_new_bot_20261106.md, "`if s[\"ema_rising_bars\"] == 3:`", "EMA 7>13>21 three bars")
- **Mark:** Owner's words, unchanged

### 7.35 Trend proof: close beyond the 7, 13, 21 and 100 EMAs
- **Code:** `analyser/states.py:213-214`
  ```python
  213	              and None not in (f.ema7, f.ema13, f.ema21, f.ema100, band_slope)
  214	              and all(beyond(f.c, e) for e in (f.ema7, f.ema13, f.ema21, f.ema100))
  ```
- **DESIGN.md:** line 79: "Price drops through the 7, 13 and 21 EMAs and stays below them."; line 80: "Price drops below the 100 EMA and stays below it."
- **Source:** agreed design (c803d53) lines 74-75, same words
- **Mark:** Owner's words, unchanged

### 7.36 Trend proof: the outer band sloping at least 0.5 pips a candle the trend's way
- **Code:** `analyser/states.py:209,215`
  ```python
  209	        band_slope = f.lower_slope if d == DOWN else f.upper_slope
  215	              and (band_slope <= -self.flat if d == DOWN else band_slope >= self.flat))
  ```
  `config/settings.toml:349`: `flat_max_pips_per_candle = 0.5` (counted at 7.16)
- **DESIGN.md:** line 82: "and the band starts to slope down"
- **Source:** agreed design (c803d53) line 77, "and the band starts to slope down"; 161 (nms_audit_for_new_bot_20261106.md, "CHOP_SLOPE_MAX_PIPS_PER_BAR ... \"0.5\"") via agreed design line 97
- **Mark:** Owner's words, unchanged

### 7.37 Trend type: strong push or, otherwise, slow grind
- **Code:** `analyser/states.py:334,487`
  ```python
  334	                    return self._change(f, TREND, d, STRONG_PUSH if self.push(f, d) else SLOW_GRIND,
  487	        want = STRONG_PUSH if self.push(f, d) else SLOW_GRIND
  ```
- **DESIGN.md:** line 50: "an established direction, either a slow grind or a strong push"
- **Source:** agreed design (c803d53) line 48, "either a slow grind or a strong push. Both are recognised from price action."
- **Mark:** Owner's words, unchanged

### 7.38 Strong push: at least 70% of the body size over the last 6 candles in the trend's colour
- **Code:** `analyser/features.py:146-152`; `analyser/states.py:225,227`
  ```python
  146	        pc = candles[max(0, i - m.push_candles + 1):i + 1]
  148	        up_bodies = sum((g(x, "close") - g(x, "open") for x in pc if g(x, "close") > g(x, "open")), ZERO)
  151	        green_share = up_bodies / all_bodies if all_bodies else ZERO
  analyser/states.py:227	        return (share * 100 >= m.push_colour_body_percent and f.widening is not None
  ```
  `config/settings.toml:391-392`: `push_candles = 6`, `push_colour_body_percent = 70`
- **DESIGN.md:** line 87: "candles mostly green"
- **Source:** owner, 2026-11-07T10:35:17Z, TYPED, "change \"70% of candles in the trend's colour\" to \"70% of the total candle body size over the last 6 candles is in the trend's colour\" ... Keep 70% as a setting."
- **Mark:** Owner's words, unchanged

### 7.39 Strong push: bands at least 150% of their width 12 candles before
- **Code:** `analyser/features.py:153-154`; `analyser/states.py:228`
  ```python
  153	        wb = back(m.band_widening_candles)
  154	        widening = (width / wb.width) if (width is not None and wb is not None and wb.width) else None
  analyser/states.py:228	                and f.widening * 100 >= m.push_band_widening_percent and f.fan is not None
  ```
  `config/settings.toml:393-394`: `push_band_widening_percent = 150`, `band_widening_candles = 12`
- **DESIGN.md:** line 87: "the bands opening up wide"
- **Source:** agreed design (c803d53) line 82, "the bands opening up wide" (no number); settings comment `config/settings.toml:386` "(new)"
- **Mark:** Added without the owner asking

### 7.40 Strong push: 7 and 21 EMAs at least 6 pips apart
- **Code:** `analyser/features.py:174`; `analyser/states.py:229`
  ```python
  174	            (abs(e7 - e21) / ppp) if (e7 is not None and e21 is not None) else None,
  analyser/states.py:229	                and f.fan >= m.push_ema_fan_pips and riding >= m.push_riding_band_closes)
  ```
  `config/settings.toml:395`: `push_ema_fan_pips = 6`
- **DESIGN.md:** line 87: "the 7, 13 and 21 EMAs fanning wide apart"
- **Source:** agreed design (c803d53) line 82, "fanning wide apart" (no number); settings comment "(new)"; 161 (nms_audit_for_new_bot_20261106.md, "**EMAs fanning apart** — **NOT USED anywhere in the five NMS pieces**")
- **Mark:** Added without the owner asking

### 7.41 Strong push: at least 3 of the 6 closes on or beyond the outer band
- **Code:** `analyser/features.py:155-160`; `analyser/states.py:226,229`
  ```python
  analyser/states.py:226	        riding = f.closes_on_lower if d == DOWN else f.closes_on_upper
  analyser/states.py:229	                and f.fan >= m.push_ema_fan_pips and riding >= m.push_riding_band_closes)
  ```
  `config/settings.toml:396`: `push_riding_band_closes = 3`
- **DESIGN.md:** line 87: "price riding along or just outside the upper band"
- **Source:** agreed design (c803d53) line 82, same words (no number); settings comment "(new)"
- **Mark:** Added without the owner asking

### 7.42 A change of trend type needs 2 candles in a row
- **Code:** `analyser/states.py:491-494`
  ```python
  491	        self._type_count = self._type_count + 1 if self._type_pending == want else 1
  493	        if self._type_count < self.m.persistence_candles:
  494	            return None
  ```
- **DESIGN.md:** line 99: "Every state is protected from flip-flopping."
- **Source:** agreed design (c803d53) line 94; 161 (nms_audit_for_new_bot_20261106.md, "`PERSISTENCE_BARS = 2`")
- **Mark:** Owner's words, unchanged

### 7.43 A change of trend type is not new evidence (does not reset the fade)
- **Code:** `analyser/states.py:500-502`
  ```python
  500	        news = self.last_news             # a change of type is not new evidence of the trend
  501	        ch = self._change(f, TREND, d, want, why, [why])
  502	        self.last_news = news
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.44 A trend ends when price closes back past the 100 EMA for 2 candles
- **Code:** `analyser/states.py:352,355-358`
  ```python
  352	            wrong_side = f.ema100 is not None and ((d == DOWN and f.c > f.ema100) or (d == UP and f.c < f.ema100))
  355	            if wrong_side:
  356	                target = (RANGING if r_ok else CONSOLIDATION, NONE,
  ```
- **DESIGN.md:** none (line 80: "Price drops below the 100 EMA and stays below it." is a sign of a trend, not an end)
- **Source:** none found (commit 4fccb1f)
- **Mark:** Added without the owner asking

### 7.45 A trend ends in consolidation (running out of steam), held 2 candles
- **Code:** `analyser/states.py:359-360`
  ```python
  359	            elif c_ok:
  360	                target = (CONSOLIDATION, NONE, f"the {d} {st} ran out of steam: {c_why}")
  ```
- **DESIGN.md:** line 52: "Consolidation (this includes a trend running out of steam)"
- **Source:** agreed design (c803d53) line 50, same words
- **Mark:** Owner's words, unchanged

### 7.46 A trend ends in ranging, held 2 candles
- **Code:** `analyser/states.py:361-362`
  ```python
  361	            elif r_ok:
  362	                target = (RANGING, NONE, f"the {d} {st} turned into a range: {r_why}")
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.47 Possible reversal: a move of at least 30 pips since the trend started AND a confirmed rejection at a level (not the band) against it
- **Code:** `analyser/states.py:308,315-325`
  ```python
  308	            moved = self._pips(self.extreme, self.start_price) if self.extreme is not None else Decimal(0)
  316	                if e.kind == CONFIRMATION and _move(e.direction) == _opposite(d):
  318	                    at = self._levels_of(stp)
  319	                    if moved >= self.s.possible_reversal.min_trend_move_pips and at:
  ```
  `config/settings.toml:247`: `min_trend_move_pips = 30`
- **DESIGN.md:** line 51: "price has moved at least 30 pips since it started, a strong reversal candle appears, recognised by the shared rejection part"
- **Source:** agreed design (c803d53) line 49, same words; owner, 2026-11-07T10:11:51Z, PASTED, "Possible reversal: only after the 30-pip move AND a confirmed rejection at a level from the shared rejection part. A single opposite candle is not enough."; owner, 2026-11-06T15:05:45Z, PASTED, "possible reversal: trend must have moved at least 30 pips"
- **Mark:** Owner's words, unchanged

### 7.48 A possible reversal can also come from an emerging trend
- **Code:** `analyser/states.py:307,315`
  ```python
  307	        if st in TRENDING:
  315	            for e in bounce:
  ```
  (`TRENDING = (EMERGING, TREND)`, line 72)
- **DESIGN.md:** line 51: "after a trend has been running"
- **Source:** agreed design (c803d53) line 49, "after a trend has been running"; none found for emerging trends
- **Mark:** Added without the owner asking

### 7.49 Section 2.6's signs are evidence only; none is waited for
- **Code:** `analyser/states.py:231-232,320,325`
  ```python
  232	        """Section 2.6: what points to a possible reversal (evidence only: none is waited for)."""
  320	                        signs = self.reversal_signs(f, d, stp)
  325	                                            f"{moved} pips: {e.note}", [e.note, *signs])
  ```
- **DESIGN.md:** line 91: "MACD lags price, so the bot must never wait for MACD to turn before allowing a reversal."
- **Source:** agreed design (c803d53) line 86, same words; owner, 2026-11-07T10:11:51Z, PASTED, "only after the 30-pip move AND a confirmed rejection at a level"
- **Mark:** Owner's words, unchanged

### 7.50 MACD sign: histogram on the old direction's side
- **Code:** `analyser/states.py:234-235`
  ```python
  234	        if f.macd_hist is not None and ((d_old == DOWN and f.macd_hist < 0) or (d_old == UP and f.macd_hist > 0)):
  235	            signs.append(f"MACD histogram {self._p(f.macd_hist)} still shows the {d_old} move")
  ```
  `config/settings.toml:297-299`: `macd_fast_periods = 35`, `macd_slow_periods = 45`, `macd_signal_periods = 30`
- **DESIGN.md:** line 91: "at its biggest histogram bar in the old direction, or already past its biggest and shrinking"
- **Source:** agreed design (c803d53) line 86, same words; line 105, "MACD | 35, 45, 30"
- **Mark:** Changed from the owner's words. **Owner:** "at its biggest histogram bar in the old direction, or already past its biggest and shrinking". **Code:** any histogram value on the old direction's side of zero.

### 7.51 RSI sign: below 40 (old trend down) or above 60 (up)
- **Code:** `analyser/states.py:236-238`
  ```python
  236	        if f.rsi is not None and ((d_old == DOWN and f.rsi < self.s.indicators.rsi_lower_line + 10)
  237	                                  or (d_old == UP and f.rsi > self.s.indicators.rsi_upper_line - 10)):
  ```
  `config/settings.toml:302-304`: `rsi_periods = 3`, `rsi_upper_line = 70`, `rsi_lower_line = 30`
- **DESIGN.md:** line 92: "RSI has gone beyond 30 or 70 and is turning back."
- **Source:** agreed design (c803d53) line 87, same words
- **Mark:** Changed from the owner's words. **Owner:** "RSI has gone beyond 30 or 70 and is turning back". **Code:** RSI under 30+10 or over 70-10, with no turning-back check.

### 7.52 Time-of-day sign: inside a reversal watch window
- **Code:** `analyser/states.py:239-240`
  ```python
  239	        if in_watch_window(self.s, f.candle.start):
  240	            signs.append("in a reversal watch window (time of day)")
  ```
- **DESIGN.md:** line 94: "Time of day, such as just before the New York session opens."
- **Source:** agreed design (c803d53) line 89, same words; owner, 2026-11-06T15:05:45Z, PASTED, "reversal watch times: 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00"
- **Mark:** Owner's words, unchanged

### 7.53 Level sign: the rejection pierced a level
- **Code:** `analyser/states.py:241-244`
  ```python
  241	        levels = [p["what"] for p in setup.pierced if p["what"] not in ("upper Bollinger band",
  242	                                                                         "lower Bollinger band")]
  ```
- **DESIGN.md:** line 95: "Price at a level, including recent hourly highs and lows."
- **Source:** agreed design (c803d53) line 90, same words
- **Mark:** Owner's words, unchanged

### 7.54 Possible reversal -> emerging trend the new way when that rejection setup triggers
- **Code:** `analyser/states.py:286-289`
  ```python
  287	                if e.setup == self.reversal_setup and e.kind == TRIGGER:
  288	                    return self._start_emerging(f, _move(e.direction), f"the reversal triggered: {e.note}",
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.55 Possible reversal -> back to the old trend when the old trend makes a new extreme
- **Code:** `analyser/states.py:290-295`
  ```python
  290	            if new_extreme:
  291	                ch = self._change(f, old_state, old_dir, old_type,
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.56 Possible reversal -> back to the old trend when the setup is cancelled or expires
- **Code:** `analyser/states.py:296-299`
  ```python
  297	                if e.setup == self.reversal_setup and e.kind in (CANCELLED, EXPIRED):
  298	                    return self._change(f, old_state, old_dir, old_type,
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.57 Evidence fades: nothing new for 24 candles ends an emerging trend, trend or possible reversal (to the base state at once)
- **Code:** `analyser/states.py:300-303,340-344`
  ```python
  300	            if self.n - self.last_news >= self.m.evidence_fades_after_candles:
  301	                state, why = self.base(f)
  340	            if self.n - self.last_news >= self.m.evidence_fades_after_candles:
  341	                state, why = self.base(f)
  ```
  `config/settings.toml:380`: `evidence_fades_after_candles = 24`
- **DESIGN.md:** line 100: "Evidence fades after a set time if nothing new happens."
- **Source:** agreed design (c803d53) line 95, same words; 161 (nms_audit_for_new_bot_20261106.md, "`EVIDENCE_TTL_BARS = 24              # 120 min`")
- **Mark:** Owner's words, unchanged

### 7.58 What counts as new evidence: a state change, a new extreme, a strong-level rejection with the trend
- **Code:** `analyser/states.py:155,326-329,405`
  ```python
  155	        self.last_news = self.n
  326	            for e, stp in important_rejection(CONFIRMATION):
  327	                if _move(e.direction) == d:
  328	                    self.last_news = self.n
  405	        self.last_news = self.n
  ```
- **DESIGN.md:** line 100: "if nothing new happens" (not defined)
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.59 Order of checks on a candle
- **Code:** `analyser/states.py:284-370`
  ```python
  284	        if st == POSSIBLE_REVERSAL and self.before is not None:
  307	        if st in TRENDING:
  330	            if new_extreme:
  373	        for e, stp in important_rejection(CONFIRMATION):
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 7.60 Strategies allowed in ranging: range trade; level reversal
- **Code:** `analyser/states.py:65`
  ```python
  65	    RANGING: ("range trade", "level reversal"),
  ```
- **DESIGN.md:** line 42: "| Ranging | Range trade; level reversal (3.6), either way |"
- **Source:** agreed design (c803d53) line 40, "| Ranging | Range trade |"; owner, 2026-11-08T05:48:07Z, PASTED, "the level reversal ... in any analyser state except consolidation"
- **Mark:** Owner's words, unchanged

### 7.61 Strategies allowed in an emerging trend: EMA pullback, breakout, level reversal
- **Code:** `analyser/states.py:66`
  ```python
  66	    EMERGING: ("EMA pullback", "breakout", "level reversal"),
  ```
- **DESIGN.md:** line 43: "| Emerging trend | EMA pullback, breakout (3.5), in the trend's direction only. Not the slow grind (owner, 8 November 2026). Level reversal (3.6), either way |"
- **Source:** owner, 2026-11-07T16:53:46Z, PASTED, "it trades in a trend and in an emerging trend" (EMA pullback); owner, 2026-11-07T19:24:52Z, PASTED, "It looks for a trade when the analyser moves into an emerging trend because price broke out" (breakout); owner, 2026-11-07T19:58:43Z, PASTED, "Trend only, in the trend's direction" (slow grind), accepted 2026-11-08T05:01:05Z, TYPED, "switch the slow grind on with result 13's settings"; owner, 2026-11-07T17:35:26Z / 17:38:00Z, "only in trend (not emerging trend)" / TYPED "Use version 3 for the bounce"; owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation" (level reversal)
- **Mark:** Owner's words, unchanged

### 7.62 Strategies allowed in a trend: slow grind, EMA pullback, Bollinger bounce against the trend only, level reversal
- **Code:** `analyser/states.py:67-68`
  ```python
  67	    TREND: ("slow grind", "EMA pullback", "breakout", "Bollinger band bounce (against the trend's direction only)",
  68	            "level reversal"),
  ```
- **DESIGN.md:** line 44: "| Trend | Slow grind (either type of trend ...), EMA pullback, breakout (3.5), in the trend's direction only; Bollinger band bounce against the trend's direction only (owner, 7 November 2026); level reversal (3.6), either way |"
- **Source:** agreed design (c803d53) line 42, "| Trend | Slow grind, EMA pullback, Bollinger band bounce in the trend's direction only |"; owner, 2026-11-07T17:35:26Z, PASTED, "3. Possible reversal, plus emerging trend and trend but only against the trend's direction, and only in trend (not emerging trend)" + 17:38:00Z, TYPED, "Use version 3 for the bounce"; owner, 2026-11-07T16:53:46Z, PASTED, "it trades in a trend and in an emerging trend"; owner, 2026-11-07T19:58:43Z, PASTED, "Trend only, in the trend's direction"; owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation"
- **Mark:** Owner's words, unchanged

### 7.63 Breakout listed as allowed in a trend
- **Code:** `analyser/states.py:67` (above, `"breakout"`), added in commit b2514d8
- **DESIGN.md:** line 44: "EMA pullback, breakout (3.5), in the trend's direction only"
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "It looks for a trade only at the moment the analyser moves from consolidation to an emerging trend"; owner, 2026-11-07T19:24:52Z, PASTED, "It looks for a trade when the analyser moves into an emerging trend". No owner message allows it in a trend.
- **Mark:** Added without the owner asking

### 7.64 Strategies allowed in a possible reversal: Bollinger bounce; level reversal
- **Code:** `analyser/states.py:69`
  ```python
  69	    POSSIBLE_REVERSAL: ("Bollinger band bounce", "level reversal"),
  ```
- **DESIGN.md:** line 45: "| Possible reversal | Bollinger band bounce; level reversal (3.6), either way |"
- **Source:** agreed design (c803d53) line 43, "| Possible reversal | Bollinger band bounce |"; owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation"
- **Mark:** Owner's words, unchanged

### 7.65 Strategies allowed in consolidation: none
- **Code:** `analyser/states.py:70`
  ```python
  70	    CONSOLIDATION: (),
  ```
- **DESIGN.md:** line 46: "| Consolidation | None (not even the level reversal). Watch and wait for a break |"
- **Source:** agreed design (c803d53) line 44, "| Consolidation | None. Watch and wait for a break |"; owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation"
- **Mark:** Owner's words, unchanged

### 7.66 Big spike: range over 3 times the average of the last 20 candles (worked out; not read by states.py)
- **Code:** `analyser/features.py:143-145`
  ```python
  143	        prev_ranges = [(g(x, "high") - g(x, "low")) / ppp for x in candles[max(0, i - m.spike_average_candles):i]]
  144	        avg_range = sum(prev_ranges) / len(prev_ranges) if len(prev_ranges) == m.spike_average_candles else None
  145	        spike = avg_range is not None and avg_range > 0 and rng > avg_range * m.spike_range_multiple
  ```
  `config/settings.toml:399-400`: `spike_range_multiple = 3`, `spike_average_candles = 20`
- **DESIGN.md:** line 83: "The candles are small and steady, with no big spikes."
- **Source:** agreed design (c803d53) line 78, same words (no number); settings comment `config/settings.toml:397-398` "(new)"
- **Mark:** Added without the owner asking

### 7.67 [analyser] direction: the 5-minute 100 EMA with the daily pivot
- **Code:** `analyser/report.py:44-45`; `analyser/direction.py:60-66`
  ```python
  44	    f = frames[an.direction_ema_timeframe]
  45	    key = f"ema_{an.direction_ema_periods}"
  analyser/direction.py:62	    if p == e == "above":
  analyser/direction.py:63	        return d(BUY_SIDE, said)
  analyser/direction.py:64	    if p == e == "below":
  analyser/direction.py:65	        return d(SELL_SIDE, said)
  ```
  `config/settings.toml:317-318`: `direction_ema_timeframe = "5m"`, `direction_ema_periods = 100`
- **DESIGN.md:** lines 56-58: "Buy side: price above the daily pivot and above the 5-minute 100 EMA." / "Sell side: ..." / "If they disagree, there is no clear direction."
- **Source:** agreed design (c803d53) lines 54-56, same words
- **Mark:** Owner's words, unchanged

### 7.68 [analyser] out of date: more than 10 minutes behind
- **Code:** `analyser/data_status.py:66,71`
  ```python
  66	    allowed = timedelta(minutes=settings.analyser.out_of_date_after_minutes)
  71	        if due is not None and (have is None or due - have > allowed):
  ```
  `config/settings.toml:322`: `out_of_date_after_minutes = 10`
- **DESIGN.md:** line 36: "whether its data is ready, warming up or out of date" (no number)
- **Source:** agreed design (c803d53) line 34, same words (no number); settings comment `config/settings.toml:321` "STARTING VALUE"; none found from the owner
- **Mark:** Added without the owner asking

### 7.69 The emerging trend's start point and extreme for the 30-pip move: close of the starting candle to the trend's furthest low/high
- **Code:** `analyser/states.py:454-455,308`
  ```python
  454	        self.start_price = f.c
  455	        self.extreme = f.l if d == DOWN else f.h
  308	            moved = self._pips(self.extreme, self.start_price) if self.extreme is not None else Decimal(0)
  ```
- **DESIGN.md:** line 51: "price has moved at least 30 pips since it started"
- **Source:** agreed design (c803d53) line 49, "price has moved at least 30 pips since it started" (how it is measured not given); none found for close-to-extreme
- **Mark:** Added without the owner asking

## 8. The trade manager's exits

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 34 | 0 | 17 | 0 | 51 |

### 8.1 The order of the steps on each bar (scheduled close, stop/lock, band, take profit, rejection)
- **Code:** `trade_manager/manager.py:231-277`
  ```python
  231	    if not first and bar.start >= t.close_at:                          # 1. the scheduled close
  233	    level = -t.stop_pips                                               # 2. the stop at IG, or the lock
  250	    if t.band_close > 0 and not t.half_done and band is not None:      # 3. the close at the opposite band
  268	    if best >= t.take_profit_pips:                                     # 4. the take profit at IG
  271	    if t.level_close and not first and t.news_direction != t.direction:   # 5. a rejection at a level against it
  ```
- **DESIGN.md:** line 224: "on each price bar in this order: the scheduled close (20:30, Friday 20:30, or 15 minutes before big news ...); the stop at IG or the slow grind's lock; the close at the opposite band ...; the take profit at IG; the close on a confirmed rejection at a level"
- **Source:** none for the order itself. Docstring `manager.py:5`: "in this order (as the research of 8 November 2026)". Owner asked only for matching closes: owner, 2026-11-08T08:33:41Z, PASTED, "a replay check that ... it closes every trade at the same time and price as the all-strategies research".
- **Mark:** Added without the owner asking

### 8.2 Stop counted before the take profit when both fall in one bar
- **Code:** `trade_manager/manager.py:239-249, 268`
  ```python
  239	    hit = worst <= level
  243	    if hit:
  249	        return finish(STOPPED_BY_IG, price, "the stop at IG")
  268	    if best >= t.take_profit_pips:                                     # 4. the take profit at IG
  ```
- **DESIGN.md:** none
- **Source:** owner, 2026-11-07T16:25:49Z, PASTED, "If a stop and a target are both reached inside one 5-minute candle, count the stop first."
- **Mark:** Owner's words, unchanged

### 8.3 A buy closes (and is stopped) on the sell price, a sell on the buy price
- **Code:** `trade_manager/manager.py:216-219`
  ```python
  216	    sell = t.direction == SELL
  217	    side = "buy" if sell else "sell"                                  # the price it closes on
  218	    g = lambda name: Decimal(getattr(bar, f"{side}_{name}"))          # noqa: E731
  219	    pips = lambda v: ((t.fill - v) if sell else (v - t.fill)) / ppp    # noqa: E731
  ```
- **DESIGN.md:** line 232: "Trades still open and close at IG's real buy or sell price as normal."
- **Source:** owner, 2026-11-07T16:20:21Z, TYPED, "At IG a sell is closed, and its stop triggered, on the buy (offer) price, and a buy on the sell (bid) price."
- **Mark:** Owner's words, unchanged

### 8.4 Closed at 20:30 UK every day: Bollinger bounce, range trade, slow grind, level reversal
- **Code:** `strategies/common.py:41-43, 172-176`
  ```python
  41	# Held overnight and closed at 20:30 UK on Friday only (owner, 7 November 2026); every other
  42	# strategy is closed at 20:30 UK every day.
  43	OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
  172	    for k in range(0, 8):
  173	        day = lt.date() + timedelta(days=k)
  174	        cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
  175	        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
  176	            return cut.astimezone(timezone.utc)
  ```
  `config/settings.toml:21`: `close_all_trades_at = "20:30"`
- **DESIGN.md:** line 258: "Any trade open at 20:30 is closed. Nothing held overnight. A trade opened just before 20:30 is simply closed at 20:30."; line 210 (slow grind) "or 20:30 UK, when any slow grind trade still open is closed, every day"; line 211 (level reversal) "or 20:30 UK ... every day"
- **Source:** agreed design (c803d53) line 199, "Any trade open at 20:30 is closed. Nothing held overnight."; owner, 2026-11-06T15:05:45Z, PASTED, "any open trade closed at 20:30; nothing held overnight"; slow grind: owner, 2026-11-08T05:01:05Z, TYPED, "closed at 20:30 UK every day, and no new trade from 20:30 to midnight UK"; level reversal: owner, 2026-11-08T05:48:07Z, PASTED, "New trades 06:00 to 20:30 UK, closed at 20:30"
- **Mark:** Owner's words, unchanged

### 8.5 EMA pullback and breakout: held overnight, closed at 20:30 UK on Friday only
- **Code:** `strategies/common.py:43, 175` (as 8.4: `strategy not in OWN_HOURS or day.weekday() == 4`)
- **DESIGN.md:** line 213: "or 20:30 UK on Friday, when any EMA pullback trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight)"; line 209 (breakout) same
- **Source:** EMA pullback: owner, 2026-11-07T16:00:31Z, PASTED, "It may be held overnight. It is not closed at 20:30, except on Friday: any EMA pullback trade still open at 20:30 UK on Friday is closed then."; repeated owner, 2026-11-07T16:53:46Z, PASTED, "it may be held overnight, and any trade still open at 20:30 UK on Friday is closed". Breakout: owner, 2026-11-07T19:24:52Z, PASTED, "It may be held overnight and through news, and is closed at 20:30 UK on Friday."
- **Mark:** Owner's words, unchanged

### 8.6 The scheduled close is made at the open of the first bar at or after its time, never in the entry bar
- **Code:** `trade_manager/manager.py:220, 231-232`
  ```python
  220	    first = t.bars == 0
  231	    if not first and bar.start >= t.close_at:                          # 1. the scheduled close
  232	        return finish(FORCED_CLOSE, g("open"), t.close_why)
  ```
  `trading/engine.py:276-277`: `if not self.replay:` / `mt.bars = 1   # opened at the market: every later price is after it`
- **DESIGN.md:** none (line 224 lists "the scheduled close" only)
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.7 Closed 15 minutes before big news (every strategy except EMA pullback, breakout, slow grind), or at 20:30 if that comes first
- **Code:** `strategies/common.py:44-45, 180-183`; `trade_manager/manager.py:187-191`
  ```python
  45	NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
  183	    return strategy not in NEWS_ALLOWED
  trade_manager/manager.py:187	    if closed_before_big_news(strategy):
  trade_manager/manager.py:188	        windows = big_news_windows(settings, pair, opened_at, close_at + timedelta(minutes=1), calendar)
  trade_manager/manager.py:189	        news = [w.close_open_trades_at for w in windows if w.close_open_trades_at > opened_at]
  trade_manager/manager.py:190	        if news and min(news) < close_at:
  trade_manager/manager.py:191	            close_at, why = min(news), "closed 15 minutes before big news"
  ```
  `news/calendar.py:123`: `close = timedelta(minutes=n.big_news_close_trades_before_minutes)`; `config/settings.toml:27`: `big_news_close_trades_before_minutes = 15`
- **DESIGN.md:** line 264: "Open trades closed 15 minutes before. This does not apply to the EMA pullback or the breakout (owner, 7 November 2026), or the slow grind (owner, 8 November 2026)"
- **Source:** agreed design (c803d53) line 200, "Open trades closed 15 minutes before."; owner, 2026-11-07T11:44:23Z, PASTED, "open trades closed 15 minutes before"; EMA pullback: owner, 2026-11-07T16:00:31Z, PASTED, "open trades are not closed before big news"; breakout: owner, 2026-11-07T19:24:52Z, PASTED, "held overnight and through news"; slow grind: owner, 2026-11-07T19:58:43Z, PASTED, "News as the EMA pullback: may open during the window, not closed before big news" (accepted owner, 2026-11-08T05:01:05Z, TYPED, "Everything else exactly as listed in your earlier reply")
- **Mark:** Owner's words, unchanged

### 8.8 Stop 12 pips for the Bollinger bounce and range trade (STOP_LOSS_PIPS)
- **Code:** `strategies/common.py:257`
  ```python
  257	    return sw.stop_loss_pips_ema_pullback if strategy == EMA_PULLBACK else sw.stop_loss_pips
  ```
  `.env:27`: `STOP_LOSS_PIPS=12`
- **DESIGN.md:** line 207: "a fixed 12 pips for every strategy except the EMA pullback, the breakout, the slow grind and the level reversal ... (`STOP_LOSS_PIPS=12`)"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "Put changes 1, 2 and 3 live exactly as tested: the 12-pip stop for the bounce, range trade and breakout" (was agreed design (c803d53) line 162, "a fixed 6 pips for every strategy")
- **Mark:** Owner's words, unchanged

### 8.9 EMA pullback stop 12 pips (STOP_LOSS_PIPS_EMA_PULLBACK)
- **Code:** `strategies/common.py:257` (above); `.env:28`: `STOP_LOSS_PIPS_EMA_PULLBACK=12`
- **DESIGN.md:** line 207: "The EMA pullback's stop is 12 pips (owner, 7 November 2026), its own switch in `.env` (`STOP_LOSS_PIPS_EMA_PULLBACK`)"
- **Source:** owner, 2026-11-07T15:36:57Z, PASTED, "EMA pullback stop loss is 12 pips. Add a separate .env setting for it, STOP_LOSS_PIPS_EMA_PULLBACK=12"
- **Mark:** Owner's words, unchanged

### 8.10 Breakout stop 12 pips
- **Code:** `strategies/common.py:253-254`
  ```python
  253	    if strategy == BREAKOUT:
  254	        return settings.breakout.stop_loss_pips
  ```
  `config/settings.toml:256`: `stop_loss_pips = 12`
- **DESIGN.md:** line 209: "a breakout trade runs until its 12-pip stop (owner, 10 November 2026)"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "the 12-pip stop for the bounce, range trade and breakout" (earlier owner, 2026-11-07T19:24:52Z, PASTED, "Stop loss 6 pips")
- **Mark:** Owner's words, unchanged

### 8.11 Slow grind stop 15 pips
- **Code:** `strategies/common.py:255-256`
  ```python
  255	    if strategy == SLOW_GRIND:
  256	        return settings.slow_grind.stop_loss_pips
  ```
  `config/settings.toml:205`: `stop_loss_pips = 15`
- **DESIGN.md:** line 210: "a slow grind trade runs until its 15-pip stop"
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "Stop 15 pips; take profit 20 pips, or 100 on a big-news day"; owner, 2026-11-08T05:01:05Z, TYPED, "switch the slow grind on with result 13's settings"
- **Mark:** Owner's words, unchanged

### 8.12 Level reversal stop 6 pips beyond the furthest point
- **Code:** `strategies/common.py:251-252, 265-267`
  ```python
  251	    if strategy == LEVEL_REVERSAL:
  252	        return settings.level_reversal.stop_beyond_furthest_pips
  265	    if idea.strategy != LEVEL_REVERSAL:
  266	        return None
  267	    return idea.context["stop_price"]
  ```
  `config/settings.toml:273`: `stop_beyond_furthest_pips = 6`
- **DESIGN.md:** line 207: "The level reversal's stop is not a distance from the entry: it is 6 pips beyond the furthest point price reached"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Stop 6 pips beyond the furthest point price reached; take profit 20 pips."
- **Mark:** Owner's words, unchanged

### 8.13 The stop is filled at the stop, or at the bar's open if the bar opened past it
- **Code:** `trade_manager/manager.py:244-246`
  ```python
  244	        at_open = pips(g("open"))
  245	        fill_pips = at_open if (not first and at_open <= level) else level
  246	        price = (t.fill - fill_pips * ppp) if sell else (t.fill + fill_pips * ppp)
  ```
- **DESIGN.md:** none
- **Source:** none found (live, IG's level replaces it: `manager.py:398-399`)
- **Mark:** Added without the owner asking

### 8.14 The entry-bar stop rule (in the entry bar the stop counts only if the bar opened past the entry price or closed beyond the stop)
- **Code:** `trade_manager/manager.py:240-242`
  ```python
  240	    if first:
  241	        opened_past = (bar.sell_open <= t.entry_price) if sell else (bar.sell_open >= t.entry_price)
  242	        hit = hit and (opened_past or pips(g("close")) <= -t.stop_pips)
  ```
- **DESIGN.md:** none
- **Source:** none for the rule's content; the owner refers to it by name after it existed: owner, 2026-11-07T17:35:26Z, PASTED, "with the same exits, limits and the entry-candle stop correction as the last run"; owner, 2026-11-07T19:37:07Z, PASTED, "include the entry-candle stop correction"
- **Mark:** Added without the owner asking

### 8.15 Slow grind profit lock 15/10
- **Code:** `strategies/common.py:196-198`; `trade_manager/manager.py:234-236, 247-248`
  ```python
  196	    if strategy != SLOW_GRIND:
  197	        return None
  198	    return settings.slow_grind.lock_from_pips, settings.slow_grind.lock_at_pips
  trade_manager/manager.py:234	    locked = t.lock is not None and t.best is not None and t.best >= t.lock[0]
  trade_manager/manager.py:235	    if locked:
  trade_manager/manager.py:236	        level = max(level, Decimal(t.lock[1]))
  trade_manager/manager.py:247	        if locked and level > 0:
  trade_manager/manager.py:248	            return finish(CLOSE, price, f"the profit lock: back to {t.lock[1]} pips up after {t.lock[0]} up")
  ```
  `config/settings.toml:209-210`: `lock_from_pips = 15` / `lock_at_pips = 10`
- **DESIGN.md:** line 210: "**Profit lock 15/10:** once the trade has been 15 pips in profit (`slow_grind.lock_from_pips`), it is closed if price comes back to 10 pips in profit"
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "once 15 pips up, close if it comes back to 10 up"; owner, 2026-11-08T08:33:41Z, PASTED, "the slow grind's 15/10 lock"; agreed design (c803d53) line 164, "once a trade is 15 pips in profit, the bot locks in 10 pips"
- **Mark:** Owner's words, unchanged

### 8.16 The lock counts only from the bar after the one that reached 15 pips
- **Code:** `trade_manager/manager.py:234, 278`
  ```python
  234	    locked = t.lock is not None and t.best is not None and t.best >= t.lock[0]
  278	    t.best = best if t.best is None else max(t.best, best)
  ```
- **DESIGN.md:** line 210: "the lock applies from the candle after the one that reached 15 pips"
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.17 No profit lock for any other strategy
- **Code:** `strategies/common.py:196-197` (above: `if strategy != SLOW_GRIND: return None`)
- **DESIGN.md:** line 212: "there is no profit lock except the slow grind's (above)"
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Profit lock: replace the 15-pip lock in DESIGN.md section 4 with: a trade runs until the analyser's state becomes consolidation"; then owner, 2026-11-07T14:50:02Z, TYPED, "Remove the consolidation exit for every strategy ... The other exits stay exactly as section 4 says"
- **Mark:** Owner's words, unchanged

### 8.18 Range trade closed in full at the opposite Bollinger band
- **Code:** `trade_manager/manager.py:201-202, 261-262`
  ```python
  201	    if strategy == RANGE_TRADE:
  202	        return Decimal(settings.range_trade.close_percent_at_opposite_band) / 100
  261	            if t.band_close >= 1:
  262	                return finish(CLOSE, price, "the opposite Bollinger band")
  ```
  `config/settings.toml:279`: `close_percent_at_opposite_band = 100`
- **DESIGN.md:** line 219: "the **range trade closes in full** when price reaches the opposite Bollinger band (50% before)"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "the range trade closed in full at the opposite band" (was agreed design (c803d53) line 170, "closes 50% at the opposite band")
- **Mark:** Owner's words, unchanged

### 8.19 Bollinger bounce closes half at the opposite band; the rest to its normal exits
- **Code:** `trade_manager/manager.py:203-204, 263-267`
  ```python
  203	    if strategy == BOLLINGER_BOUNCE:
  204	        return Decimal(settings.bounce.close_percent_at_opposite_band) / 100
  263	            share = t.band_close
  264	            d = Decision(HALF_CLOSE, price, pips(price), "the opposite Bollinger band", share, bar.start)
  265	            t.half_done, t.half_pips, t.half_share, t.state = True, d.pips, share, HALF_CLOSE
  ```
  `config/settings.toml:186`: `close_percent_at_opposite_band = 50`
- **DESIGN.md:** line 219: "the **Bollinger bounce closes half** there, and the rest goes on to its normal exits"
- **Source:** owner, 2026-11-11T08:05:29Z, TYPED, "the bounce closed half at the opposite band with the rest left to its normal exits"
- **Mark:** Owner's words, unchanged

### 8.20 The band used is the one at the last finished candle; "reached" judged on the sell price's high/low
- **Code:** `trade_manager/manager.py:251-253`; `trading/engine.py:180, 439`
  ```python
  251	        upper, lower = (Decimal(x) for x in band)
  252	        b = lower if sell else upper
  253	        reached = (bar.sell_low <= b) if sell else (bar.sell_high >= b)
  trading/engine.py:180	            band = (hist[i - 1][0].upper, hist[i - 1][0].lower) if i > 0 and hist[i - 1][0].upper is not None else None
  trading/engine.py:439	            band = (hist[-1][0].upper, hist[-1][0].lower) if hist and hist[-1][0].upper is not None else None
  ```
- **DESIGN.md:** line 219: "The band is the one at the last finished candle."
- **Source:** none for this detail; owner, 2026-11-11T08:05:29Z, TYPED, "Put changes 1, 2 and 3 live exactly as tested"
- **Mark:** Added without the owner asking

### 8.21 The band close's price (the open if opened past the band, else the band, a sell's band plus the spread, rounded to a tenth of a pip against the trade)
- **Code:** `trade_manager/manager.py:255-260`
  ```python
  255	            if (bar.sell_open <= b) if sell else (bar.sell_open >= b):
  256	                price = g("open")                                       # opened past it: closed at the open
  258	                step_ = ppp / 10                                        # IG quotes a tenth of a pip
  259	                raw = (b + (bar.buy_open - bar.sell_open)) if sell else b   # the band is a sell price
  260	                price = (raw / step_).to_integral_value(ROUND_CEILING if sell else ROUND_FLOOR) * step_
  ```
- **DESIGN.md:** line 219: "the band on the side the trade closes on (a sell's band plus the spread), rounded to IG's tenth of a pip against the trade, or the price itself if it is already past the band"
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.22 No band close for the EMA pullback, slow grind, breakout and level reversal
- **Code:** `trade_manager/manager.py:205`
  ```python
  205	    return Decimal(0)
  ```
- **DESIGN.md:** lines 209-213 (each one's exits list no band close)
- **Source:** EMA pullback: owner, 2026-11-07T16:00:31Z, PASTED, "Its other exits stay: the 12-pip stop and the 100-pip take profit"; breakout: owner, 2026-11-07T19:24:52Z, PASTED (stop, take profit, Friday 20:30, "No close on a rejection at a level"); slow grind: owner, 2026-11-07T19:58:43Z, PASTED (stop, take profit, lock); level reversal: owner, 2026-11-08T05:48:07Z, PASTED (stop, take profit, 20:30)
- **Mark:** Owner's words, unchanged

### 8.23 Only a range trade or a Bollinger bounce is closed by half, and only once
- **Code:** `orders/sender.py:79, 640-643`
  ```python
  79	HALF_CLOSED = (RANGE_TRADE, BOLLINGER_BOUNCE)
  640	            if half and (t.strategy not in HALF_CLOSED or t.half_closed):
  641	                return Result(False, "refused", reference, t.deal_id,
  642	                              reasons=["only a range trade or a Bollinger bounce is closed by half, and only once"])
  643	            size = (t.size / 2) if half else t.size
  ```
- **DESIGN.md:** line 275: "closes trades in full or by half (the Bollinger bounce at the opposite band; the range trade only if set to half)"
- **Source:** owner, 2026-11-08T07:32:34Z, PASTED, "It closes trades when the trade manager tells it to, in full or by half for the range trade"; owner, 2026-11-11T08:05:29Z, TYPED, "the bounce closed half at the opposite band"
- **Mark:** Owner's words, unchanged

### 8.24 Take profit 100 pips (TAKE_PROFIT_PIPS) for the Bollinger bounce and range trade
- **Code:** `strategies/common.py:230-231`
  ```python
  230	    if strategy not in (EMA_PULLBACK, SLOW_GRIND):
  231	        return settings.switches.take_profit_pips
  ```
  `.env:29`: `TAKE_PROFIT_PIPS=100`
- **DESIGN.md:** line 208: "a fixed 100 pips sent to IG as a safety net, for every strategy except the EMA pullback, the breakout and the slow grind. A switch in `.env` (`TAKE_PROFIT_PIPS`)"
- **Source:** agreed design (c803d53) line 163, "a fixed 100 pips sent to IG as a safety net"; owner, 2026-11-07T09:39:16Z, TYPED, "Move the stop loss (6 pips) and take profit sent to IG (100 pips) ... into .env, as STOP_LOSS_PIPS and TAKE_PROFIT_PIPS"
- **Mark:** Owner's words, unchanged

### 8.25 EMA pullback take profit 30 pips
- **Code:** `strategies/common.py:236`
  ```python
  236	    return settings.ema_pullback.take_profit_pips if strategy == EMA_PULLBACK else settings.slow_grind.take_profit_pips
  ```
  `config/settings.toml:221`: `take_profit_pips = 30`
- **DESIGN.md:** line 208: "The EMA pullback's take profit is 30 pips (owner, 7 November 2026"
- **Source:** owner, 2026-11-07T16:53:46Z, PASTED, "12-pip stop and 30-pip take profit"
- **Mark:** Owner's words, unchanged

### 8.26 Slow grind take profit 20 pips
- **Code:** `strategies/common.py:236` (above); `config/settings.toml:206`: `take_profit_pips = 20`
- **DESIGN.md:** line 210: "its take profit at IG (20 pips"
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "Stop 15 pips; take profit 20 pips, or 100 on a big-news day"; owner, 2026-11-08T05:01:05Z, TYPED, "result 13's settings"
- **Mark:** Owner's words, unchanged

### 8.27 EMA pullback and slow grind: 100 pips for a trade opened on a UK day with big news for the pair
- **Code:** `strategies/common.py:208-211, 234-235`
  ```python
  208	    day = t.astimezone(uk).date()
  211	    return any(start <= w.release_utc < end for w in big_news_windows(settings, pair, start, end, calendar))
  234	    if opened is not None and pair is not None and big_news_day(settings, pair, opened, calendar):
  235	        return settings.switches.take_profit_pips
  ```
- **DESIGN.md:** line 208: "an EMA pullback or slow grind trade opened on a day with big news for the pair ... gets the 100 pips of `TAKE_PROFIT_PIPS`"
- **Source:** EMA pullback: owner, 2026-11-07T17:09:43Z, TYPED, "Every EMA pullback trade opened on a day with big news for the pair gets the 100-pip take profit from TAKE_PROFIT_PIPS instead of 30."; slow grind: owner, 2026-11-07T19:58:43Z, PASTED, "or 100 on a big-news day"
- **Mark:** Owner's words, unchanged

### 8.28 EMA pullback and slow grind: 100 pips in the trend day's direction on a trend day
- **Code:** `strategies/common.py:232-233`
  ```python
  232	    if trend_day is not None and direction == {"down": SELL, "up": BUY}.get(trend_day):
  233	        return settings.switches.take_profit_pips
  ```
- **DESIGN.md:** line 70: "on a trend day, an EMA pullback or slow grind trade in the trend day's direction ... gets the 100-pip take profit of `TAKE_PROFIT_PIPS`"
- **Source:** owner, 2026-11-08T06:31:08Z, PASTED, "On a trend day, any EMA pullback or slow grind trade going in the trend day's direction (back towards the monthly pivot) gets the 100-pip take profit from TAKE_PROFIT_PIPS instead of its usual take profit."
- **Mark:** Owner's words, unchanged

### 8.29 Breakout take profit 50 pips on any day
- **Code:** `strategies/common.py:226-227`
  ```python
  226	    if strategy == BREAKOUT:
  227	        return settings.breakout.take_profit_pips
  ```
  `config/settings.toml:257`: `take_profit_pips = 50`
- **DESIGN.md:** line 208: "The breakout's is 50 pips (`breakout.take_profit_pips`) ... on any day"
- **Source:** owner, 2026-11-07T19:24:52Z, PASTED, "Stop loss 6 pips, take profit 50 pips (breakout.stop_loss_pips = 6, breakout.take_profit_pips = 50)"
- **Mark:** Owner's words, unchanged

### 8.30 Level reversal take profit 20 pips on any day
- **Code:** `strategies/common.py:228-229`
  ```python
  228	    if strategy == LEVEL_REVERSAL:
  229	        return settings.level_reversal.take_profit_pips
  ```
  `config/settings.toml:274`: `take_profit_pips = 20`
- **DESIGN.md:** line 208: "the level reversal's 20 pips (owner, 8 November 2026; `level_reversal.take_profit_pips`), on any day"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "Stop 6 pips beyond the furthest point price reached; take profit 20 pips."
- **Mark:** Owner's words, unchanged

### 8.31 Close on a confirmed rejection at a level against the trade: Bollinger bounce and range trade only
- **Code:** `strategies/common.py:46-47, 186-189`; `trade_manager/manager.py:271-277`
  ```python
  47	NO_LEVEL_CLOSE = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  189	    return strategy not in NO_LEVEL_CLOSE
  trade_manager/manager.py:272	        against = BUY if sell else SELL
  trade_manager/manager.py:273	        got = [r for r in rejections if r.direction == against]
  trade_manager/manager.py:277	            return finish(CLOSE, price, f"a confirmed rejection at a level: {r.levels}")
  ```
- **DESIGN.md:** line 214: "If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open"; lines 209-213 (not for EMA pullback, breakout, slow grind, level reversal)
- **Source:** agreed design (c803d53) line 165, "If price is rejected at the level against the trade, the trade closes"; exemptions: owner, 2026-11-07T15:36:57Z, PASTED, "The close on a rejection at a level does not apply to it" (EMA pullback); owner, 2026-11-07T19:24:52Z, PASTED, "No close on a rejection at a level." (breakout); owner, 2026-11-07T19:58:43Z, PASTED, "No close on a rejection at a level." (slow grind); owner, 2026-11-08T05:48:07Z, PASTED, "no close on a rejection at a level" (level reversal)
- **Mark:** Owner's words, unchanged

### 8.32 The rejection close applies only from the bar after the entry bar
- **Code:** `trade_manager/manager.py:271`
  ```python
  271	    if t.level_close and not first and t.news_direction != t.direction:   # 5. a rejection at a level against it
  ```
- **DESIGN.md:** line 224: "the close on a confirmed rejection at a level (from the bar after the entry bar"
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.33 The rejection close is at the rejection's trigger (the break past the confirmation candle), on the closing side
- **Code:** `trade_manager/manager.py:275-276`
  ```python
  275	            r = got[0]
  276	            price = r.price + (bar.buy_open - bar.sell_open) if sell else r.price
  ```
- **DESIGN.md:** line 214: "the trade closes at the same moment a bounce the other way would open: when the live price breaks past the confirmation candle"
- **Source:** agreed design (c803d53) line 165, "when the live price breaks past the confirmation candle"
- **Mark:** Owner's words, unchanged

### 8.34 Only rejections at levels that count (not the Bollinger band alone; the reversal watch windows) close a trade
- **Code:** `trading/engine.py:66-71`
  ```python
  66	    for e in watcher.events:
  67	        if e.version == "bounce" and e.kind == "trigger" and e.time == at:
  68	            st = watcher.setups[e.setup - 1]
  69	            levels = [p for p in st.pierced if "Bollinger" not in p["what"]]
  70	            if levels and st.counts:
  ```
- **DESIGN.md:** line 216: "In those windows a rejection at any level counts; outside them, only at levels where several line up."
- **Source:** agreed design (c803d53) lines 165, 167, "If price is rejected at the level against the trade"; "In those windows a rejection at any level counts; outside them, only at levels where several line up."
- **Mark:** Owner's words, unchanged

### 8.35 The expected news direction takes precedence: no rejection close for a trade in the day's expected news direction
- **Code:** `trade_manager/manager.py:271` (above: `t.news_direction != t.direction`); `manager.py:408`: `now_watching = against in watching and t.news_direction != t.direction`
- **DESIGN.md:** line 67: "The expected news direction takes precedence: a trade in that direction is kept open through rejections at levels."; line 218
- **Source:** agreed design (c803d53) line 64, "The expected news direction takes precedence: a trade in that direction is kept open through rejections at levels."; owner, 2026-11-08T08:33:41Z, PASTED, "with the expected news direction taking precedence on big-news days as section 4 says"
- **Mark:** Owner's words, unchanged

### 8.36 The day's expected news direction is that of the first big-release time of the UK day that has one
- **Code:** `trade_manager/manager.py:172-175`
  ```python
  172	    for td in time_directions(settings, pair, start, end, calendar):
  173	        if td.direction in ("up", "down"):
  174	            return BUY if td.direction == "up" else SELL
  175	    return None
  ```
- **DESIGN.md:** none (line 65: "use that as the expected direction for the day")
- **Source:** none for choosing the first time; agreed design (c803d53) line 63, "use that as the expected direction for the day"
- **Mark:** Added without the owner asking

### 8.37 "Watching a level": while the analyser has a rejection setup running against the trade at a level that counts
- **Code:** `trade_manager/manager.py:406-412`; `trading/engine.py:77-79`
  ```python
  406	            if t.open and t.level_close:
  407	                against = BUY if t.direction == SELL else SELL
  408	                now_watching = against in watching and t.news_direction != t.direction
  trading/engine.py:77	    return {st.direction for st in watcher.setups
  trading/engine.py:78	            if st.version == "bounce" and st.status == "running" and st.counts
  trading/engine.py:79	            and any("Bollinger" not in p["what"] for p in st.pierced)}
  ```
- **DESIGN.md:** line 221: "each open trade is always in one of: hold, watching a level, half close, close, forced close (news or 20:30), stopped by IG, take profit hit at IG."
- **Source:** the state's name only: agreed design (c803d53) line 171, "hold, watching a level, half close"; owner, 2026-11-08T08:50:50Z, PASTED, "including the "watching a level" state the trade manager still needs". No source for its definition.
- **Mark:** Added without the owner asking

### 8.38 No close on a change of market state, nor on distance travelled
- **Code:** `trade_manager/manager.py:208-209` (step() takes no market state)
  ```python
  208	def step(settings: Any, t: ManagedTrade, bar: Bar, band: tuple[Decimal, Decimal] | None = None,
  209	         rejections: list[Rejection] = ()) -> list[Decision]:
  ```
- **DESIGN.md:** lines 215, 217: "**Distance travelled** does not force a close on its own."; "**A change of market state** does not close a trade on its own"
- **Source:** agreed design (c803d53) lines 166, 168 (same words); owner, 2026-11-07T14:50:02Z, TYPED, "Remove the consolidation exit for every strategy"
- **Mark:** Owner's words, unchanged

### 8.39 A valid Bollinger bounce against open trend trades closes every trade open the other way (close_now)
- **Code:** `trading/engine.py:249-251`; `trade_manager/manager.py:428-429`
  ```python
  249	        for mt in list(self.manager.trades.values()):
  250	            if mt.open and mt.direction != idea.direction and mt.reference != r.reference:
  251	                self.manager.close_now(mt.reference, price, why, opened_at)
  trade_manager/manager.py:428	        d = Decision(CLOSE, price, pips, why, (1 - t.half_share) if t.half_done else Decimal(1), at)
  trade_manager/manager.py:429	        sent = self.sender.close(reference, half=False, why=why, price=price)
  ```
- **DESIGN.md:** line 220: "a Bollinger bounce that opens against open trend trades, at a significant level with price moving slowly, closes every trade open in the opposite direction at that moment"
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "Then it opens, and closes every open trade in the opposite direction at that moment."
- **Mark:** Owner's words, unchanged

### 8.40 A close counts only once IG confirms it; refused or unclear leaves the trade open and it is tried again
- **Code:** `trade_manager/manager.py:373-383`
  ```python
  373	                    if self.ig_confirms and not getattr(sent, "ok", False):
  374	                        # never closed unless IG confirms it: the trade stays as it was, the close is tried again
  375	                        self._put_back(t, before, kept)
  376	                        t.close_attempts += 1
  377	                        t.retry_close_at = self.now() + timedelta(seconds=self.s.orders.close_retry_seconds)
  ```
- **DESIGN.md:** line 276: "(a) a trade is closed in the records only once IG confirms the close: a refused or unclear close leaves it open, alerts the owner at once with IG's error and is tried again"
- **Source:** owner, 2026-11-10T22:18:34Z, PASTED, "A trade must never be recorded as closed unless IG confirms the close. If IG refuses a close, keep the trade as open, retry, and send me a Telegram alert straight away with IG's error."; agreed design (c803d53) line 207, "a trade only counts as open, closed or half closed once IG confirms it"
- **Mark:** Owner's words, unchanged

### 8.41 A refused close is tried again after 30 seconds
- **Code:** `trade_manager/manager.py:362-365, 377`
  ```python
  362	                if d.kind in BOT_CLOSES and self.ig_confirms and t.retry_close_at is not None \
  363	                        and self.now() < t.retry_close_at:
  364	                    self._put_back(t, before, kept)     # a close IG did not confirm: not tried again yet
  377	                        t.retry_close_at = self.now() + timedelta(seconds=self.s.orders.close_retry_seconds)
  ```
  `config/settings.toml:90`: `close_retry_seconds = 30`
- **DESIGN.md:** line 276: "is tried again every `orders.close_retry_seconds`"
- **Source:** owner asked for a retry, no interval: owner, 2026-11-10T22:18:34Z, PASTED, "keep the trade as open, retry". The 30 appeared in commit addf1b8 (2026-11-10 22:36).
- **Mark:** Added without the owner asking

### 8.42 close_now not confirmed by IG: its scheduled close is brought forward to now
- **Code:** `trade_manager/manager.py:433-436`
  ```python
  433	        if self.ig_confirms and not getattr(sent, "ok", False):
  434	            t.close_attempts += 1
  435	            t.retry_close_at = self.now() + timedelta(seconds=self.s.orders.close_retry_seconds)
  436	            t.close_at, t.close_why = min(t.close_at, self.now()), why
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.43 IG's stop and take profit are never sent as closes; live, they close the trade only once IG confirms it
- **Code:** `trade_manager/manager.py:391-403`
  ```python
  391	                elif d.kind in IG_CLOSES and hasattr(self.sender, "closed_at_ig"):
  392	                    sent = self.sender.closed_at_ig(t.reference, d.kind, d.price)
  400	                    if self.ig_confirms and not getattr(sent, "ok", False):
  401	                        t.expected_at_ig = (d.kind, d.price, d)
  402	                        t.state, t.decisions = HOLD if not t.half_done else HALF_CLOSE, t.decisions[:-1]
  ```
- **DESIGN.md:** line 224: "records IG's stop and take profit without sending anything for them"; line 271
- **Source:** agreed design (c803d53) lines 162-163, "sent to IG"; line 207, "a trade only counts as open, closed or half closed once IG confirms it"
- **Mark:** Owner's words, unchanged

### 8.44 A trade IG has already closed ("gone at IG") is finished as closed at IG, at IG's level and time
- **Code:** `trade_manager/manager.py:368-371, 469-481`
  ```python
  368	                    if self.ig_confirms and getattr(sent, "what", "") in GONE:
  369	                        self._put_back(t, before, kept)
  370	                        self._closed_at_ig(t, sent)
  473	        level = getattr(found, "level", None)
  476	        kind = CLOSED_BY_OWNER if getattr(found, "what", "") == CLOSED_BY_OWNER else CLOSED_AT_IG
  ```
- **DESIGN.md:** line 276: "(b) after a refused close IG is asked whether the position still exists, and one IG had already closed is recorded with IG's own close level and time from IG's activity"
- **Source:** owner asked to be alerted: owner, 2026-11-10T22:18:34Z, PASTED, "At start-up and regularly, compare the bot's open trades with IG's open positions, and alert me about any difference."; he later had past trades corrected: owner, 2026-11-11T06:19:43Z, TYPED, "Yes, correct those trades to IG's figures". No owner words ask for the automatic finish.
- **Mark:** Added without the owner asking

### 8.45 Closed on IG's channel SYSTEM, not at the stop or take profit, means closed by the owner (kept apart)
- **Code:** `trade_manager/manager.py:68-71, 476`
  ```python
  68	# Live only: the owner closed it by hand at IG (IG's channel SYSTEM, not at the stop or take profit; owner,
  69	# 11 November 2026). Kept apart from the bot's own exits in the records, the dashboard and the summaries.
  70	CLOSED_BY_OWNER = "closed by owner"
  476	        kind = CLOSED_BY_OWNER if getattr(found, "what", "") == CLOSED_BY_OWNER else CLOSED_AT_IG
  ```
- **DESIGN.md:** line 277: "a trade IG shows closed on channel SYSTEM but not at its stop or take profit (at or beyond either counts as the stop or limit) was closed by the owner by hand"
- **Source:** owner, 2026-11-11T06:19:43Z, TYPED, "The six trades IG shows closed by "SYSTEM" (Monday 9 November at 15:21, and Tuesday 10 November at 17:12 and 17:56) were closed by me, by hand, so mark them as closed by the owner." (about those six trades; no owner words make it a general rule)
- **Mark:** Added without the owner asking

### 8.46 Each open trade's best pips, half close and watching are saved and restored after a restart
- **Code:** `trade_manager/manager.py:337-350`
  ```python
  342	        t.best = None if saved["best"] is None else Decimal(saved["best"])
  343	        t.bars = max(int(saved["bars"]), 1)
  344	        t.half_done = bool(saved["half_done"])
  347	        t.watching = bool(saved["watching"])
  ```
- **DESIGN.md:** line 24: "Each open trade's best price so far, half close and "watching a level" are saved by the trade manager and restored after a restart."
- **Source:** owner, 2026-11-08T09:37:37Z, PASTED, "save each open trade's best price reached so far, and restore it after a restart, so the slow grind's lock and anything else that depends on it carry on correctly."
- **Mark:** Owner's words, unchanged

### 8.47 hours.hold_overnight must be false
- **Code:** `config/settings_loader.py:292` (no other code reads it)
  ```python
  292	        "hold_overnight": _must_be(False),
  ```
  `config/settings.toml:22`: `hold_overnight = false`
- **DESIGN.md:** line 258: "Nothing held overnight."
- **Source:** agreed design (c803d53) line 199, "Nothing held overnight."; owner, 2026-11-06T15:05:45Z, PASTED, "nothing held overnight"
- **Mark:** Owner's words, unchanged

### 8.48 STOP_LOSS_PIPS and STOP_LOSS_PIPS_EMA_PULLBACK must be whole pips 1 to 100; TAKE_PROFIT_PIPS 1 to 1000
- **Code:** `config/switches.py:88-90`
  ```python
  88	    "STOP_LOSS_PIPS": ("stop_loss_pips", _pips(1, 100)),
  89	    "STOP_LOSS_PIPS_EMA_PULLBACK": ("stop_loss_pips_ema_pullback", _pips(1, 100)),
  90	    "TAKE_PROFIT_PIPS": ("take_profit_pips", _pips(1, 1000)),
  ```
- **DESIGN.md:** line 361: "checked at start-up"
- **Source:** owner asked for a check, no limits: owner, 2026-11-07T09:39:16Z, TYPED, "Check them at start-up like the other .env switches"
- **Mark:** Added without the owner asking

### 8.49 Band-close settings may only be 0, 50 or 100 (bounce) and 50 or 100 (range trade)
- **Code:** `config/settings_loader.py:384, 444`
  ```python
  384	        "close_percent_at_opposite_band": _whole_number_of(0, 50, 100),
  444	        "close_percent_at_opposite_band": _whole_number_of(50, 100),
  ```
- **DESIGN.md:** line 219: "each 50 or 100 (the bounce's may also be 0), since the order sender closes in full or by half only"
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.50 lock_at_pips must be smaller than lock_from_pips
- **Code:** `config/settings_loader.py:679-680`
  ```python
  679	    if sg["lock_at_pips"] >= sg["lock_from_pips"]:
  680	        raise SettingsError("Setting [slow_grind] lock_at_pips must be smaller than lock_from_pips.")
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 8.51 A close sent for an IG-confirmed half close in the same bar is kept when the rest of the bar is put back
- **Code:** `trade_manager/manager.py:460-467`
  ```python
  460	    def _put_back(cls, t: ManagedTrade, before: dict, kept: list[Decision]) -> None:
  461	        """The trade as it was before this bar, plus the half close IG confirmed in it (if any)."""
  465	        for d in kept:
  466	            t.half_done, t.half_pips, t.half_share, t.state = True, d.pips, d.part, HALF_CLOSE
  ```
- **DESIGN.md:** none
- **Source:** follows owner, 2026-11-10T22:18:34Z, PASTED, "A trade must never be recorded as closed unless IG confirms the close" (a confirmed half close stays recorded)
- **Mark:** Owner's words, unchanged

## 9. The safety rules

| Owner's words, unchanged | Changed from the owner's words | Added without the owner asking | No source found | Rules |
|---:|---:|---:|---:|---:|
| 44 | 1 | 10 | 0 | 55 |

### 9.1 New trades only from 06:00 to 20:30 UK (bounce, range trade, level reversal, breakout)
- **Code:** `strategies/common.py:150-153`
  ```python
  150	    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
  151	    sw = settings.switches
  152	    if not (sw.new_trades_from <= lt < sw.new_trades_until):
  153	        reasons.append(f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK")
  ```
  `.env:19-20`: `NEW_TRADES_FROM=06:00` / `NEW_TRADES_UNTIL=20:30`; `config/settings.toml:18-19` (comment: "new trades from 06:00 until 20:30 ... switches in .env")
- **DESIGN.md:** line 258: "new trades from 06:00 to 20:30 (switches in `.env`, section 13)"; lines 261-262
- **Source:** agreed design (c803d53) line 199, "new trades from 06:00 to 20:30"; owner, 2026-11-07T07:53:05Z, PASTED, "the trading hours (06:00 to 20:30 UK)" into .env; breakout: owner, 2026-11-07T19:24:52Z, PASTED, "New trades only from 06:00 to 20:30 UK"; level reversal: owner, 2026-11-08T05:48:07Z, PASTED, "New trades 06:00 to 20:30 UK"
- **Mark:** Owner's words, unchanged

### 9.2 Times are UK time (Europe/London)
- **Code:** `config/settings.toml:20`: `timezone = "Europe/London"`; used at `strategies/common.py:128`: `tz = settings.hours.timezone`
- **DESIGN.md:** line 258: "Trading hours (UK clock time)"
- **Source:** owner, 2026-11-06T15:05:45Z, PASTED, "Times are UK time (Europe/London, so GMT in winter and BST in summer)."
- **Mark:** Owner's words, unchanged

### 9.3 No new trade while the market is closed (every strategy)
- **Code:** `strategies/common.py:125-127`
  ```python
  125	    hours = MarketHours(settings.market_hours)
  126	    if not hours.is_open(t):
  127	        reasons.append("the market is closed")
  ```
- **DESIGN.md:** line 259: "the EMA pullback may open at any time the market is open"
- **Source:** owner, 2026-11-07T16:53:46Z, PASTED, "it may open at any time the market is open"
- **Mark:** Owner's words, unchanged

### 9.4 EMA pullback: any time the market is open, big-news windows included
- **Code:** `strategies/common.py:144-149`
  ```python
  144	    if strategy == EMA_PULLBACK:
  145	        lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)
  146	        if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
  149	        return reasons
  ```
- **DESIGN.md:** line 259: "the EMA pullback may open at any time the market is open, not only 06:00 to 20:30"; line 264
- **Source:** owner, 2026-11-07T16:53:46Z, PASTED, "it may open at any time the market is open; ... it may open during a big-news window and is not closed before big news"
- **Mark:** Owner's words, unchanged

### 9.5 EMA pullback: no new trade from 20:30 UK on Friday
- **Code:** `strategies/common.py:146-148`
  ```python
  146	        if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
  147	            reasons.append(f"after {settings.hours.close_all_trades_at:%H:%M} UK on Friday: "
  148	                           f"no {strategy} trade is held over the weekend")
  ```
- **DESIGN.md:** line 259: "except after 20:30 UK on Friday: no new EMA pullback trade opens then"
- **Source:** owner, 2026-11-07T17:03:03Z, PASTED, "No new EMA pullback trade opens after 20:30 UK on Friday, so none is ever held over the weekend."
- **Mark:** Owner's words, unchanged

### 9.6 Slow grind: any time the market is open, big-news windows included, except 20:30 UK to midnight
- **Code:** `strategies/common.py:129-134, 143`
  ```python
  129	    if strategy == SLOW_GRIND:
  133	        if lt >= settings.hours.close_all_trades_at:
  134	            reasons.append(f"from {settings.hours.close_all_trades_at:%H:%M} UK to midnight: no new {strategy} trade")
  143	        return reasons
  ```
- **DESIGN.md:** line 260: "the slow grind may open at any time the market is open ... except: from 20:30 UK to midnight every day"
- **Source:** owner, 2026-11-08T05:01:05Z, TYPED, "holding rule 2: closed at 20:30 UK every day, and no new trade from 20:30 to midnight UK"; owner, 2026-11-07T19:58:43Z, PASTED, "Opens at any time the market is open ... News as the EMA pullback: may open during the window"
- **Mark:** Owner's words, unchanged

### 9.7 Slow grind: none in the first 15 minutes after the week opens
- **Code:** `strategies/common.py:138-142`
  ```python
  138	        if hours.is_open(t):
  139	            opened = hours.session(t)[0]
  140	            if t < opened + timedelta(minutes=sg.week_open_no_new_trades_minutes):
  ```
  `config/settings.toml:214`: `week_open_no_new_trades_minutes = 15`
- **DESIGN.md:** line 260: "in the first 15 minutes after the market opens on Sunday"
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "except the first 15 minutes after the Sunday open, 21:55 to 22:15 UK"; accepted owner, 2026-11-08T05:01:05Z, TYPED, "Everything else exactly as listed in your earlier reply"
- **Mark:** Owner's words, unchanged

### 9.8 Slow grind: none from 21:55 to 22:15 UK
- **Code:** `strategies/common.py:135-137`
  ```python
  135	        if sg.rollover_no_new_trades_from <= lt < sg.rollover_no_new_trades_until:
  ```
  `config/settings.toml:215-216`: `rollover_no_new_trades_from = "21:55"` / `rollover_no_new_trades_until = "22:15"`
- **DESIGN.md:** line 260: "and from 21:55 to 22:15 UK"
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "21:55 to 22:15 UK"
- **Mark:** Owner's words, unchanged

### 9.9 Big news: no new trade from 15 minutes before to 30 minutes after (bounce, range trade, level reversal)
- **Code:** `strategies/common.py:156-158`; `news/calendar.py:121-122, 152`
  ```python
  156	    windows = no_new_trades(settings, pair, t, calendar)
  157	    if windows:
  158	        reasons.append("in a big-news window: " + ", ".join(sorted({w.event for w in windows})))
  news/calendar.py:121	    before = timedelta(minutes=n.big_news_no_new_trades_before_minutes)
  news/calendar.py:122	    after = timedelta(minutes=n.big_news_no_new_trades_after_minutes)
  news/calendar.py:152	            if w.no_new_trades_from <= t < w.no_new_trades_until]
  ```
  `config/settings.toml:25-26`: `big_news_no_new_trades_before_minutes = 15` / `big_news_no_new_trades_after_minutes = 30`
- **DESIGN.md:** line 264: "Big news: no new trades from 15 minutes before to 30 minutes after."; line 261 (level reversal)
- **Source:** agreed design (c803d53) line 200, "no new trades from 15 minutes before to 30 minutes after"; owner, 2026-11-07T11:44:23Z, PASTED, same words
- **Mark:** Owner's words, unchanged

### 9.10 Breakout: may open in a big-news window
- **Code:** `strategies/common.py:154-155`
  ```python
  154	    if strategy == BREAKOUT:
  155	        return reasons
  ```
- **DESIGN.md:** line 262: "it may open during a big-news window"
- **Source:** owner, 2026-11-07T17:48:56Z, PASTED, "Hours, news and the Friday rules as for the EMA pullback."; owner, 2026-11-07T19:24:52Z, PASTED, "It may be held overnight and through news"
- **Mark:** Owner's words, unchanged

### 9.11 Only big news counts; medium and small news ignored
- **Code:** `news/calendar.py:138-139`
  ```python
  138	        if m.tier != BIG:
  139	            continue
  ```
  `config/settings.toml:28`: `ignore_medium_and_small_news = true` (read only by the loader, `config/settings_loader.py:298`)
- **DESIGN.md:** line 264: "Medium and small news ignored."
- **Source:** agreed design (c803d53) line 200, "Medium and small news ignored."
- **Mark:** Owner's words, unchanged

### 9.12 Which releases are big: 161's table, applied only to Finnhub's "high" impact releases
- **Code:** `news/calendar.py:135` (`classify(rows, settings, cur, e["event"], e.get("impact"), ...)`); `config/settings.toml:56`: `table_impacts = ["high"]`
- **DESIGN.md:** line 264: "Which releases count as big comes from AutoBot's own small, medium and big table (built: the owner's table from AutoBot 161 ...)"
- **Source:** owner, 2026-11-07T12:14:37Z, PASTED, "Replace the news part's tiers with the owner's table from AutoBot 161 ... Keep the same matching"; 161 (news_impact_table_161_README.md, "applied to any HIGH-impact event")
- **Mark:** Owner's words, unchanged

### 9.13 Missing or out-of-date news calendar: an alert, trading not blocked
- **Code:** `config/settings.toml:42-44`
  ```toml
  42	# The calendar is OUT OF DATE (a Telegram problem alert; trading is not blocked
  43	# by it) when the last good fetch is older than this many hours.
  44	out_of_date_hours = 24
  ```
- **DESIGN.md:** line 264: "If the news data is missing or out of date, alert Johnny rather than block trading indefinitely (built: a Telegram problem alert; trading is not blocked by it)."
- **Source:** agreed design (c803d53) line 200, "If the news data is missing or out of date, alert Johnny rather than block trading indefinitely."
- **Mark:** Owner's words, unchanged

### 9.14 The news-calendar numbers: out of date after 24 h; fetch every 6 h, retry after 60 min, checked every 5 min, alert at most every 6 h, 7 days back / 14 ahead, kept 90 days, 20 s timeout
- **Code:** `config/settings.toml:32-50`: `request_timeout_seconds = 20`, `refresh_hours = 6`, `retry_minutes = 60`, `fetch_days_back = 7`, `fetch_days_ahead = 14`, `keep_days = 90`, `out_of_date_hours = 24`, `check_minutes = 5`, `alert_every_hours = 6`
- **DESIGN.md:** none (line 264: "fetched a few times a day")
- **Source:** owner asked for settings, gave no values: owner, 2026-11-07T11:44:23Z, PASTED, "Fetch it at most a few times a day, never in a fast loop ... Make the timings settings."
- **Mark:** Added without the owner asking

### 9.15 Releases where a lower figure is good for the currency (Unemployment Rate, Jobless Claims, Claimant Count Change)
- **Code:** `config/settings.toml:60`: `lower_is_better = ["Unemployment Rate", "Jobless Claims", "Claimant Count Change"]`
- **DESIGN.md:** line 65: "work out whether the expected result is good or bad for the pound or the dollar"
- **Source:** agreed design (c803d53) line 63, "work out whether the expected result is good or bad for the pound or the dollar"; no owner source for the list
- **Mark:** Added without the owner asking

### 9.16 The strategy's .env switch must be on (checked at entry and again by the safety rules)
- **Code:** `strategies/common.py:276-277`; `safety/rules.py:196-197`
  ```python
  276	    if not getattr(settings.switches, SWITCH[strategy]):
  277	        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
  safety/rules.py:196	    if not getattr(settings.switches, SWITCH[idea.strategy]):
  safety/rules.py:197	        reasons.append(f"its switch STRATEGY_{SWITCH[idea.strategy].upper()} is off")
  ```
- **DESIGN.md:** line 361: "each strategy on or off (`STRATEGY_SLOW_GRIND` on, ...)"
- **Source:** owner, 2026-11-07T12:42:17Z, PASTED, "A strategy only looks for ideas when all of these allow it: its .env switch is on"; owner, 2026-11-08T06:55:27Z, PASTED, "the strategy's switch is on"
- **Mark:** Owner's words, unchanged

### 9.17 Range trade: ranging only, either way
- **Code:** `strategies/common.py:57`
  ```python
  57	    RANGE_TRADE: {RANGING: "any"},
  ```
- **DESIGN.md:** line 42: "Ranging | Range trade"
- **Source:** agreed design (c803d53) line 40, "Ranging | Range trade"
- **Mark:** Owner's words, unchanged

### 9.18 EMA pullback: emerging trend and trend, in the trend's direction only
- **Code:** `strategies/common.py:55, 281-287`
  ```python
  55	    EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
  281	    elif ok_in[state.state] in ("trend", "against"):
  282	        want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
  285	        if direction != want:
  ```
- **DESIGN.md:** lines 43-44: "EMA pullback, breakout (3.5), in the trend's direction only"
- **Source:** owner, 2026-11-07T16:53:46Z, PASTED, "it trades in a trend and in an emerging trend"; agreed design (c803d53) lines 41-42, "in the trend's direction only"
- **Mark:** Owner's words, unchanged

### 9.19 Slow grind: trend only, in the trend's direction
- **Code:** `strategies/common.py:54`
  ```python
  54	    SLOW_GRIND: {TREND: "trend"},                      # trend only (owner, 8 November 2026)
  ```
- **DESIGN.md:** line 43: "Not the slow grind (owner, 8 November 2026)"; line 44
- **Source:** owner, 2026-11-07T19:58:43Z, PASTED, "Trend only, in the trend's direction."; accepted owner, 2026-11-08T05:01:05Z, TYPED
- **Mark:** Owner's words, unchanged

### 9.20 Bollinger bounce: trend against the trend's direction only; possible reversal either way
- **Code:** `strategies/common.py:56, 283-284`
  ```python
  56	    BOLLINGER_BOUNCE: {TREND: "against", POSSIBLE_REVERSAL: "any"},
  283	        if ok_in[state.state] == "against":
  284	            want = {SELL: BUY, BUY: SELL}.get(want)
  ```
- **DESIGN.md:** line 44: "Bollinger band bounce against the trend's direction only (owner, 7 November 2026)"; line 45
- **Source:** owner, 2026-11-07T17:35:26Z, PASTED, version 3: "Possible reversal, plus emerging trend and trend but only against the trend's direction, and only in trend (not emerging trend)."; owner, 2026-11-07T17:38:00Z, TYPED, "Use version 3 for the bounce"
- **Mark:** Owner's words, unchanged

### 9.21 Breakout: emerging trend and trend, in the trend's direction only
- **Code:** `strategies/common.py:58`
  ```python
  58	    BREAKOUT: {EMERGING: "trend", TREND: "trend"},
  ```
- **DESIGN.md:** lines 43-44: "EMA pullback, breakout (3.5), in the trend's direction only"
- **Source:** owner names only the move into an emerging trend and the day's move: owner, 2026-11-07T19:24:52Z, PASTED, "It looks for a trade when the analyser moves into an emerging trend ... It only takes a breakout in the direction of the day's move so far". No owner words allow it in trend or require the trend's direction. Added in commit b2514d8.
- **Mark:** Added without the owner asking

### 9.22 Level reversal: every state except consolidation, either way
- **Code:** `strategies/common.py:59-60`
  ```python
  59	    # every state except consolidation, either way (owner, 8 November 2026)
  60	    LEVEL_REVERSAL: {RANGING: "any", EMERGING: "any", TREND: "any", POSSIBLE_REVERSAL: "any"},
  ```
- **DESIGN.md:** lines 42-46: "level reversal (3.6), either way"
- **Source:** owner, 2026-11-08T05:48:07Z, PASTED, "in any analyser state except consolidation"
- **Mark:** Owner's words, unchanged

### 9.23 Consolidation: no strategy
- **Code:** `strategies/common.py:279-280`
  ```python
  279	    if state.state not in ok_in:
  280	        reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
  ```
- **DESIGN.md:** line 46: "Consolidation | None (not even the level reversal)"
- **Source:** agreed design (c803d53) line 44, "Consolidation | None. Watch and wait for a break"
- **Mark:** Owner's words, unchanged

### 9.24 Direction rule: a buy needs buy side (above the daily pivot and the 5-minute 100 EMA), a sell needs sell side
- **Code:** `strategies/common.py:274, 288-290`
  ```python
  274	    rule = decide(price, "the price", pivot, ema100, "5m 100 EMA", ema100 is not None)
  288	    need = BUY_SIDE if direction == BUY else SELL_SIDE
  289	    if rule.side != need and strategy not in NO_DIRECTION_RULE:
  290	        reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
  ```
- **DESIGN.md:** lines 56-58: "**Buy side:** price above the daily pivot and above the 5-minute 100 EMA. ... If they disagree, there is no clear direction."
- **Source:** agreed design (c803d53) lines 54-56 (same words)
- **Mark:** Owner's words, unchanged

### 9.25 The direction rule does not apply to the range trade, Bollinger bounce, breakout, slow grind
- **Code:** `strategies/common.py:48-49`
  ```python
  49	NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
  ```
- **DESIGN.md:** line 59: "except the range trade, the Bollinger band bounce and the breakout (owner, 7 November 2026) and the slow grind ..."
- **Source:** range trade: owner, 2026-11-07T14:41:12Z, TYPED, "the direction rule applies to every strategy except the range trade"; bounce: owner, 2026-11-07T17:48:56Z, PASTED, "The direction rule does not apply to the Bollinger bounce at all, in any state."; breakout: owner, 2026-11-07T19:24:52Z, PASTED, "The direction rule does not apply to it."; slow grind: owner, 2026-11-07T19:58:43Z, PASTED, "No direction filter"
- **Mark:** Owner's words, unchanged

### 9.26 The direction rule does not apply to the level reversal
- **Code:** `strategies/common.py:49` (above, `LEVEL_REVERSAL` in `NO_DIRECTION_RULE`)
- **DESIGN.md:** line 59: "and the slow grind and the level reversal (owner, 8 November 2026), which it does not apply to in any state"
- **Source:** agreed design (c803d53) line 57, "This applies to every strategy". The level reversal decision does not mention it: owner, 2026-11-08T05:48:07Z, PASTED, "It trades rejections at round 00 numbers, S2 and R2 only, in any analyser state except consolidation ... Entry when price breaks past the confirmation candle, as in the research."
- **Mark:** Changed from the owner's words. **Owner:** "This applies to every strategy" (no exemption for the level reversal) / **Code:** the level reversal is exempt.

### 9.27 Checks made at entry only: the state after the last finished candle, the direction rule at the entry price
- **Code:** `strategies/common.py:297`
  ```python
  297	    reasons, rule = allowed(settings, c.strategy, c.direction, c.entry_price, state, pivot, ema100)
  ```
- **DESIGN.md:** none directly (docstring `strategies/common.py:5-6`: "checked at entry only, owner 7 November 2026")
- **Source:** owner, 2026-11-07T13:35:04Z, PASTED, "Remove the check at setup start. The switch, state and direction checks apply at entry only, as before."
- **Mark:** Owner's words, unchanged

### 9.28 The pause switch blocks every new trade; open trades still run
- **Code:** `safety/rules.py:192-193`; `trading/engine.py:257, 266`
  ```python
  192	    if paused:
  193	        reasons.append("the pause switch is on: no new trades")
  trading/engine.py:257	        paused = Path(self.s.trading.pause_file).exists()
  trading/engine.py:266	        r = self.sender.place(idea, paused=self._paused(), trend_day=td, calendar=self.calendar, day=day)
  ```
  `config/settings.toml:106`: `pause_file = "/opt/autobot/data/control/pause_new_trades"`
- **DESIGN.md:** line 313: "while the file `trading.pause_file` exists no new trade is sent; open trades are still run"
- **Source:** agreed design (c803d53) line 232, "one switch labelled "pause new trades" (open trades are still managed while paused)"; owner, 2026-11-08T06:55:27Z, PASTED, "the pause switch, which blocks every new trade when on"
- **Mark:** Owner's words, unchanged

### 9.29 TRADING=off: everything runs and is recorded, nothing is sent to IG
- **Code:** `trading/engine.py:98`
  ```python
  98	        self.sender = OrderSender(settings, client, alerts, now=now, quote=quote, paper=not trading_on, **kw)
  ```
  `orders/sender.py:511-512`: `if self.paper:` / `return self._paper_open(ref, idea)`
- **DESIGN.md:** line 361: "the master switch `TRADING` (off: everything runs and is recorded, but no order is sent to IG)"
- **Source:** owner, 2026-11-08T08:50:50Z, PASTED, "Add a master switch in .env, TRADING=off ... While it is off, everything runs and is recorded, but no order is ever sent to IG."
- **Mark:** Owner's words, unchanged

### 9.30 One trade open at a time per strategy (range trade, slow grind, breakout, level reversal)
- **Code:** `safety/rules.py:114-116`
  ```python
  114	        elif len(mine) >= lim.max_open_trades_per_strategy:
  115	            out.append(f"{idea.strategy} already has {len(mine)} trade(s) open "
  ```
  `config/settings.toml:65`: `max_open_trades_per_strategy = 1`
- **DESIGN.md:** line 250: "Trades open at once: 1 per strategy (the slow grind and the level reversal too: one trade of each at a time"
- **Source:** agreed design (c803d53) line 197, "Trades open at once: 1 per strategy"; owner, 2026-11-07T19:24:52Z, PASTED, "One breakout trade open at a time."; owner, 2026-11-07T19:58:43Z, PASTED, "One slow grind trade at a time."; owner, 2026-11-08T05:48:07Z, PASTED, "one at a time"
- **Mark:** Owner's words, unchanged

### 9.31 Bollinger bounce: one each way (two in all)
- **Code:** `safety/rules.py:106-113`
  ```python
  107	            same = [t for t in mine if t.direction == idea.direction]
  108	            most = lim.max_open_trades_per_strategy + lim.bollinger_bounce_extra_opposite_direction_trades
  109	            if len(same) >= lim.max_open_trades_per_strategy:
  112	            elif len(mine) >= most:
  ```
  `config/settings.toml:66`: `bollinger_bounce_extra_opposite_direction_trades = 1`
- **DESIGN.md:** line 250: "the bounce may also have 1 in the opposite direction"
- **Source:** agreed design (c803d53) line 197, "the bounce may also have 1 in the opposite direction"; owner, 2026-11-06T15:05:45Z, PASTED, "except the Bollinger band bounce, which may also have 1 in the opposite direction"
- **Mark:** Owner's words, unchanged

### 9.32 EMA pullback: no limit on its own trades
- **Code:** `safety/rules.py:104`
  ```python
  104	    if idea.strategy != EMA_PULLBACK:
  ```
- **DESIGN.md:** line 250: "The EMA pullback is not limited to one trade at a time"
- **Source:** owner, 2026-11-07T15:49:03Z, TYPED, "the EMA pullback is not limited to one trade at a time. It may have several trades open at once, each managed on its own."
- **Mark:** Owner's words, unchanged

### 9.33 At most 5 trades open at once, not counting the EMA pullback's
- **Code:** `safety/rules.py:117-121`; `strategies/common.py:239-241`
  ```python
  117	    if counts_towards_most_at_once(idea.strategy):
  118	        counted = [t for t in open_trades if counts_towards_most_at_once(t.strategy)]
  119	        if len(counted) >= lim.max_open_trades:
  strategies/common.py:241	    return strategy != EMA_PULLBACK
  ```
  `config/settings.toml:68`: `max_open_trades = 5`
- **DESIGN.md:** line 250: "Most at once: 5. EMA pullback trades do not count towards that limit"
- **Source:** agreed design (c803d53) line 197, "Most at once: 5."; owner, 2026-11-07T16:53:46Z, PASTED, "it does not count towards the "most at once: 5" limit"
- **Mark:** Owner's words, unchanged

### 9.34 Size £10 a pip
- **Code:** `safety/rules.py:200-202`; `orders/sender.py:499`
  ```python
  200	    want = Decimal(settings.trade.size_gbp_per_pip)
  201	    if Decimal(order.size_gbp_per_pip) != want:
  202	        reasons.append(f"the size is £{order.size_gbp_per_pip} a pip, not £{want}")
  orders/sender.py:499	                "size": float(order.size_gbp_per_pip / self.ppp),
  ```
  `config/settings.toml:13`: `size_gbp_per_pip = 10`
- **DESIGN.md:** line 249: "Size: £10 per pip."
- **Source:** agreed design (c803d53) line 196, "Size: £10 per pip."; owner, 2026-11-06T15:05:45Z, PASTED, "size: £10 per pip"
- **Mark:** Owner's words, unchanged

### 9.35 Total risk at most £100,000
- **Code:** `safety/rules.py:130-134`
  ```python
  130	    most = Decimal(settings.safety.max_total_risk_gbp)
  131	    total = sum((t.risk_gbp for t in open_trades), Decimal(0)) + order.risk_gbp
  132	    if total > most:
  ```
  `config/settings.toml:125`: `max_total_risk_gbp = 100000`
- **DESIGN.md:** line 251: "may not be more than £100,000 (`safety.max_total_risk_gbp`), set so it is never reached"
- **Source:** owner, 2026-11-08T07:19:17Z, PASTED, "Total risk: set the limit to £100,000 across all open trades, so it is never reached. Keep the check, as a setting."
- **Mark:** Owner's words, unchanged

### 9.36 A trade's risk = its stop distance x its size (the level reversal's: entry to stop price)
- **Code:** `safety/rules.py:55-56, 87-91`
  ```python
  56	        return Decimal(self.stop_pips) * Decimal(self.size_gbp_per_pip)
  87	    sp = stop_price(settings, idea)
  89	        stop = abs(Decimal(idea.entry_price) - Decimal(sp)) / Decimal(settings.market.points_per_pip)
  91	        stop = Decimal(stop_loss_pips(settings, idea.strategy))
  ```
- **DESIGN.md:** line 251: "every open trade's risk (its stop distance x its size)"
- **Source:** owner gave the total only: owner, 2026-11-08T07:19:17Z, PASTED, "£100,000 across all open trades"; agreed design (c803d53) line 198, "Total risk across all open trades ... also checked"
- **Mark:** Added without the owner asking

### 9.37 Available funds at least £5,000
- **Code:** `safety/rules.py:139, 143-144`
  ```python
  139	    need = Decimal(settings.safety.margin_per_trade_gbp)
  143	    if funds.available < need:
  ```
  `config/settings.toml:129`: `margin_per_trade_gbp = 5000`
- **DESIGN.md:** line 252: "a new trade is allowed only if the account's available funds are at least the margin for one trade, £5,000 at £10 a pip"
- **Source:** owner, 2026-11-08T07:19:17Z, PASTED, "a new trade is only allowed if the account's available funds are at least the margin for one trade, a setting of £5,000 at £10 a pip"
- **Mark:** Owner's words, unchanged

### 9.38 Funds read from IG at start-up and whenever a trade opens or closes, never before each trade
- **Code:** `orders/sender.py:223, 414-417, 625`
  ```python
  223	            self._read_funds("start-up")
  416	            self.funds = AccountFunds.from_ig(self.client.account_balance(), self.now())
  625	                self._read_funds("a trade closed")
  ```
- **DESIGN.md:** line 252: "The available funds come from IG's account details, read at start-up and again whenever a trade opens or closes, never as an extra call before each trade."
- **Source:** owner, 2026-11-08T07:19:17Z, PASTED, "Take the available funds from IG's account details read at start-up and again whenever a trade opens or closes, never as an extra call before each trade."
- **Mark:** Owner's words, unchanged

### 9.39 Unknown funds refuse every new trade (and alert)
- **Code:** `safety/rules.py:140-142`; `orders/sender.py:419-422`
  ```python
  140	    if funds is None:
  141	        return ["the account's available funds are not known (read from IG at start-up and whenever a trade "
  orders/sender.py:419	            self.funds = None                                       # unknown funds: the safety rules refuse
  orders/sender.py:421	            self.alerts.problem("funds-not-read", f"The account's available funds could not be read from IG ({why}): {e}. "
  ```
- **DESIGN.md:** line 253: "the available funds (unknown funds refuse)"
- **Source:** none found
- **Mark:** Added without the owner asking

### 9.40 One view at a time (1): no reversal trade against a strong push
- **Code:** `safety/rules.py:179-180`
  ```python
  179	    if idea.state == TREND and idea.trend_type == STRONG_PUSH and td != idea.direction:
  180	        out.append(f"a reversal trade against a strong push ({idea.state_direction})")
  ```
- **DESIGN.md:** line 255: "**No reversal trade against a strong push:** refused while the analyser's state ... is a trend of the strong-push type in the other direction."
- **Source:** owner, 2026-11-09T11:35:32Z, PASTED, "No reversal trade against a strong push."
- **Mark:** Owner's words, unchanged

### 9.41 One view at a time (2): no reversal trade against the day's direction (big-news day, trend day, Monday after a Friday of 80 pips or more)
- **Code:** `safety/rules.py:181-182`
  ```python
  181	    for what in (day.against(idea.direction) if day is not None else []):
  182	        out.append(f"a reversal trade against the day's direction: {what}")
  ```
  `config/settings.toml:139`: `big_friday_move_pips = 80`
- **DESIGN.md:** line 256: "on a **big-news day** ... on a **trend day** ... on the **Monday after a Friday whose daily candle moved 80 pips or more**"
- **Source:** owner, 2026-11-09T11:35:32Z, PASTED, "No reversal trade against the day's direction on: a big-news day, in the expected news direction; a trend day, in the trend day's direction; and the Monday after a Friday whose daily candle moved 80 pips or more ... Make the 80 pips a setting"
- **Mark:** Owner's words, unchanged

### 9.42 A reversal trade: every Bollinger bounce, and a level reversal against the analyser's trend direction
- **Code:** `safety/rules.py:155-170`
  ```python
  155	    if idea.state in (EMERGING, TREND):
  156	        return "buy" if d == "up" else "sell"
  157	    if idea.state == POSSIBLE_REVERSAL:
  158	        return "sell" if d == "up" else "buy"
  165	    if idea.strategy == BOLLINGER_BOUNCE:
  166	        return True
  169	        return td is not None and td != idea.direction
  ```
- **DESIGN.md:** line 254: "A **reversal trade** is every Bollinger band bounce, and a level reversal that trades against the analyser's trend direction"
- **Source:** owner, 2026-11-09T11:35:32Z, PASTED, "A reversal trade is a Bollinger bounce, or a level reversal going against the analyser's trend direction, as in the research."
- **Mark:** Owner's words, unchanged

### 9.43 IG's minimum stop is not checked before a trade; only after IG refuses for the stop
- **Code:** `safety/rules.py:28-29`
  ```python
  28	IG's minimum stop distance is NOT checked before a trade (owner, 8 November 2026): the bot assumes each
  29	strategy's own stop meets it; safety/refusals.py deals with IG refusing a trade.
  ```
  `orders/sender.py:567`: `kind = on_refusal(self.s, reason, idea.strategy, order.stop_pips, Decimal(idea.entry_price),`
- **DESIGN.md:** line 273: "IG's dealing rules are not fetched before trades ... Only if IG refuses a trade because of its stop does the bot fetch IG's current minimum once"
- **Source:** owner, 2026-11-08T07:19:17Z, PASTED, "Minimum stop: do not fetch IG's dealing rules before trades ... Only if IG refuses a trade because of its stop does the bot fetch IG's current minimum once, record it, and send me a Telegram alert"
- **Mark:** Owner's words, unchanged

### 9.44 IG's refusal reasons taken as "the stop" and "lack of funds"
- **Code:** `config/settings.toml:130-133`
  ```toml
  131	# funds (design 7). STARTING VALUES: to be confirmed against IG when the order sender is built.
  132	ig_stop_refusal_reasons = ["ATTACHED_ORDER_LEVEL_ERROR"]
  133	ig_funds_refusal_reasons = ["INSUFFICIENT_FUNDS"]
  ```
- **DESIGN.md:** none
- **Source:** none found (commit 95608f4, 2026-11-08 07:26)
- **Mark:** Added without the owner asking

### 9.45 No order before the order sender's start-up (its own trades found at IG) is done
- **Code:** `orders/sender.py:472-474`
  ```python
  472	            if not self.ready:
  473	                self._record("safety refused", strategy=idea.strategy, reasons=["the order sender's start-up is not done"])
  474	                return Result(False, "safety refused", reasons=["the order sender's start-up is not done"])
  ```
- **DESIGN.md:** line 272: "on start-up, find the bot's own positions at IG using the saved deal references, take over managing them, and only then allow new trades"
- **Source:** agreed design (c803d53) line 208 (same words); owner, 2026-11-08T07:32:34Z, PASTED, "After a restart, it finds its own open trades at IG by their saved deal references, before any new trade is allowed."
- **Mark:** Owner's words, unchanged

### 9.46 Demo account only, on the price service's own IG login
- **Code:** `orders/sender.py:215-219`
  ```python
  215	                demo = self.s.ig.demo_base_url                  # settings refuse any other address
  216	                if getattr(self.client, "base_url", None) != demo:
  217	                    raise NotReady(f"the IG client is not on IG's demo address ({demo}): no orders")
  218	                if not getattr(self.client, "account_active", False):
  219	                    raise NotReady("the price service's IG login is not active: the order sender never logs in itself")
  ```
  `config/settings.toml:7`: `account_type = "demo"`
- **DESIGN.md:** line 275: "using the price service's IG login (never a second one), on the demo account only"
- **Source:** owner, 2026-11-08T07:32:34Z, PASTED, "It places market orders for GBPUSD on the demo account only ... It must use the price service's existing IG login and session, never a second login"
- **Mark:** Owner's words, unchanged

### 9.47 Level reversal refused if price is already past its stop price when sent
- **Code:** `orders/sender.py:460-464, 481-483`
  ```python
  460	        dist = (Decimal(sp) - bid) if idea.direction == "sell" else (offer - Decimal(sp))
  461	        dist = dist.quantize(Decimal("0.1"))
  462	        if dist <= 0:
  481	            if stop_points is None:
  482	                self._record("safety refused", strategy=idea.strategy, direction=idea.direction, reasons=[why])
  ```
- **DESIGN.md:** none
- **Source:** none found (owner asked only for the conversion: owner, 2026-11-08T07:56:47Z, PASTED, "convert the level reversal's stop price to a distance at the moment the order is sent")
- **Mark:** Added without the owner asking

### 9.48 Force open on every order; the stop always as stopDistance
- **Code:** `orders/sender.py:492, 500`
  ```python
  492	                "forceOpen": True,                                  # always
  500	                "stopDistance": float(stop_points),                 # always a distance, never stopLevel
  ```
- **DESIGN.md:** line 270: "**Force open** on every order"; line 275
- **Source:** agreed design (c803d53) line 206, "**Force open** on every order"; owner, 2026-11-08T07:56:47Z, PASTED, "Force open must always be true. The stop must always be sent as stopDistance, never stopLevel"
- **Mark:** Owner's words, unchanged

### 9.49 Never sent twice: a timeout or unclear answer is checked with IG, never resent
- **Code:** `orders/sender.py:516-520`
  ```python
  516	            except IGRequestError as e:
  517	                if e.status is not None and 400 <= e.status < 500:
  518	                    return self._refused(ref, idea, order, e.error_code or f"HTTP {e.status}")
  519	                self._record("unclear", reference=ref, error=str(e))
  520	                return self._settle_unclear(ref, idea, order)
  ```
- **DESIGN.md:** line 271: "On a timeout, check with IG before trying again, so nothing is ever opened or closed twice."
- **Source:** agreed design (c803d53) line 207 (same words); owner, 2026-11-08T07:32:34Z, PASTED, "It never sends the same trade twice."
- **Mark:** Owner's words, unchanged

### 9.50 Unclear answers checked 3 times, 2 seconds apart
- **Code:** `config/settings.toml:82-83`: `unclear_checks = 3` / `unclear_check_wait_seconds = 2` (comment line 81: "STARTING VALUES.")
- **DESIGN.md:** line 275: "(`orders.unclear_checks`)"
- **Source:** none found (commit 5e739e1, 2026-11-08 07:46)
- **Mark:** Added without the owner asking

### 9.51 IG's confirmation asked up to 5 times, 1 second apart, while IG answers 404
- **Code:** `orders/sender.py:438-447`
  ```python
  438	        for k in range(attempts):
  439	            if k:
  440	                self.sleep(self.o.confirm_wait_seconds)
  446	                if e.status != 404:
  ```
  `config/settings.toml:86-87`: `confirm_attempts = 5` / `confirm_wait_seconds = 1`
- **DESIGN.md:** line 275: "`GET /confirms/{reference}` with `VERSION: 1`, up to 5 times a second apart while IG answers 404"
- **Source:** owner, 2026-11-08T07:56:47Z, PASTED, "make the order sender match it exactly"; 161 (open_sb_now_for_new_bot_20261108.md, "**Retry:** up to 5 attempts, 1 s apart, on HTTP 404")
- **Mark:** Owner's words, unchanged

### 9.52 At most one trade per strategy and direction per candle (an idea already sent live is not sent again)
- **Code:** `trading/engine.py:186, 190, 464-467`
  ```python
  186	                sent_live = (idea.strategy, idea.direction, c.start) in self.fired
  190	                if idea.allowed and not sent_live:
  464	            key = (idea.strategy, idea.direction, p.start)
  465	            if not idea.allowed or key in self.fired:
  467	            self.fired.add(key)
  ```
- **DESIGN.md:** line 24: "When the candle finishes the strategies take it as always and an idea already sent live is not sent again"
- **Source:** accepted after it was built: owner, 2026-11-11T20:45:20Z, PASTED, "Behave like the live bot: entries on the tick, as live; stops, targets and band closes checked tick by tick; at most one trade per strategy and direction per candle."
- **Mark:** Owner's words, unchanged

### 9.53 The pace and target rule refuses a Bollinger bounce against open trend trades unless it is valid
- **Code:** `trading/engine.py:202-204, 473-475`
  ```python
  202	        verdict = self._against_trend(idea, candle.start)
  203	        if verdict is not None and not verdict.valid:
  204	            return
  ```
- **DESIGN.md:** line 158 ("Against open trend trades: the pace and target rule"); line 220: "A bounce that is not at such a level, or comes while price is moving fast, is refused and the trend trades are held."
- **Source:** owner, 2026-11-11T16:53:52Z, PASTED, "While the bot has open trend trades (EMA pullback, slow grind, breakout), no Bollinger bounce may open against them, unless it opens at a significant level ... Otherwise it is refused and the trend trades are held."
- **Mark:** Owner's words, unchanged

### 9.54 If the pace and target rule cannot be checked, a bounce against open trend trades is refused
- **Code:** `trading/engine.py:224-231`
  ```python
  224	        except Exception as e:                              # noqa: BLE001  (never open it unchecked)
  226	            opp = trend_trades_against(self.manager.trades.values(), idea.direction) \
  230	            v = Verdict(False, f"the rule could not be checked ({e})", [f"{x.strategy} {x.direction} {x.reference}"
  ```
- **DESIGN.md:** none
- **Source:** none found
- **Mark:** Added without the owner asking

### 9.55 Start-up checks on the hours: NEW_TRADES_FROM before NEW_TRADES_UNTIL; close_all_trades_at not before NEW_TRADES_UNTIL; rollover from before until
- **Code:** `config/settings_loader.py:666-670, 681`
  ```python
  666	    if sw["new_trades_from"] >= sw["new_trades_until"]:
  668	    if v["hours"]["close_all_trades_at"] < sw["new_trades_until"]:
  681	    if sg["rollover_no_new_trades_from"] >= sg["rollover_no_new_trades_until"]:
  ```
- **DESIGN.md:** line 361: "Switches in `.env`, checked at start-up"
- **Source:** owner asked for checks, gave none of these: owner, 2026-11-07T07:53:05Z, PASTED, "with their values checked at start-up"
- **Mark:** Added without the owner asking
