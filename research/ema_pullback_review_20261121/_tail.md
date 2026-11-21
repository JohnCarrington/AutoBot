
# What I couldn't check, and why

1. **The exact age of the price when an order went out.**
   - The records keep IG's time stamp on the triggering price and the time the order was sent, both only to the second, so the ages in 1.5 are each ±1 s.
   - The bot doesn't record when it received the price, so delay between IG and the bot can't be told apart from delay inside the bot.
   - Live prices aren't stored, so the prices between the trigger and IG's fill can't be seen.
2. **Prices inside a 5-minute candle.** Only finished 5-minute candles are stored. So:
   - which came first inside the entry candle, a wick or the entry, is unknown (listed apart in 3.4);
   - a LOOK BACK stop or take profit hit inside the entry candle is marked as uncertain;
   - the spread at a close is known only at the candle's open and close (1.4).
3. **Setups that never reached their entry.** The bot doesn't log them, so the 395 that were cancelled or expired can only be rebuilt from the candles, not checked against a live record. The rebuild matches all 85 logged idea lines and all 24 trades exactly. Every setup that reached its entry while the service was running is in the log, so the service missed none.
4. **The direction rule on setups that never reached their entry.** The bot only checks the rule at the entry, so for those setups there is no "passed" or "blocked" to report. I didn't work out what the rule would have said, because the bot never applied it.
5. **Which switches were on at each moment.** The repository doesn't record the history of `.env`. Period B's extra gates (the hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL) show only where they blocked something (2.3). Section 0 lists only whether each gate's code was present.
6. **Uncommitted code at each start.** The commit per start is HEAD from `git reflog`. Edits that weren't committed can't be ruled out. For every trade, though, the logged step 0, pivot and 100 EMA are reproduced exactly by this code.
7. **The news calendar as it stood at the time.** I used the calendar copy on disk now (fetched again every 6 hours, covering 31 Oct onwards). Event times may have been revised after the fact. The news table itself is unchanged since `f99efe1`.
8. **The LOOK BACK take profit.** It uses the brief's 30 pips. 9 of the 24 live trades were actually sent with 100 pips (`take_profit_kind` "100 for a big-news day", section 1).
9. **How long the LOOK BACK runs.** It follows each blocked setup up to the EMA pullback's Friday 20:30 close, so some results come many hours later (the "LOOK BACK when" column). A live trade could also have been closed by Johnny or hit by a rollover spread, and the LOOK BACK doesn't model either.
10. **Sample size.** 22 bot-closed trades with 3 winners, and every win came on one morning (11 Nov, trades 5–7). That is too few to judge any of the five problems, the analyser states or the wick question on results. The counts show what happened; they don't show what will happen.
