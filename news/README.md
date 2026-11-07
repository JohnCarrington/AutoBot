# news

**What it does:** Keeps the economic calendar from Finnhub (fetched a few times a day by the price service, kept on disk), says which releases are big (AutoBot 161's table), gives the big-news no-trading windows for each pair's currencies and each big release's expected direction, and alerts the owner if the calendar is missing or out of date. Rules: `docs/NEWS.md`.

Files: `finnhub.py` (the fetch and the copy on disk), `calendar.py` (tiers, windows, direction, status), `keeper.py` (run by the price service), `__main__.py` (`python -m news status | fetch | windows`).

**What it must never do:** Never place, change or close a trade. Never print or log the Finnhub key. Never fetch in a fast loop. Never block trading because the calendar is out of date (alert instead). Never contact IG.
