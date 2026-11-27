# Review R3.1: live price continuity (review of `b84d6d6`, 27 November 2026)

> **Superseded in part by `REVIEW_R3_2.md` (review of `fec364b`):** a candle built from the live prices never stands in for IG's candle, because its completeness cannot be established. The local record and the stall wiring described below were removed.

**Verdict: confirmed defect, in two parts, both corrected.** Reproduced with failing functional tests on `b84d6d6` (`review_R3_1_tests_before_fix.txt`).

No strategy confirmation, forecasting, entry zone, stop, take profit or trade management changed. Nothing is deployed.

## What `b84d6d6` did

`Trading._forming` marked a candle as covered when the previous forming candle ended exactly at its start (`p.end == start`). The engine then offered that candle, `previous_partial`, as a stand-in for a finished candle IG had not yet published.

## Findings

1. **Adjacent timestamps do not prove continuity.** A stream drop and reconnection inside the candle, or across the boundary before it, left `p.end == start` true. The candle counted as covered even though the prices during the outage were never seen.
2. **The engine never sees every price.** The price service hands the engine only the feed's **latest** tick, once a second (`prices/service.py every_second → Trading.on_price(feed.last_tick)`). Production averages about 0.86 ticks a second, with bursts of several in one second. The engine's candle therefore misses any high or low that lasts less than a second, even on a perfectly healthy stream.

**Reproduced on `b84d6d6`.** The test drives the real stream, the real feed, the engine's once-a-second path, the real `Trading._place` and the real STP check, on a store that lacks the 10:00 candle.

| Test | Situation | `b84d6d6` | Now |
|---|---|---|---|
| R31-01 | disconnection and reconnection inside the candle | **authorised** | refused (PD-5) |
| R31-02 | interruption across the boundary into the candle | **authorised** | refused (PD-5) |
| R31-03 | IG's library reports STALLED inside the candle | not detected (no stall event existed) | refused (PD-5) |
| R31-04 | service restart during the candle | refused | refused |
| R31-05 | the destination touched and gone within one second | **authorised** (the sample missed it) | refused: destination reached |
| R31-06 | clean candle seen whole, IG's normal publication delay | authorised | authorised (preserved) |
| R31-07 | first price 40 s after the boundary, unbroken stream | authorised | authorised (preserved) |
| R31-08 | repeated identical prices | authorised | authorised (preserved) |
| R31-09 | IG then publishes the authoritative candle | IG's candle decides | IG's candle decides |

## The existing mechanisms used (no new number)

- **IG's stream sends every price change.** On an unbroken connection, no price means no change.
- **Every new connection** (first connect, reconnect after a drop, re-login) already calls `PriceFeed.new_connection`.
- **A drop** goes through `PriceStream._reconnect`.
- **IG's Lightstreamer library reports `STALLED`** (until now only logged).

## Correction (smallest)

- **`prices/live.py` (new) `LiveCandles`**, kept by the price feed. For each 5-minute candle it keeps the high and low from **every** price the feed receives (`PriceFeed.on_tick`), not the once-a-second sample.
  - A candle is **whole** only when one connection delivered prices without interruption from before it began until after it ended.
  - The first price on a connection starts coverage from the **next** candle.
  - Any break ends coverage at once.
- **`ig/stream.py`:** a `Stalled` event emitted on `STALLED`, and an `on_interruption` callback called on every drop (`_reconnect`) and every stall.
- **`prices/feed.py`:** `new_connection` and the new `interrupted()` end coverage.
- **`prices/service.py`:** wires `on_interruption` to every feed, and gives the engine `feed.live.observed`.
- **`trading/engine.py`:** `_place` offers the STP check the just-finished candle only from the feed's record and only if it is whole (`_observed_finished`). The engine's own continuity guess from `b84d6d6` is removed.
- **`stp/authorise.py`:** unchanged from R3. Any finished interval neither stored nor offered whole refuses.

Once IG publishes the candle, the store holds it and decides. The live record is never stored and never used for anything else.

## Tests

- **Functional R31-01..09:** `tests/functional/test_stp_live_continuity_20261127.py`, the real stream and feed through the pretend IG transport.
- **Technical TR3-06, rewritten:** the live record's coverage rules. It replaces the `b84d6d6` test of the engine bookkeeping that R3.1 removes. That test was added in Phase 2, not part of the original suite.
- **Focused regression (STP, lifecycle, stream, candles, trading, live entries):** 519 passed, 3 skipped. The full suite is in the commit's hook.
