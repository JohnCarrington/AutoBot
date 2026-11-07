# News

The economic calendar (`news/`), for the big-news rules of design section 6 and the expected direction of section 2.4. The safety rules (not built yet) will read the no-trading windows from here.

## Where it comes from

- **Finnhub's economic calendar** (`GET /calendar/economic`), with the API key in `.env` as `FINNHUB_API_KEY` (never printed, logged or committed; an error is reported by its kind and HTTP status only, because the key travels in the request's address).
- The **price service** looks at the copy on disk every 5 minutes (`news.check_minutes`). It fetches only when the copy is older than 6 hours (`news.refresh_hours`), and never sooner than 60 minutes after the last attempt (`news.retry_minutes`): a few requests a day, never a fast loop. Each fetch covers 7 days back and 14 ahead (`news.fetch_days_back`, `news.fetch_days_ahead`).
- The **copy on disk**, `data/news/calendar.json`, keeps every release fetched so far (a newer fetch updates its figures; releases older than 90 days are dropped). A restart uses it and does not fetch again while it is fresh.
- `.venv/bin/python -m news status` (contacts nobody), `... news fetch` (one request now), `... news windows <from UTC> <to UTC> [--pair GBPUSD]` (contacts nobody).

## Big, medium and small: the news table

AutoBot's own table, `config/news_table.toml`: **the owner's table from AutoBot 161** (the tiers the owner set from their research into how far GBPUSD moved around each release), copied as data from the public audit report `news_impact_table_161.csv` and its README, with five rows added by the owner (7 November 2026): GBP "Interest Rate" (the Bank of England rate decision, as Finnhub named it on 5 November 2026) and GBP "Unemployment Rate" are big; USD "Building Permits Prel", "Existing Home Sales" and "Housing Starts" are placed as small. Every row, and how releases are matched, is in `docs/SETTINGS.md` ("News table").

In short: only high-impact releases (as Finnhub marks them) are matched; overrides first (each for its own currency), then big rules, then medium rules, otherwise small; two same-day rules (the US unemployment rate is big only on payrolls day; a Fed chair speech only on a rate-decision day). A release that matches no row is small and logged once (`data/news/unmatched.json`), so the owner can place it. Medium and small news is ignored for trading.

Because only high-impact releases are matched, a release Finnhub marks medium (for example the BoE Monetary Policy Report and the MPC minutes on 5 November 2026) is not big, even though a big rule names it. This is how 161 worked; `news.table_impacts` can widen it.

## The no-trading windows

For each **big** release in either currency of a switched-on pair (GBPUSD: GBP and USD): **no new trades from 15 minutes before to 30 minutes after**, and **open trades closed 15 minutes before** (settings `news.big_news_*`). Example: the Bank of England rate decision at 12:00 UK on Thursday 5 November 2026: no new trades 11:45 to 12:30, open trades closed at 11:45.

## The expected direction (design section 2.4)

For each big release: the forecast (Finnhub's `estimate`) against the previous figure. A higher figure is good for the currency, except for names containing one in `news.lower_is_better` (unemployment, jobless claims, claimant count). Good for the pair's first currency (GBP in GBPUSD) means **up**; good for its second (USD) means **down**. The same figures mean **in line**; no figures (speeches, minutes, press conferences) mean **no direction**.

## Big releases at the same time

If two or more big releases come out at the same time and their expected directions agree, that is the direction for that time. If they disagree, the **headline release decides**, from the news table's `[[headline]]` order (top first): **rate decision**, **main payrolls**, **private payrolls**, **headline CPI**, **core CPI**; a release in none of these ranks below them all. So a rate decision decides over everything else at that time, main payrolls over private payrolls, and headline CPI over core CPI. If the headline release has no expected direction, there is no expected direction for that time; if several releases share the top place (for example CPI MoM and YoY) and do not agree, there is none either.

Example: Friday 6 November 2026, 13:30: Non Farm Payrolls (forecast 65 above previous 60: good for USD, so GBPUSD down) and Unemployment Rate (4.2, in line) disagree; main payrolls decide: **down**. `python -m news windows <from> <to>` shows the direction for each time.

## If the calendar is missing or out of date

If the last good fetch is more than 24 hours old (`news.out_of_date_hours`), or there has never been one, or `FINNHUB_API_KEY` is not set, the price service sends a **Telegram problem alert**, at most every 6 hours while it lasts (`news.alert_every_hours`). **Trading is not blocked by this** (design section 6): the windows use the last calendar on disk.
