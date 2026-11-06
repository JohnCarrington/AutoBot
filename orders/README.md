# orders

**What it does:** Sends orders to IG. Every order always has a stop loss and a take profit attached. It only ever touches the bot's own trades.

**What it must never do:** Never send an order without a stop loss and a take profit. Never change or close a trade the bot did not open (for example, a trade placed by hand). Never send an order that has not passed the safety rules.
