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
| Legitimate trades unaffected | the 61.4-pip sweep (S2) · EMA pullback 23 Nov 14:39 +30.0 (S2) · slow grind +20 ×3 (S2) · breakout 24 Nov 08:55 +50.0 (S2) · bounce 5m 26 Nov 11:40 +14.0 (S6, retest of a broken zone) · reversals at structure 23 Nov 09:05 +14.8 (S1), 26 Nov 06:01 +5.0 (S5), 27 Nov 15:11 (S5) · a genuine new test after re-arming, 26 Nov 11:40 (+14.0, `0000-37#t2`, S6). *Rev 1 wrongly cited 27 Nov 12:01 here: that was the duplicate of `0300-56#t1`, which Phase 2 refuses whatever its SCA state (§6.5).* |
| Unintended consequences | (1) Break continuations wait for the hourly D-20 close. On 27 Nov, SELL ideas from 13:20 to 14:23 (13110.6 → 13111.6) were deferred until STP broke BUY 1305-58 at 15:00, which is later entry or no entry. (2) A breakout into an unresolved zone is effectively refused, because its pullback window expires first. (3) Opportunities created seconds before an entry (23 Nov 13:00:12 vs 13:00:03) decide the state, so ordering matters (TS-12). (4) A bad STP zone becomes a bad deferral: the SCA inherits STP's errors in both directions. (5) The noisiest strategy (bounce 5m) carries the most deferrals (41 of 82 ideas). (6) On the Phase 2 build, an opposing opportunity with an unreconciled data gap cannot be resolved, so it can hold back trades at or past it until Phase 2 reconciles the gap (R3, D-14; not measurable in this window, O-6). |
| Tests | TS-01…TS-14, TS-22…TS-33, FS-01…FS-24 (§7) |

### SCA-S5 (contested-zone rejection exemption, option C-1)

| Item | Evidence |
|---|---|
| Defect addressed | Without it, S4 would veto every reversal at a two-direction zone (OD-33): option C-2, a near-blanket veto from 24 Nov. Revision 2: S5 resolves only the opposing opportunity whose zone the rejection reached, paired with a directly overlapping agreeing one, and never another opportunity's S4 (R2). |
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

416 confirmed ideas (passed `common.check`), one per strategy, direction and 10 minutes. These are revision 2
figures (`classify3.py`: each opportunity judged on its own, no 24-hour look-back). Revision 1's figures are
in brackets. 8 ideas changed and no trades (§10). S2 here is "neutral as reconstructed": STP's historical
availability cannot be rebuilt, so UNKNOWN (R5) cannot be counted for the past.

| State | Ideas | Share |
|---|---|---|
| S2 neutral | 212 | 51% |
| S4 within unresolved opposing (deferred) | **82** (75) | **20%** (18%) |
| S5 confirmed rejection | 35 (34) | 8% |
| S1 aligned | 29 | 7% |
| S7 continuation (naming only) | 28 (36) | 7% (9%) |
| S6 confirmed break | 20 | 5% |
| S3 approaching | 10 | 2% |

- **Not directional.** The deferred ideas are 46 BUY and 36 SELL. By day: 18 Nov 1, 20 Nov 2, 23 Nov 8,
  24 Nov 4, 25 Nov 14 (all BUY, against the evening SELL zone 1800-35), 26 Nov 9, 27 Nov 44 (30 SELL at the BUY
  zone that held, 14 BUY).
- **On days with no live STP structure (18–19 Nov) the SCA defers nothing** (1 idea on 18 Nov).
- **Friday 27 Nov is the heaviest day.** 44 of 94 ideas were deferred. They cluster in three places:
  - the 13121–130 BUY zone 03:45–10:52, which held: three wick sweeps closed back inside, and it completed at
    11:05;
  - the 13:20–14:23 SELLs past BUY 1305-58, before its 15:00 D-20 break;
  - new in revision 2: the 01:35–01:50 BUYs past the new SELL 0100-51, before its 02:00 break, and 17:34 past
    SELL 1700-61.

## 6.4 Watch & Wait releases observed (fresh confirmation)

| Deferred | Released by | Fresh idea (journal outcome) |
|---|---|---|
| 23 Nov 06:00 level reversal BUY (S4) | price left the zone | 10:42 BUY 13110.9, S2. The safety limit refused it (the 06:00 trade was open). |
| 23 Nov 12:26 / 13:00 bounce 5m BUY (S4) | zones ended / price left | 15:30 BUY 13043.2, S2: opened, −12.0 (an unrelated S2 loss) |
| 25 Nov 12:25 session sweep BUY (S4) | SELL 1200-29 completed 13:10 | **15:05 BUY 13061.8, S2: opened, +61.4** (London-low sweep, a different level) |
| 26 Nov 12:51 bounce 5m SELL (S3, if D-2) | — | 14:22 SELL 13114.8, S1: opened, +2.1 |
| 27 Nov 15:47 slow grind SELL (S4) | BUY 1500-60 D-20 break 16:00 | 16:05 SELL 13098.3, S6. The safety limit refused it (15:47 trade open). |

No deferred idea is ever executed later. Each release is a new setup of the strategy's own.

## 6.5 Structural permission versus overall admission (R4)

- The SCA gives **structural permission** only. **Admission** needs every layer of `_place` (§3.11).
- Every trade figure above is the SCA's own effect, i.e. what the SCA refuses. It never claims that an SCA permit
  admits a trade.
- None of the 11 S4 bot trades was STP-authorised: they predate Stage B, or are ungated strategies. Phase 2 does
  not change them, so for these the SCA refusal is the overall result.

| Trade / idea | SCA state (permission) | Phase 2 (gate on) | Other layers | Overall admission (Phase 2 + SCA) |
|---|---|---|---|---|
| 25 Nov 15:05 sweep BUY (+61.4) | S2 permit | not gated | passed (recorded) | admitted |
| 26 Nov 06:01 bounce 5m BUY (+5.0) | S5 permit | `0000-37#t1` admitted | passed | admitted |
| 26 Nov 11:40 bounce 5m BUY (+14.0) | S6 permit | `0000-37#t2` admitted (genuine re-armed test, FL-A5) | passed | admitted |
| **27 Nov 12:01 bounce 5m BUY (owner −1.4)** | **S7 permit** | **refused**: 1200-57 withheld (PD-2); rule 11 alias `0300-56#t1` (FL-A3, FL-M1) | — | **refused (Phase 2)** |
| 27 Nov 15:11 bounce 5m SELL (owner +9.0) | production data: S5 permit. **Phase 2 build, before OP-1: S4(d) unverifiable**, because the agreeing 1500-59's lineage count runs through the uncertain 12:00 hour, so no S5 (R3). | **refused under D-R2** until the 12:00–12:10 candles are recovered and reconciled (Saturday pack §8) | — | refused (Phase 2, and the SCA agrees); re-decided after OP-1 |
| 25 Nov 18:45 slow grind BUY (−5.1) | **S4** | not gated | passed (recorded) | refused (SCA) |
| 23 Nov 10:42 level reversal BUY (fresh idea after a deferral) | S2 permit | not gated in the window | **safety limit** (06:00 trade open) | refused (safety) |
| 27 Nov 16:05 slow grind SELL (fresh idea) | S6 permit | not gated | **safety limit** (15:47 trade open) | refused (safety) |
