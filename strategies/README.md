# strategies

**What it does:** Holds one subfolder per strategy. Each strategy looks for its own setup and, when it finds one, produces a trade idea. Trade ideas go to the safety part, never straight to IG.

- `slow_grind/`
- `ema_pullback/`
- `bollinger_bounce/`
- `range_trade/`

**What it must never do:** Never send orders to IG directly. Never skip the safety rules. Never run when the analyser has not allowed it.
