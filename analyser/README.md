# analyser

**What it does:** Reads the candles, the levels and the rejection part, decides which of the five market states the market is in, and decides which strategies are allowed to look for trades right now.

**Built so far (Stage 7, part 1):** the indicators on the 5-minute and hourly candles (`indicators.py`), the direction rule (`direction.py`), whether the data is ready, warming up or out of date (`data_status.py`), and the answer at one moment (`report.py`, `python -m analyser <UTC time>`). **Part 2:** the five market states (`features.py`, `states.py`, `market_state.py`; `python -m analyser.states_timeline <from> <to>`). **The hourly read** (`hourly_read.py`; owner, 14 November 2026): ranging, sell-off or rally on the hourly chart, which the trend strategies must agree with. See `docs/ANALYSER.md`.

**What it must never do:** Never place, change or close a trade. Never let a strategy run that is not allowed in the current market state. Never contact IG.
