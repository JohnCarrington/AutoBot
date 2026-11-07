# News

The economic calendar (`news/`), for the big-news rules of design section 6 and the expected direction of section 2.4. The safety rules (not built yet) will read the no-trading windows from here.

## Where it comes from

- **Finnhub's economic calendar** (`GET /calendar/economic`), with the API key in `.env` as `FINNHUB_API_KEY` (never printed, logged or committed; an error is reported by its kind and HTTP status only, because the key travels in the request's address).
- The **price service** looks at the copy on disk every 5 minutes (`news.check_minutes`). It fetches only when the copy is older than 6 hours (`news.refresh_hours`), and never sooner than 60 minutes after the last attempt (`news.retry_minutes`): a few requests a day, never a fast loop. Each fetch covers 7 days back and 14 ahead (`news.fetch_days_back`, `news.fetch_days_ahead`).
- The **copy on disk**, `data/news/calendar.json`, keeps every release fetched so far (a newer fetch updates its figures; releases older than 90 days are dropped). A restart uses it and does not fetch again while it is fresh.
- `.venv/bin/python -m news status` (contacts nobody), `... news fetch` (one request now), `... news windows <from UTC> <to UTC> [--pair GBPUSD]` (contacts nobody).

## Big, medium and small: AutoBot 161's own table

161 classified every release with its own `news_tier_classifier` into BIG, MIDDLE and SMALL. Its table was recovered from the public audit report `news_rest_break_event_study_20261007.md`, which tags every GBP and USD release from 1 January to 7 October 2026 (4,427 releases, 398 distinct names) with 161's tier; each name always had the same tier. The names are Finnhub's own (161's calendar also came from Finnhub).

- **GBP big (11):** BoE Interest Rate Decision, BoE Monetary Policy Report, BoE FPC Meeting Minutes, MPC Meeting Minutes, Inflation Rate MoM, Inflation Rate YoY, Core Inflation Rate MoM, Core Inflation Rate YoY, GDP Growth Rate QoQ Prel, GDP Growth Rate YoY Prel, DMP 1Y CPI Expectations.
- **USD big (16):** Fed Interest Rate Decision, Fed Press Conference, FOMC Minutes, FOMC Economic Projections, CPI, CPI s.a, Inflation Rate MoM, Inflation Rate YoY, Core Inflation Rate MoM, Core Inflation Rate YoY, Non Farm Payrolls, Nonfarm Payrolls Private, Non Farm Payrolls Annual Revision Prel, GDP Growth Rate QoQ Adv, GDP Price Index QoQ Adv, GDP Sales QoQ Adv.
- **Medium:** 20 GBP and 51 USD names (settings `news_tiers.middle_GBP`, `middle_USD`). **Small:** everything else. Medium and small are ignored.
- 161's table only covers GBP and USD. A pair with another currency (for example EUR) needs its lists added before its news counts.

## The no-trading windows

For each **big** release in either currency of a switched-on pair (GBPUSD: GBP and USD): **no new trades from 15 minutes before to 30 minutes after**, and **open trades closed 15 minutes before** (settings `news.big_news_*`). Example: the Bank of England rate decision at 12:00 UK on Thursday 5 November 2026: no new trades 11:45 to 12:30, open trades closed at 11:45.

## The expected direction (design section 2.4)

For each big release: the forecast (Finnhub's `estimate`) against the previous figure. A higher figure is good for the currency, except for names containing one in `news.lower_is_better` (unemployment, jobless claims, claimant count). Good for the pair's first currency (GBP in GBPUSD) means **up**; good for its second (USD) means **down**. The same figures mean **in line**; no figures (speeches, minutes, press conferences) mean **no direction**.

## If the calendar is missing or out of date

If the last good fetch is more than 24 hours old (`news.out_of_date_hours`), or there has never been one, or `FINNHUB_API_KEY` is not set, the price service sends a **Telegram problem alert**, at most every 6 hours while it lasts (`news.alert_every_hours`). **Trading is not blocked by this** (design section 6): the windows use the last calendar on disk.
