# safety

**What it does:** Checks every trade idea before it can become an order: the trade size, how many trades are open, trading hours (UK time), big news and the off switch. Only ideas that pass every check go to the order sender. It also says when open trades must be closed (20:30, and 15 minutes before big news).

**What it must never do:** Never let a trade through when any check fails or when it is unsure. Never be bypassed or switched off by a strategy. Never allow a trade to be held overnight.
