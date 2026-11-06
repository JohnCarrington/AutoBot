# levels

**What it does:** Works out the price levels the bot cares about, always with the sell (bid) price, as on Johnny's IG chart (`chart.price`): the daily pivot, R1–R3 and S1–S3, round numbers, the previous day's high and low, London and New York session highs and lows, and hourly turning levels (looking back 2 weeks). Levels within 5 pips of each other are grouped as lining up, and the ones that matter most are marked. It writes one current list for the rest of the bot (`/opt/autobot/data/levels/current.json`), updated each time the price service stores a 5-minute candle. Rules: `docs/LEVELS.md`.

Files: `rules.py` (each rule: candles in, levels out), `current.py` (builds the list from the candle store, writes and reads the file, and the updater the price service calls), `__main__.py` (`python -m levels`).

**What it must never do:** Never contact IG. Never place, change or close a trade. Never decide on its own whether a trade should be taken; it only supplies levels.
