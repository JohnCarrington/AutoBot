# rejection

**What it does:** Works out, step by step, whether price has been rejected at a level or the Bollinger band, on the sell (bid) price as on Johnny's IG chart. Each step is a timestamped event: pierce (a level reached within 3 pips counts; for the bounce the band needs a real pierce, for the range trade a band reached within 3 pips counts), reversal candle, confirmation candle, live trigger, cancelled or expired. It runs both the bounce and the quicker range-trade version, in both directions. It records how big the reversal candle was against the piercing candle and which levels lined up, and marks whether the setup counts under the reversal watch windows, but never filters on any of these. Candles with a spread spike cannot start or cancel a setup. It is shared by the analyser, the strategies and the trade manager, so all three use the same answer. Rules: `docs/REJECTION.md`.

Files: `watch.py` (the watcher: every rule, the watch windows, the spread rule), `replay.py` (runs it over stored candles), `__main__.py` (`python -m rejection <from> <to>`).

**What it must never do:** Never contact IG. Never place, change or close a trade. Never keep its own private copy of the rules for a single user: there is one rejection check, used by everyone.
