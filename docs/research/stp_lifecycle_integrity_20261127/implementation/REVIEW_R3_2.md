# Review of `fec364b`: completeness of a locally built candle (27 November 2026)

**Verdict: a defect against the approved requirement**, which is: "Where continuity cannot be established, the engine-built candle must not substitute for a missing authoritative candle", and "If the completeness of a locally constructed candle cannot be established, prefer the authoritative completed IG candle and fail closed until it is available".

It was reproduced with failing functional tests on `fec364b` (`review_R3_2_tests_before_fix.txt`). It is corrected by **removing the local stand-in altogether**. Phase 2 is under feature freeze: nothing else changed.

## 1. Does IG's subscription guarantee every price change?

**No guarantee can be established.**

- **The bot's subscription.** Ticks are `CHART:<epic>:TICK` in mode **DISTINCT**, snapshot "no", **no requested maximum frequency**, and **without unfiltered dispatching** (`ig/stream.py LightstreamerTransport`). The 5-minute candles are `CHART:<epic>:5MINUTE` in mode MERGE.
- **IG's documentation.** The Streaming API Reference lists `CHART:{epic}:TICK` as DISTINCT. The Streaming API Guide says DISTINCT "indicates that each update should yield a notification". It says nothing about conflation, server-side frequency limits, or a guarantee that every market price change is published to the client.
- **The Lightstreamer client library's own documentation** (lightstreamer-client-lib 2.2.3, installed):
  - `setRequestedMaxFrequency`: "frequency limits on the items can also be set on the server side and this request can only be issued in order to furtherly reduce the frequency, not to rise it beyond these limits". It adds that "a further global frequency limit could also be imposed by the Server".
  - `onItemLostUpdates`: the server reports dropped updates "only if the items are delivered in an unfiltered mode". So with the bot's filtered DISTINCT subscription, dropped or filtered updates would not be reported at all.
- **So** neither IG nor the library guarantees that every price change reaches the bot, and the bot could not detect it if one did not. A candle built from the received ticks cannot be shown to be complete. R3.1's premise ("IG's stream sends every price change, so no price on an unbroken connection means no change") cannot be established.

## 2. A quiet five-minute interval, then a price change

**Reproduced (R31-10).**
- On an unbroken stream with no price change from 10:00 to 10:05:30, the price carried into the 10:05 candle (13169.5, at the destination 13170) is that candle's open.
- `prices/live.py` (`fec364b`) opened the 10:05 candle at the first **new** price (13200), because the candle before it was not the one immediately before. The carried-forward open was omitted, and the STP check **authorised**.
- R31-11 shows the general case: with a clean, unbroken stream, the local candle stood in for IG's unpublished one and the check authorised. That is not allowed, given §1.

## 3. Correction

- **The stand-in is removed.** `prices/live.py` is deleted. `ig/stream.py`, `prices/feed.py` and `prices/service.py` are back to production (`fadf228`); `trading/engine.py` is back to WP3 (`b49337e`).
- **`stp/authorise.py`:** every finished 5-minute interval after the tracker's last step, **the most recent included**, must be stored as **IG's own completed candle**. Otherwise the check refuses: "IG's 5-minute candle for … is not stored yet … (PD-5)". The R3 defect stays fixed: a genuine gap in the most recent interval refuses.
- **Effect on normal trading:** in IG's normal publication delay (production: 4,291 of 4,297 candles stored within second :00 after their boundary, 4 more within :01), a gated idea in that sub-second refuses. The engine tries each strategy, direction and candle once, so such an idea is not retried in that candle. This is the fail-closed choice your brief asks for, with no timing number.

  On the record since Stage B, every one of the 10 STP-authorised ideas came **3 seconds or more** after its 5-minute boundary, by which time IG's candle was stored. The earliest was 11:40:03 on 26 Nov; then 06:30:04 on 26 Nov and 06:55:04 on 27 Nov (4 s), and 20:05:14 on 25 Nov (14 s). None fell inside the publication delay.

## 4. Tests

- **`tests/functional/test_stp_live_continuity_20261127.py`**, the real stream and feed through the pretend IG transport, the engine's live path, and the real `Trading._place` and STP check:
  - R31-01 to R31-05, R31-07, R31-08, R31-10 and R31-11: before IG publishes, the check refuses, whatever the stream did. That covers an interruption inside the candle or across the boundary, a quiet spell, a restart, a touch within one second, a late first price, repeated prices, the quiet interval with a carried-forward open, and a clean candle.
  - R31-05, R31-06 and R31-09: once IG's candle is stored, it decides. IG's candle with the touch refuses; IG's clean candle authorises.
- **TR3-01 to TR3-05 and TR3-07** (rewritten to the same rule): TR3-05 asserts that the engine passes the STP check nothing but its forming candle and the live price.
- **Changed** (all Phase 2 tests, none from the original suite):
  - the R3.1 expectations that a locally built candle authorises (R31-06, R31-07, R31-08) now expect a refusal until IG publishes;
  - R31-03 (stall) became a quiet spell, since the stall event is removed with the stand-in;
  - TR3-06 (the live record) is removed with its module.
- **`test_stp_review_20261125::test_R6`'s stand-in** is back to its original signature: that test is now as in the original suite, apart from WP2's R4 field list.

`REVIEW_R3_1.md` is superseded by this document wherever it relies on a locally built candle.

## 5. Found while preparing the Saturday pack: the duplicate rule and genuinely new tests

The before-and-after replay to 18:30 (production copies of 18:29, `tests/stp/fixtures/lifecycle_20261127_1830`) showed two more **defects against approved requirements**. Both are reproduced first (`review_duplicate_rearm_tests_before_fix.txt`) and corrected.

1. **A completed place's republication was withheld for good.**
   - **Requirement:** brief §2, "a genuine new structural test following the approved re-arm conditions must remain available for trading", and §3.4.
   - **What happened:** after a completion, later reissues of the place were themselves withheld, so the completion stayed "the most recently ended" match indefinitely.
   - **The real case:** SELL 13108.5–13119.1 → 13103 at 15:00 on 27 Nov. It was withheld as a duplicate of 1400-44, which reached 13103 on **26 Nov** at 14:45. Since then the zone had re-armed many times, and the migration places the 15:11 rejection at test 9.
   - **Correction** (`OpportunityKeeper._duplicate_of`, `planner/lineage.py rearmed_since`): the completed opportunity withholds a republication only while its zone has **not re-armed** since the completion, by the D-25 / P-C8 rule (a complete hourly candle wholly clear of it). No new number.
   - **Effect on the real days:** the only republications still withheld are 1200-57 and 1305-58, the reissues of 0300-56's test 1, which never re-armed. **The 12:01 duplicate stays refused.** The other five withholdings in earlier versions of this report were re-armed places, and they are now published.
   - Tests: TW1-19; FL-E2; FL-A8 (the list is now those two).
2. **An uncertain hour met while seeding or rejoining a lineage was never reconciled.**
   - **Requirement:** PD-5 C, "only restore authorisation eligibility when the relevant data and affected lifecycle state have been successfully reconciled".
   - **What happened:** reconciliation re-checked uncertain hours only through a gap recorded on an opportunity, so such a lineage would have stayed blocked even after IG's recovery.
   - **Correction** (`OpportunityKeeper._reconcile_uncertain`): every lineage's uncertain hour is re-checked once its complete candle is stored. Its D-25 verdict is applied if no later test is numbered. Otherwise the hour is **left for review** (`review_hours`), which keeps the lineage's opportunities ineligible (D-R2). Every outcome is a new event.
   - Tests: TW3-11; TW3-08 (the review case).

**The 15:11 SELL on 27 Nov.** The 15:00 SELL is now published as a new test. Its lineage's count, though, passes through the 12:00 hour: that hour was built from 9 of 12 candles, and its stored part was clear of the zone, so the missing candles could hide a test or a re-arm. The 15:11 idea is therefore refused under D-R2 (fail closed) until IG's candles for 12:00–12:10 are recovered and reconciled (FL-E1). In production it traded (+9.0 pips, closed by hand at 16:20).
