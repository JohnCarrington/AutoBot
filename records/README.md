# records

**What it does:** The bot's records (`book.py`, design section 9), kept for good: every trade when it opens and when it closes (strategy, direction, size, market state, open and close times and prices, stop and take profit in pips and as prices, the kind of take profit, the reason in one line, how it closed, pips and £, win or loss, how long it was open, the best profit it reached, the levels that lined up, the range trade's half close and rest), every decision (ideas and why they were blocked, the order sender's answers, the analyser's state changes, the trade manager's decisions, the pause switch), and the daily and weekly summaries. Paper trades (while `TRADING` is off) are kept apart in `paper/`.

**What it must never do:** Never place, change or close a trade. Never delete or rewrite a past record.
