"""The bot's records (design section 9), kept for good: never deleted or rewritten (append only; the summaries are
worked out again from the records).

In records.folder/<PAIR>/ (paper trades, while TRADING is off, in records.folder/<PAIR>/paper/):
  * trades.jsonl: one line when each trade opens and one when it closes (the closing line holds the whole trade:
    strategy, direction, size, market state at the open, open and close times and prices, stop and take profit in
    pips and as prices, the kind of take profit, the reason it opened in one line, how it closed, pips and £, win or
    loss, how long it was open, the best profit it reached, the levels that lined up for a close at a level, and
    for the range trade the half close and the rest);
  * decisions.jsonl: every decision the bot made: ideas (allowed, or blocked with the reasons), the order sender's
    answers (sent, refused and why), the analyser's state changes, the trade manager's decisions, the pause switch;
  * summaries/daily/<UK date>.json and summaries/weekly/<year>-W<week>.json: trades, wins, losses, pips and £,
    by strategy, of the trades closed that day or week.
A trade the owner closed by hand at IG ("closed_by": "owner", how_closed "closed by owner"; owner, 11 November
2026) is kept apart: it is never counted in the bot's trades, wins, losses, pips or £, only in its own
"closed by owner" figures, so the bot is judged on its own exits. A close whose result is unknown (pips None) is
counted in neither.
The one correction made by hand (owner, 11 November 2026): six trades the owner closed on 9 and 10 November were
rewritten or added at IG's figures; the file as it was is kept as trades.jsonl.before-2026-11-11-correction. Then
the bot's own 19 closes of 9 to 11 November whose price or time differed from IG's were corrected to IG's close
time, level and booked £ (each with its "before_correction"); the file before that is
trades.jsonl.before-2026-11-11-ig-prices. Since then every live close is recorded at IG's price and time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

UTC = timezone.utc


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _plain(x: Any) -> Any:
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, datetime):
        return _iso(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


@dataclass
class Summary:
    trades: int
    wins: int
    losses: int
    pips: Decimal
    gbp: Decimal
    by_strategy: dict
    owner_trades: int = 0                   # closed by the owner by hand: never in the figures above
    owner_pips: Decimal = Decimal(0)
    owner_gbp: Decimal = Decimal(0)

    def as_dict(self) -> dict:
        return {"trades": self.trades, "wins": self.wins, "losses": self.losses, "pips": str(self.pips),
                "gbp": str(self.gbp),
                "closed_by_owner": {"trades": self.owner_trades, "pips": str(self.owner_pips), "gbp": str(self.owner_gbp)},
                "by_strategy": {k: {kk: str(vv) if isinstance(vv, Decimal) else vv
                                                          for kk, vv in v.items()} for k, v in self.by_strategy.items()}}


class Book:
    def __init__(self, settings: Any, paper: bool = False):
        from zoneinfo import ZoneInfo
        self.s, self.paper = settings, paper
        tz = settings.hours.timezone
        self.uk = ZoneInfo(tz) if isinstance(tz, str) else tz
        base = Path(settings.records.folder) / settings.market.pair
        self.folder = base / "paper" if paper else base
        self.trades_file = self.folder / "trades.jsonl"
        self.decisions_file = self.folder / "decisions.jsonl"

    def _append(self, path: Path, row: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(_plain(row)) + "\n")

    # ---- trades -------------------------------------------------------------------------------

    def opened(self, record: dict) -> None:
        self._append(self.trades_file, {"event": "opened", "paper": self.paper} | record)

    def closed(self, record: dict) -> None:
        self._append(self.trades_file, {"event": "closed", "paper": self.paper} | record)

    def closed_trades(self) -> list[dict]:
        if not self.trades_file.exists():
            return []
        return [r for r in (json.loads(x) for x in self.trades_file.read_text().splitlines()) if r["event"] == "closed"]

    # ---- decisions --------------------------------------------------------------------------------

    def decision(self, kind: str, t: datetime, **data: Any) -> None:
        self._append(self.decisions_file, {"time_utc": _iso(t), "kind": kind, "paper": self.paper} | data)

    # ---- summaries ------------------------------------------------------------------------------------

    def _uk_day(self, iso: str) -> date:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(self.uk).date()

    def summary(self, first: date, last: date) -> Summary:
        """The trades closed from UK day `first` to `last` (both included)."""
        chosen = [r for r in self.closed_trades() if first <= self._uk_day(r["closed_utc"]) <= last]
        known = [r for r in chosen if r.get("pips") is not None and r.get("gbp") is not None]
        owner = [r for r in known if is_owner_close(r)]
        rows = [r for r in known if not is_owner_close(r)]
        by: dict = {}
        for r in rows:
            b = by.setdefault(r["strategy"], {"trades": 0, "wins": 0, "losses": 0, "pips": Decimal(0), "gbp": Decimal(0)})
            b["trades"] += 1
            b["wins"] += Decimal(r["gbp"]) > 0
            b["losses"] += Decimal(r["gbp"]) < 0
            b["pips"] += Decimal(r["pips"])
            b["gbp"] += Decimal(r["gbp"])
        return Summary(len(rows), sum(Decimal(r["gbp"]) > 0 for r in rows), sum(Decimal(r["gbp"]) < 0 for r in rows),
                       sum((Decimal(r["pips"]) for r in rows), Decimal(0)), sum((Decimal(r["gbp"]) for r in rows), Decimal(0)),
                       by, len(owner), sum((Decimal(r["pips"]) for r in owner), Decimal(0)),
                       sum((Decimal(r["gbp"]) for r in owner), Decimal(0)))

    def today(self, now: datetime) -> Summary:
        d = now.astimezone(self.uk).date()
        return self.summary(d, d)

    def write_daily(self, day: date) -> Summary:
        s = self.summary(day, day)
        self._write(self.folder / "summaries" / "daily" / f"{day.isoformat()}.json", {"day": day.isoformat()} | s.as_dict())
        monday = day - timedelta(days=day.weekday())
        w = self.summary(monday, day)                       # the week so far
        year, week, _ = day.isocalendar()
        self._write(self.folder / "summaries" / "weekly" / f"{year}-W{week:02d}.json",
                    {"week": f"{year}-W{week:02d}", "from": monday.isoformat(), "to": day.isoformat()} | w.as_dict())
        return s

    def _write(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1) + "\n")
        tmp.replace(path)


def is_owner_close(r: dict) -> bool:
    """A trade the owner closed by hand (kept apart from the bot's own exits everywhere)."""
    return r.get("closed_by") == "owner" or r.get("how_closed") == "closed by owner"


def daily_text(pair: str, day: date, s: Summary, week: Summary, paper: bool) -> str:
    """The daily summary for Telegram, in the trade messages' format (Telegram's HTML: bold labels)."""
    from alerts.trades import item, items, money, pips
    lines = ["[AutoBot] 📊 DAILY SUMMARY", item("Date", f"{day:%a %d %b %Y}"), item("Pair", pair)]
    if paper:
        lines.append(item("Mode", "paper trades (TRADING is off)"))
    lines += [items(("Trades", s.trades), ("Won", s.wins), ("Lost", s.losses)),
              item("PnL", f"{pips(s.pips)} | {money(s.gbp)}")]
    for name, b in sorted(s.by_strategy.items()):
        lines.append(item(name, f"{b['trades']} trade{'s' if b['trades'] != 1 else ''} | {pips(b['pips'])} | {money(b['gbp'])}"))
    lines.append(item("Week so far", f"{week.trades} trade{'s' if week.trades != 1 else ''} | {pips(week.pips)} | {money(week.gbp)}"))
    if s.owner_trades:
        lines.append(item("Closed by you (not counted)",
                          f"{s.owner_trades} trade{'s' if s.owner_trades != 1 else ''} | {pips(s.owner_pips)} | {money(s.owner_gbp)}"))
    return "\n".join(lines)
