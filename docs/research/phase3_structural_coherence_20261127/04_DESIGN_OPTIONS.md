# 4. Alternative design options and their implications

Each option is shown on named trades from Tables B1/B2. Counts refer to the 86 actual trades and the 416
confirmed ideas, 18–27 Nov. The trade lists are evidence of mechanism. They are not forecasts (§6.1).

## A. Where the structural role of a zone comes from

| Option | Description | Implications |
|---|---|---|
| **A-1 STP labels + lifecycle (recommended)** | Opposing = an STP opportunity labelled in the other direction. Position measured against the zone. Breaks from STP's D-20 events. | Reuses STP exactly. It is deterministic and auditable from current.json. Two-direction zones are handled by S5. |
| A-2 Price-path role inference | The role (resistance/support) is inferred from the side price approached the zone from, using 5m candles over N days, and flips on a confirmed break. | **Rejected after testing** (`evidence/scripts/classify_price_path_rejected.py`). The role changed with the look-back (3 vs 5 days). Visits from earlier days set the role (e.g. 26 Nov 13093–103 came out "unknown" at 5 days). A sweep through a zone looked like a crossing until visit grouping was added. It is a new structural algorithm, which the brief rules out. |
| A-3 All structural levels (STP candidate zones, pivots) | Treat every level in STP's map as a barrier. | This is a blanket filter. Phase 1 showed it refuses the 25 Nov +£614 sweep (pivot 23.7 and candidate zones ahead) and the +£200 slow grind. |

## B. What counts as "within unresolved opposing" (S4)

| Option | Rule | Bot trades refused (recorded result) | Owner closes | Comment |
|---|---|---|---|---|
| B-1 AT only (≈ Phase 1 C-b) | Entry inside or within NEAR of an unbroken opposing zone, or against a confirmed break | 8, all losers: 23 Nov 06:00 −14.6, 12:26 −12.0, 12:30 −13.5, 13:00 −12.0; 25 Nov 18:02 −15.0, 19:10 −5.7; 26 Nov 11:45 −6.0, 11:55 −15.0 | 25 Nov 12:25 (−6.0) | It misses continuation *through* an unconfirmed barrier. |
| **B-2 AT + PAST-unconfirmed (recommended)** | B-1, plus past the far edge of an opposing zone STP holds ACTIVE without a D-20 break | 11, all losers: B-1 + 20 Nov 13:25 −15.0, 23 Nov 06:45 −12.0, 25 Nov 18:45 −5.1 | + 20 Nov 13:10 (−26.1), 27 Nov 15:47 (+4.3) | Covers the brief's "continuation without evidence that an opposing zone had been overcome". Cost: break continuations wait for the hourly D-20 close. On 27 Nov the SELLs from 13:20 waited until 15:00 (§6.3). |
| B-3 B-2 + WAITING zones PAST | Also through opposing zones never touched since publication | same trades as B-2: no trade in the window was past an untouched opposing WAITING zone | — | No evidence for it. It would count zones price never reached since publication as "not overcome". Not recommended. |

## C. Reversal at a contested zone (OD-33 pairs)

| Option | Rule | Effect |
|---|---|---|
| **C-1 S5 exemption (recommended)** | A reversal-family idea whose rejection reached a zone that also carries a live same-direction opportunity is permitted. | 26 Nov 06:01 BUY +5.0 and 06:30 SELL −7.3, and 27 Nov 15:11 SELL (owner +9.0), are permitted. It preserves OD-33 (STP lets the strategy's confirmation decide). |
| C-2 No exemption (≈ Phase 1 C-a) | Any live opposing member at the zone defers. | It defers all three above. In effect it vetoes reversals at every two-direction zone, and from 24 Nov most zones are two-direction. That is close to a blanket veto: the 26 Nov and 27 Nov S5 ideas (34) would all be deferred. |
| C-3 Exemption for every family | Continuation and breakout ideas at a contested zone are also exempt. | In the window no trade differs from C-1. 26 Nov 11:45 breakout SELL −6.0 and 11:55 slow grind SELL −15.0 stay S4(c), against STP's upward break. It removes protection with no evidence for it. |

## D. Approaching an opposing zone (S3)

| Option | Effect |
|---|---|
| **D-1 Record only (recommended)** | S3 permits and is journalled. Distance belongs to the room rule (§3.9), which keeps the two rules independently testable. |
| D-2 Watch & Wait | It would also defer 26 Nov 12:51 bounce 5m SELL −6.4 (1.6 pips above the contested zone) and 10 ideas. The window has one trade of evidence. |

## E. Breakouts into an unresolved zone

| Option | Effect |
|---|---|
| **E-1 Same SCA rule (recommended)** | A breakout AT/PAST an unresolved opposing zone waits for STP's D-20 break. The strategy's 6-candle pullback window usually expires first, so in practice it is a refusal: 26 Nov 11:45 SELL −6.0. The 24 Nov 08:55 +50 breakout (no opposing zone) is unaffected. |
| E-2 Accept the strategy's 5m breakout as the break | It mixes timeframes and duplicates STP's break rule with a new one, so it is a new threshold. Not recommended. |

## F. STP unavailable

| Option | Effect |
|---|---|
| **F-1 Fail open to S2, journalled (recommended)** | Trading continues as today. The SCA cannot become a blanket veto through an outage. |
| F-2 Fail closed | A planner outage or a stale file stops all ten strategies until STP recovers. This is a blanket veto by outage. |

## G. Opposite positions

| Option | Effect |
|---|---|
| **G-1 Record only (recommended)** | `opposite_open` on every assessment. No refusal by direction alone. |
| G-2 An opposite entry needs a non-neutral justifying state (S1/S5/S6/S7) | It refuses the 14 neutral opposite entries: 10 bot losers and 4 bot winners (23 Nov 14:39 EMA pullback +30.0, 10:57 slow grind +20.0, 09:10 sweep +12.2, 20 Nov 07:30 sweep +7.5). It is a directional rule. |

## H. Build base

| Option | Effect |
|---|---|
| **H-1 On top of the reviewed Phase 2 build (recommended)** | One lineage/membership reader. Data-gap semantics reused. It waits for Phase 2's review and deployment. |
| H-2 On fadf228 now | Earlier, but membership has to be rewritten when Phase 2 lands, and there is a risk of disagreeing with the gate. |

## I. Room rule

| Option | Effect |
|---|---|
| **I-1 Not adopted now (recommended)** | The evidence is 2 bot winners vs 2 losers (§3.9). |
| I-2 R (all opposing zones ahead) | It refuses 23 Nov 01:47 +20.0, 26 Nov 14:22 +2.1, 25 Nov 11:00 −12.0, 26 Nov 12:51 −6.4. |
| I-3 R-b (contested pairs ignored) | It refuses +20.0, +2.1, −12.0. |
