## Step 3. Mechanics of every losing trade since 19 Nov 18:44

The live code is 02f6c7e: the price service process started at `Thu Nov 19 18:43:54 2026` (`ps -o lstart`) and
has not restarted. The tree was later checked out at 26c06fc (19 Nov 20:20) and bb085f4 (20 Nov 12:11), but
neither was loaded by the running service (memory note `stp-structural-history-deploy`: "autobot-prices NOT
restarted"). Every code reading below is from an exact copy of 02f6c7e (`git archive 02f6c7e`).

### 3.1 The losing (and flat) trades, checked one by one

"Quote at send" is the bot's own `reached on the live price at … (bid, offer)` line in the trade record. "Stop
candle" is the stored 5-minute candle in which IG closed the trade.

| # | Opened | Strategy, dir | Entry rule | Rule price → IG fill | Stop: rule / sent / IG | Stop side | Spread at entry / at stop | Exit | Management |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 19 Nov 19:33:16 | level reversal buy | live break above confirmation high 13102.7 | quote offer 13104.4 (bid 13102.9) → 13104.4 | 13091.8 / 12.6 / 13091.8 (12.6) | below ✔ | 1.5 / – | Johnny 20:16:50 at 13100.9 (−3.5) | none due |
| 2 | 19 Nov 19:51:09 | EMA pullback sell | live, 3 pips below the 5-candle low, 13094.8 | bid 13094.8 → 13094.5 | 12 / 12 / 13106.5 (12) | above ✔ | 1.5 / – | Johnny 20:16:54 at 13102.4 (−7.9) | none due |
| 3 | 20 Nov 06:07:42 | level reversal buy | live break above 13109.6 | offer 13111.5 → 13111.4 | 13094.2 / 17.3 / 13094.1 (17.3) | below ✔ | 1.5 / 1.5 | IG stop 11:59:15 at 13094.1 (−17.3); candle 11:55 sell low 13093.0 | best +10.5; no break-even in this build (rule, not fault) |
| 4 | 07:15:01 | Asian range breakout buy | next candle's open after the 07:10 close above the Asian high 13117.8 | 07:15 open 13120.8 (bid) → offer fill 13122.3 | 12 / 12 / 13110.3 (12) | below ✔ | 1.5 / 0.9–1.5 | IG stop 08:00:46 at 13110.3 (−12.0); candle 08:00 sell low 13105.8 | best −0.9; trail (from +12) never reached |
| 5 | 07:25:06 | Bollinger bounce 5m sell | live break below 13114.8 | bid 13114.7 → 13114.8 | 12 / 12 / 13126.8 (12) | above ✔ | 1.5 / – | bot closed 07:45:02 at 13116.5 (−1.7): "a confirmed rejection at a level: london_session_low 13111.2, pivot 13111.6" | the 5m bounce's level-close rule, as written |
| 6 | 13:10:24 | level reversal buy | live break above confirmation high 13126.2 (confirmation 13:00, trigger on the 13:10 candle) | offer 13127.9 → 13127.7 | 13093.6 / 34.3 / 13093.4 (34.3) | below ✔ | 1.5 / – | Johnny 16:11:44 at 13101.6 (−26.1, −£261) | best +0.9; stop never reached |
| 7 | 13:25:12 | slow grind buy | live break above the pause high 13126.9 | offer 13128.5 → 13128.3 | 15 / 15 / 13113.3 (15) | below ✔ | 1.5 / 1.5 | IG stop 13:41:36 at 13113.3 (−15.0); candle 13:40 sell low 13111.9 | best −1.1 |
| 8 | 13:32:09 | Bollinger bounce 5m sell | live break below 13118.9 | bid 13118.6 → 13118.1 | 12 / 12 / 13130.1 (12) | above ✔ | 1.5 / – | bot closed 14:35:02 at 13118.1 (0.0): "a confirmed rejection at a level: pivot 13111.6" | best +11.0; the 5m bounce has no trail in this build |
| 9 | 14:45:07 | Bollinger bounce 5m sell | live break below 13107.4 | bid 13107.1 → 13107.1 | 12 / 12 / 13119.1 (12) | above ✔ | 1.5 / 1.5 | IG stop 15:44:03 at 13119.1 (−12.0); candle 15:40 buy high 13120.3 | best +3.1; the level watch "hold … the analyser's rejection setup is over" (15:20) |
| 10 | 18:42:26 | EMA pullback sell | live, 13092.3 | bid 13092.3 → 13091.4 | 12 / 12 / 13103.4 (12) | above ✔ | 1.5 / – | Johnny 18:43:24 at 13092.8 (−1.4) | none due |

Raw evidence for row 6 (the −£261 trade):
- Journal line 935: `"event": "sending", "strategy": "level reversal", "direction": "buy", "stop_pips": "32.6", "stop_distance": "34.3", "take_profit_pips": 20, "idea_price": "13126.2"`
- IG activity 13:10:24: `"Position opened: WDUG25BW", "level": 13127.7, "stopLevel": 13093.4, "stopDistance": 34.3, "limitLevel": 13147.7`
- IG transaction: `"openDateUtc": "2026-11-20T13:10:24", "dateUtc": "2026-11-20T16:11:44", "openLevel": "13127.7", "closeLevel": "13101.6", "profitAndLoss": "£-261.00"`
- The record's steps: `pierce 13099.6 … reached round_number 13100` (12:40), `reversal candle … C 13112` (12:55), `confirmation 13125.2 … trigger at above 13126.2` (13:00), `price went above 13126.2` (13:10), `furthest low 13099.6 … 0.4 pips past the level (allowance 5)`, `stop 13093.6: 6 pips below the furthest point; take profit 20 pips`.

### 3.2 Findings for each check

- **Stop sent, accepted, right distance, right side:** yes for all 15 trades since 18:44 (and all 106 since 9 Nov).
  IG's `stopDistance` equals the bot's `stop_distance` on every trade. No trade was ever open without a stop.
- **Opened at the price and time the rule says:** yes. The next-candle strategies (Asian range breakout, hourly
  bounce, session sweep) opened 0–6 seconds into the candle, at its open. The live-break strategies opened while
  the price was at the trigger (each quote at send is within 0.4 pips of the trigger, on the right side). Fills
  differed from the quote by 0.0–0.9 pips (worst: 18:42 EMA sell, bid 13092.3, filled 13091.4).
- **Direction right for the rule:** yes. In 02f6c7e the direction rule applies only to the EMA pullback
  (`NO_DIRECTION_RULE` in `strategies/common.py`). Both EMA sells were on the sell side ("price … below the pivot
  … and below the 5m 100 EMA"). The 5m bounce is allowed only *against* a trend (`BOLLINGER_BOUNCE_5M: {TREND:
  "against", POSSIBLE_REVERSAL: "any"}`), so its sells in "trend up, slow grind" are by design. The hourly bounce
  and the session strategies aren't checked against the state at all (`WITHOUT_HINDRANCE`).
- **Buy vs sell price basis:** the strategies work on the sell (bid) chart. Buys fill at the offer and sells at the
  bid, as they should. IG triggers a buy's stop on the bid and a sell's stop on the offer. Two small effects:
  (a) **for the level reversal and the session sweep, the stop is a bid-chart price.** For a sell, IG triggers it
  when the *offer* reaches it, so a sell's real cushion beyond the furthest high is 6 − spread (≈4.5 pips), while
  a buy gets the full 6. (b) The bot sends a *distance* worked out from the quote at the moment of sending. IG
  applies it to the *fill*, so the stop moves by the slippage: 06:07 rule 13094.2 → IG 13094.1; 13:10 13093.6 →
  13093.4; the open 18:45 sell 13104.0 → 13103.3 (0.7 pips tighter). Small, but not what the rule says.
- **Spread:** 1.5 pips at every entry and at every stop candle (0.9–1.0 at moments). Nothing abnormal, and no stop
  filled worse than its level.
- **Duplicate, late or stale entries:** none. No strategy had two trades open at once in this version. The only
  same-strategy overlaps since 9 Nov are the EMA pullback's (10–11 Nov and 16 Nov), which has no open-trade limit
  by design (safety rule 5: "the EMA pullback no limit"). **One design gap:** a bounce setup's trigger never
  expires after its confirmation candle (`rejection/watch.py`: "4. trigger: the live price goes below the
  confirmation candle's low"; only a cancel past the reversal candle ends it). The 13:10 buy triggered two candles
  after its 13:00 confirmation, after the 13:05 high of 13126.0 missed the trigger by 0.2 pips.
- **Opposite trades open together:** 12 pairs in this version (e.g. 13:10 LR buy and 13:25 slow grind buy open
  while 13:30 bounce sell, 13:32 bounce 5m sell and 13:35 session sweep sell opened). They came from one move:
  the 13:00–13:10 push to 13128.6 was the level reversal's *confirmation* (buy) and the hourly bounce's *rejection
  candle* (sell) at the same time.
- **Trade management:** did what the live rules say. The session sweep at 07:30 trailed from +12 to a stop at
  13106.0 and banked +7.5. The hourly bounce at 13:30 trailed to 13117.2 (+2.9), with IG's minimum distance
  respected ("sent as 13117.6, the nearest level IG allows"). The 5m bounce's level closes fired on confirmed
  rejections. The level reversal has no break-even in this build. TRAIL_NO_LOSS was a Stage 4 switch, and the
  rollback dropped it, so trade 3 went from +10.5 to −17.3. That follows the rules.

### 3.3 Extra check 1: the level reversal's stop

**The exact rule (02f6c7e, `strategies/level_reversal/strategy.py` lines 90–101):**

```python
furthest = max(self._h(c) for c in span) if sell else min(self._l(c) for c in span)
...
beyond = Decimal(self.lr.stop_beyond_furthest_pips) * self.ppp
stop = furthest + beyond if sell else furthest - beyond
```

`span` is every candle from the piercing candle to the confirmation candle. `stop_beyond_furthest_pips = 6`
(`config/settings.toml` `[level_reversal]`). The sender turns that price into a distance from the current price
(`orders/sender.py` `_stop_distance`: `dist = (offer - Decimal(sp))` for a buy). Take profit is a fixed
`take_profit_pips = 20`.

- **17.3 pips (06:07):** furthest low 13100.2 (05:45 candle) − 6 = 13094.2. The entry trigger was 13109.6 and the
  offer 13111.5, so the distance was 13111.5 − 13094.2 = 17.3.
- **34.3 pips (13:10):** furthest low 13099.6 (12:40) − 6 = 13093.6. The trigger was 13126.2 (the confirmation
  candle ran from 13111 to 13125.2) and the offer 13127.9, so the distance was 13127.9 − 13093.6 = 34.3.
- **In the first build (f99efe1)?** Yes, line for line. `git show f99efe1:strategies/level_reversal/strategy.py`
  has the same lines 100–101, `stop_beyond_furthest_pips = 6` and `take_profit_pips = 20`. Its sender has the same
  `_stop_distance`.
- **Does anything cap it?** **No, not in the live code.** No maximum stop, no maximum distance from the level, no
  stop-versus-target check. Safety rule 7 (total risk) is £100,000, "set so it is never reached". The only caps
  ever built were in d9e5d0e (Stage 4, live 19 Nov 09:49–18:43): `LEVEL_STOPS` ("refused if wider than
  widest_stop_pips (20)") and `LR_ENTRY_NEAR_LEVEL` (`entry_within_pips_of_level 6`). Neither file exists in
  02f6c7e. `.env` still has `LEVEL_STOPS=on` and `LR_ENTRY_NEAR_LEVEL=on`, but the live `config/switches.py` reads
  neither. Six other lines in `.env` are also ignored by the live code: `HOURLY_READ`, `TREND_STILL_GOING`,
  `ANALYSER_USES_HOURLY`, `ANALYSER_GOVERNS_ALL`, `SCALE_OUT_REVERSAL`, `TRAIL_NO_LOSS`.

**Stop vs take profit, every level reversal trade since 9 Nov (IG's figures):**

LR_TABLE

Five of the 19 had a stop of 20 pips or more, against the 20-pip target. By the rule's own arithmetic it needs to win
more than half its trades to break even at 1:1, and more than 63% at 34:20.

### 3.4 Extra check 2: the stop each strategy is meant to use, against what it sent

Where the live code decides the stop: `strategies/common.py` `stop_loss_pips()` and `stop_price()`, with the
values from `config/settings.toml` and `.env` (`STOP_LOSS_PIPS=12`, `STOP_LOSS_PIPS_EMA_PULLBACK=12`).

| Strategy | Setting the live code uses | Meant stop | Sent since 19 Nov 18:44 (rule → IG) | Sent 9–19 Nov |
|---|---|---|---|---|
| EMA pullback | `.env STOP_LOSS_PIPS_EMA_PULLBACK` | 12 | 12 → 12 (×3) | 12 → 12 (×22) |
| slow grind | `[slow_grind] stop_loss_pips` | 15 | 15 → 15 | 15 → 15 (×16) |
| Bollinger bounce (hourly) | `.env STOP_LOSS_PIPS` | 12 | 12 → 12 | 6 → 6 (×7, 9–10 Nov when STOP_LOSS_PIPS was 6), 12 → 12 (×11) |
| Bollinger bounce 5m | `.env STOP_LOSS_PIPS` | 12 | 12 → 12 (×3) | – |
| range trade | `.env STOP_LOSS_PIPS` | 12 | – (no trade) | 6 → 6 (×3, 9–10 Nov), 12 → 12 (×4) |
| **breakout** | **`[breakout] stop_loss_pips`** | **6 in the live code** (Johnny set 12 on 10 Nov) | – (no trade) | 6 → 6 (×4, 9–10 Nov), 12 → 12 (×6, from 10 Nov 15:36 to 18 Nov) |
| Asian range breakout | `[asian_range_breakout] stop_loss_pips` | 12 | 12 → 12 | 12 → 12 (×2) |
| New York open reversal | `[new_york_open_reversal] stop_loss_pips` | 12 | – (never traded) | – |
| session sweep | `stop_price()`: 1 beyond the sweep's furthest point, at least `min_stop_pips` 12 | ≥ 12 | 12 → 12 (×2) | 15.6 → 17.1, 22.0 → 22 |
| level reversal | `stop_price()`: 6 beyond the furthest point, **no cap** | varies | 10.9–32.6 → 12.6–34.3 | 9.7–23.6 → 9.8–25.3 |

**The breakout:** the earlier report's "`[breakout] stop_loss_pips = 6`" is what the live code reads (02f6c7e
`config/settings.toml`: `stop_loss_pips = 6`, `take_profit_pips = 50`; `stop_loss_pips()` returns
`settings.breakout.stop_loss_pips`). Johnny's commit 0e1492b (10 Nov 15:36, "Stop 12 pips for the Bollinger
bounce, range trade and breakout") changed it to 12, and every breakout from then to 18 Nov sent 12. First-build-plus
(f35bd1b → 02f6c7e) is built on f99efe1, which predates 0e1492b, so the value went back to 6.
`research/rollback_20261119/REPORT.md` line 125 ("The 9 Nov code would use 12 for the bounce, range trade and
breakout") and `research/first_build_plus_20261119/REPORT.md` line 123 ("both bounces, the range trade and the
breakout take their stop from STOP_LOSS_PIPS") are **wrong about the breakout**. **The 12-pip, −£120 loss today
was the 07:15 Asian range breakout** (journal: `"strategy": "Asian range breakout", "stop_pips": "12"`; IG:
`"openLevel": "13122.3", "closeLevel": "13110.3", "profitAndLoss": "£-120.00"`). Its own setting is 12, as
specified. The other −£120 today was the 14:45 Bollinger bounce 5m (`STOP_LOSS_PIPS` 12).
