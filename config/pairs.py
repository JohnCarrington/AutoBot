"""Currency pairs. Every part of the bot works on ONE pair, given to it as
settings.for_pair(name): the same settings, plus that pair's own

  market.pair, market.epic          e.g. "GBPUSD", "CS.D.GBPUSD.TODAY.IP"
  market.pip_size                   one pip in the real price (0.0001; 0.01 for JPY pairs)
  market.price_scale                IG's price = real price x this (GBPUSD 10000:
                                    IG's 13354.4 is 1.33544)
  market.points_per_pip             pip_size x price_scale: pips -> IG's points
  candles.folder                    <candles folder>/<PAIR>/   (each pair's own store)
  levels.folder                     <levels folder>/<PAIR>/
  history.pair_folder               <history folder>/<PAIR>/   (this pair's fill records)

The history door's files (budget ledger, IG's allowance, block marker) stay in
the history folder itself: the budget and IG's allowance are SHARED by all pairs.

The plain settings (without a pair) have no market, so no part can run without
being told its pair. Which pairs are switched on is in .env (config/switches.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PAIR_NAME = re.compile(r"^[A-Z]{6}$")


@dataclass(frozen=True)
class Pair:
    name: str
    epic: str
    pip_size: Decimal
    price_scale: int

    @property
    def points_per_pip(self) -> Decimal:
        x = self.pip_size * self.price_scale
        return Decimal(int(x)) if x == x.to_integral_value() else x.normalize()

    def real_price(self, ig_points: Decimal) -> Decimal:
        """IG's price in points -> the real exchange rate (e.g. 13354.4 -> 1.33544)."""
        return Decimal(ig_points) / self.price_scale


def pip_size(v: Any) -> Decimal:
    if not isinstance(v, str):
        raise ValueError(f'must be written in quotes, like "0.0001", got {v!r}')
    try:
        d = Decimal(v)
    except InvalidOperation:
        raise ValueError(f"must be a number, got {v!r}") from None
    if not d.is_finite() or d <= 0 or d > 1:
        raise ValueError(f"must be above 0 and at most 1, got {v}")
    return d


class _View:
    """A read-only section with some values replaced."""

    def __init__(self, name: str, base: Any, **over: Any):
        object.__setattr__(self, "_name", name)
        for k, v in vars(base).items():
            if not k.startswith("_"):
                object.__setattr__(self, k, v)
        for k, v in over.items():
            object.__setattr__(self, k, v)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("settings cannot be changed while the bot is running")

    def __repr__(self) -> str:
        return f"<settings [{self._name}]>"


class PairSettings:
    """The settings for one pair (see the module text)."""

    def __init__(self, base: Any, pair: Pair):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "pair", pair)
        object.__setattr__(self, "market", _View("market", type("M", (), {})(), pair=pair.name, epic=pair.epic,
                                                 pip_size=pair.pip_size, price_scale=pair.price_scale,
                                                 points_per_pip=pair.points_per_pip))
        object.__setattr__(self, "candles", _View("candles", base.candles,
                                                  folder=Path(base.candles.folder) / pair.name))
        object.__setattr__(self, "levels", _View("levels", base.levels, folder=Path(base.levels.folder) / pair.name))
        object.__setattr__(self, "history", _View("history", base.history,
                                                  pair_folder=Path(base.history.folder) / pair.name))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("settings cannot be changed while the bot is running")

    def for_pair(self, name: str) -> "PairSettings":
        return self._base.for_pair(name)

    def __repr__(self) -> str:
        return f"<settings for {self.pair.name}>"


def choose_pair(settings: Any, name: str | None) -> "PairSettings":
    """For the command-line tools: the pair named, or the only pair switched on."""
    if name:
        return settings.for_pair(name.upper())
    on = list(settings.switches.pairs_on)
    if len(on) != 1:
        raise SystemExit(f"More than one pair is switched on ({', '.join(on)}): say which with --pair.")
    return settings.for_pair(on[0])


def take_pair_option(args: list[str]) -> tuple[str | None, list[str]]:
    """Take "--pair XXXYYY" out of a command line; returns (pair or None, the rest)."""
    rest, pair, i = [], None, 0
    while i < len(args):
        if args[i] == "--pair" and i + 1 < len(args):
            pair, i = args[i + 1], i + 2
        else:
            rest.append(args[i])
            i += 1
    return pair, rest


def check_same_pair(settings: Any, store: Any) -> None:
    """Stop at once if a part is given another pair's candle store: a pair's
    store is always in a folder named after the pair (<candles folder>/<PAIR>/)."""
    pair, folder = settings.market.pair, Path(store.folder)
    if folder.name != pair:
        raise ValueError(f"Pair mix-up: these settings are for {pair}, but the candle store given is "
                         f"{folder} (a {pair} store is always in a folder named {pair}).")
