"""The economic calendar by hand.

  .venv/bin/python -m news status
      when the calendar was last fetched, and whether it is out of date. Contacts nobody.
  .venv/bin/python -m news fetch
      fetch it from Finnhub now (one request), whatever its age.
  .venv/bin/python -m news windows <from UTC> <to UTC> [--pair GBPUSD]
      the big-news no-trading windows and expected directions between two times. Contacts nobody.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from config.pairs import choose_pair, take_pair_option
from config.settings_loader import load_or_exit
from news.calendar import big_news_windows, status
from news.finnhub import FinnhubNotSetUp, fetch, load_key, read_store
from prices.model import parse_iso, uk_short


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    settings = load_or_exit()
    now = datetime.now(timezone.utc)
    if args == ["status"]:
        st = status(settings, now)
        data = read_store(settings)
        print(f"{'OK' if st.ok else 'PROBLEM'}: {st.why}; {len(data['events'])} releases on disk; "
              f"last attempt {data.get('last_attempt_utc')}" + (f" ({data['last_error']})" if data.get("last_error") else ""))
        return 0 if st.ok else 1
    if args == ["fetch"]:
        try:
            key = load_key()
        except FinnhubNotSetUp as e:
            print(f"Finnhub is not set up: {e}")
            return 3
        r = fetch(settings, key, now)
        print(f"{'FETCHED' if r.ok else 'NOT FETCHED'}: {r.why}" + (f"; {r.received} releases received" if r.ok else ""))
        return 0 if r.ok else 1
    if len(args) == 3 and args[0] == "windows":
        ps = choose_pair(settings, pair)
        p = ps.market.pair
        ws = big_news_windows(settings, p, parse_iso(args[1]), parse_iso(args[2]))
        print(f"Big news for {p} ({p[:3]} and {p[3:]}) from {uk_short(parse_iso(args[1]))} to {uk_short(parse_iso(args[2]))}: {len(ws)}")
        for w in ws:
            print(f"  {uk_short(w.release_utc)}  {w.currency} {w.event}: no new trades {uk_short(w.no_new_trades_from)[-9:]} "
                  f"to {uk_short(w.no_new_trades_until)[-9:]}, open trades closed at {uk_short(w.close_open_trades_at)[-9:]}; "
                  f"expected {w.direction} ({w.direction_reason})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
