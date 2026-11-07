"""Show the analyser's indicators, direction and data status at one or more
UTC times, from the stored candles. Contacts nobody.

  .venv/bin/python -m analyser 2026-11-06T13:00:00Z [more times ...]
"""

from __future__ import annotations

import sys
from decimal import Decimal

from analyser.report import AnalyserReport, analyse
from config.settings_loader import load_or_exit
from prices.model import parse_iso, uk_short
from prices.store import CandleStore


def _n(v: Decimal | None, places: str = "0.1") -> str:
    return "-" if v is None else str(v.quantize(Decimal(places)))


def show(r: AnalyserReport) -> list[str]:
    d = r.direction
    out = [f"At {uk_short(r.as_of)}:",
           f"  direction: {d.side.upper()} ({d.reason})",
           f"  price {_n(d.price)} = {d.price_from}; daily pivot {_n(d.pivot)}; "
           f"{d.ema_name} {_n(d.ema)}{'' if d.ema_ready else ' (warming up)'}",
           f"  data: {r.data.describe()}"]
    for tf, f in r.indicators.items():
        v = f.values
        warm = lambda name: "" if f.ready[name] else "*"
        emas = ", ".join(f"{k[4:]} {_n(x)}{warm(k)}" for k, x in v.items() if k.startswith("ema_"))
        out.append(f"  {tf} at candle {uk_short(f.candle.start) if f.candle else '-'} "
                   f"({f.candles_used} candles): EMAs {emas}")
        out.append(f"      Bollinger {_n(v['bb_lower'])} / {_n(v['bb_middle'])} / {_n(v['bb_upper'])}"
                   f"{warm('bollinger')}; MACD {_n(v['macd_line'], '0.01')} signal {_n(v['macd_signal'], '0.01')}"
                   f" histogram {_n(v['macd_histogram'], '0.01')}{warm('macd')}; RSI {_n(v['rsi'])}{warm('rsi')}")
    out.append("  (* = warming up)")
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 2
    settings = load_or_exit()
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    for a in args:
        print("\n".join(show(analyse(settings, store, parse_iso(a)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
