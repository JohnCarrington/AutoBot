# 6. Historical trade impact assessment

## 6.1 How to read this

- Every figure is the **recorded result of an actual trade** at IG (corrections in §1.1). No trade was replayed,
  simulated or re-managed. Nothing here says what a deferred idea would have earned later.
- Filtering past trades in hindsight **is not proof of future profitability.** A rule refusing a past loser says
  only that the loser had the structural defect the rule names. Live demo results are the judge.
- Owner closes (16) are listed and never counted as bot wins or losses.
- The sample is small: 86 trades, of which 11–14 are touched.

## 6.2 Evidence card per proposed rule

### Rule SCA-S4 (Watch & Wait when within an unresolved opposing zone; options B-2, C-1)

| Item | Evidence |
|---|---|
| Defect addressed | Entries at, inside, or through an opposing STP zone that STP still holds unresolved: no D-20 break in the trade's direction, no OD-33 contested-zone rejection. Also entries against a confirmed D-20 break. |
| Structural evidence used | STP opportunities live at entry (status, label, zone), STP's D-20 break and its direction, "confirmed break held", NEAR (3 pips), the strategy's own rejection candle (for S5). |
| Losing bot trades prevented (11) | 20 Nov 13:25 slow grind BUY −15.0 · 23 Nov 06:00 level reversal BUY −14.6 · 06:45 EMA pullback BUY −12.0 · 12:26 bounce BUY −12.0 · 12:30 sweep BUY −13.5 · 13:00 bounce 5m BUY −12.0 · 25 Nov 18:02 slow grind BUY −15.0 (orphan, IG) · 18:45 slow grind BUY −5.1 · 19:10 EMA pullback BUY −5.7 · 26 Nov 11:45 breakout SELL −6.0 · 11:55 slow grind SELL −15.0 |
| Winning bot trades prevented | **none** in the window |
| Owner closes affected (3) | 20 Nov 13:10 level reversal BUY −26.1 · 25 Nov 12:25 sweep BUY −6.0 · 27 Nov 15:47 slow grind SELL +4.3 (closed by hand at 16:20; after-close path unknown) |
| Legitimate trades unaffected | the 61.4-pip sweep (S2) · EMA pullback 23 Nov 14:39 +30.0 (S2) · slow grind +20 ×3 (S2) · breakout 24 Nov 08:55 +50.0 (S2) · bounce 5m 26 Nov 11:40 +14.0 (S6, retest of a broken zone) · reversals at structure 23 Nov 09:05 +14.8 (S1), 26 Nov 06:01 +5.0 (S5), 27 Nov 15:11 (S5) · re-armed tests 27 Nov 12:01 (S7, re-issued 1200-57) |
| Unintended consequences | (1) Break continuations wait for the hourly D-20 close. On 27 Nov, SELL ideas from 13:20 to 14:23 (13110.6 → 13111.6) were deferred until STP broke BUY 1305-58 at 15:00, which is later entry or no entry. (2) A breakout into an unresolved zone is effectively refused, because its pullback window expires first. (3) Opportunities created seconds before an entry (23 Nov 13:00:12 vs 13:00:03) decide the state, so ordering matters (TS-12). (4) A bad STP zone becomes a bad deferral: the SCA inherits STP's errors in both directions. (5) The noisiest strategy (bounce 5m) carries most deferrals (38 of 75 ideas). |
| Tests | TS-01…TS-14, FS-01…FS-10 (§7) |

### SCA-S5 (contested-zone rejection exemption, option C-1)

| Item | Evidence |
|---|---|
| Defect addressed | Without it, S4 would veto every reversal at a two-direction zone (OD-33): option C-2, a near-blanket veto from 24 Nov. |
| Trades it keeps | 26 Nov 06:01 bounce 5m BUY +5.0 · 06:30 SELL −7.3 · 27 Nov 15:11 SELL (owner +9.0) |
| Losers it lets through | 26 Nov 06:30 −7.3 |
| Unintended consequences | The strategy's rejection candle must be emitted for every reversal strategy (WP-2). A rejection that only reached the zone by a NEAR allowance counts. |

### SCA-S3 (approaching; option D-1 record only, D-2 Watch & Wait)

| Item | Evidence |
|---|---|
| D-2 would prevent | 26 Nov 12:51 bounce 5m SELL −6.4 (1 trade, 10 ideas) |
| Recommendation | record only. Too little evidence, and distance is the room rule's question. |

### Rule R (room to opposing zone, separate)

| Item | Evidence |
|---|---|
| Defect addressed | Entries whose own stop is larger than the room to the next live opposing zone. |
| Losing bot trades prevented (2) | 25 Nov 11:00 EMA pullback SELL −12.0 (11.3 vs 12) · 26 Nov 12:51 bounce 5m SELL −6.4 (1.6 vs 12; not under R-b) |
| Winning bot trades prevented (2) | 23 Nov 01:47 slow grind BUY **+20.0** (4.1 vs 15) · 26 Nov 14:22 bounce 5m SELL +2.1 (11.8 vs 12) |
| Unintended consequences | Wide-stop strategies (level reversal, sweep) are refused more often by construction. It interacts with stop methodology, which is out of scope to change. |
| Recommendation | not adopted now (D-7) |

### Opposite-position rule G-2 (not recommended)

| Item | Evidence |
|---|---|
| Prevents | 10 bot losers (mostly 23 Nov hourly-bounce BUYs during the down-move) |
| Also prevents | 4 bot winners: 23 Nov 14:39 EMA pullback +30.0, 10:57 slow grind +20.0, 09:10 sweep +12.2, 20 Nov 07:30 sweep +7.5 |
| Why not | It is a directional rule (constraint 7). Opposite entries with a structural conflict are already caught by S4. |

## 6.3 Breadth over ideas (STP must not become a blanket veto)

416 confirmed ideas (passed `common.check`), one per strategy, direction and 10 minutes:

| State | Ideas | Share |
|---|---|---|
| S2 neutral | 212 | 51% |
| S4 within unresolved opposing (deferred) | 75 | 18% |
| S7 continuation | 36 | 9% |
| S5 confirmed rejection | 34 | 8% |
| S1 aligned | 29 | 7% |
| S6 confirmed break | 20 | 5% |
| S3 approaching | 10 | 2% |

- **Not directional.** The deferred ideas are 39 BUY and 36 SELL. By day: 18 Nov 1, 20 Nov 2, 23 Nov 8,
  24 Nov 4, 25 Nov 14 (all BUY, against the evening SELL zone 1800-35), 26 Nov 9, 27 Nov 37 (30 SELL at the BUY
  zone that held, 7 BUY).
- **On days with no live STP structure (18–19 Nov) the SCA defers nothing** (1 idea on 18 Nov).
- **Friday 27 Nov is the heaviest day.** 37 of 94 ideas were deferred. They cluster in two places:
  the 13121–130 BUY zone 03:45–10:52 (which held: three wick sweeps back inside, completed 11:05), and the
  13:20–14:23 SELLs past BUY 1305-58 before its 15:00 D-20 break.

## 6.4 Watch & Wait releases observed (fresh confirmation)

| Deferred | Released by | Fresh idea (journal outcome) |
|---|---|---|
| 23 Nov 06:00 level reversal BUY (S4) | price left the zone | 10:42 BUY 13110.9, S2. The safety limit refused it (the 06:00 trade was open). |
| 23 Nov 12:26 / 13:00 bounce 5m BUY (S4) | zones ended / price left | 15:30 BUY 13043.2, S2: opened, −12.0 (an unrelated S2 loss) |
| 25 Nov 12:25 session sweep BUY (S4) | SELL 1200-29 completed 13:10 | **15:05 BUY 13061.8, S2: opened, +61.4** (London-low sweep, a different level) |
| 26 Nov 12:51 bounce 5m SELL (S3, if D-2) | — | 14:22 SELL 13114.8, S1: opened, +2.1 |
| 27 Nov 15:47 slow grind SELL (S4) | BUY 1500-60 D-20 break 16:00 | 16:05 SELL 13098.3, S6. The safety limit refused it (15:47 trade open). |

No deferred idea is ever executed later. Each release is a new setup of the strategy's own.
