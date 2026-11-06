# trade_manager

**What it does:** Looks after each open trade from the moment it is opened until it closes: for example, closing part of a range trade at the opposite band, and closing trades at 20:30 or before big news when the safety part says so.

**What it must never do:** Never open new trades. Never widen or remove a stop loss. Never touch a trade the bot did not open.
