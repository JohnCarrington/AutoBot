"""AutoBot's news table (config/news_table.toml): which releases are BIG, MEDIUM
or SMALL. The owner's table from AutoBot 161, copied as data; the matching is
written here (161's code was not copied). See the file's own notes and
docs/SETTINGS.md ("News table").

Matching, in this order (the first row that matches decides):
  0. only releases whose Finnhub impact is in news.table_impacts are matched
     (as on 161: high); any other release is SMALL;
  1. [[override]] rows, each only for its own currency;
  2. [[big]] rows, any currency;
  3. [[middle]] rows, any currency;
  4. otherwise SMALL, and the release is logged once (and kept in
     <news.folder>/unmatched.json) so the owner can place it.
A row matches when every text in all_of is in the lower-cased name (or, for a
name_is row, the name is exactly that, ignoring case), and, if it has
same_day, when another release of the same currency on the same UTC day
matches one of those keyword groups (161: unemployment rate is big only on
payrolls day; a Fed chair speech only on a rate-decision day).
"""

from __future__ import annotations

import json
import logging
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from housekeeping.files import safe_write

log = logging.getLogger("autobot.news")
TABLE_PATH = Path(__file__).resolve().parents[1] / "config" / "news_table.toml"
BIG, MEDIUM, SMALL = "big", "medium", "small"
SECTIONS = (("override", None), ("big", BIG), ("middle", MEDIUM))
UNMATCHED_FILE = "unmatched.json"


class NewsTableError(Exception):
    pass


@dataclass(frozen=True)
class Row:
    section: str                        # override, big or middle
    rule: str
    tier: str                           # big or medium
    currency: str | None                # overrides only
    all_of: tuple[str, ...]
    name_is: str | None
    same_day: tuple[tuple[str, ...], ...]

    def matches_name(self, name: str) -> bool:
        low = name.lower().strip()
        if self.name_is is not None:
            return low == self.name_is.lower()
        return all(k in low for k in self.all_of)


@dataclass(frozen=True)
class Match:
    tier: str
    rule: str                           # the row's rule, or "default_small" / "impact_not_matched"
    row: Row | None


def _group(v: Any, where: str) -> tuple[str, ...]:
    if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
        raise NewsTableError(f"{where}: must be a non-empty list of texts, got {v!r}")
    if any(x != x.lower() for x in v):
        raise NewsTableError(f"{where}: texts must be lower case (names are matched lower-cased), got {v!r}")
    return tuple(x.strip() for x in v)


def load_table(path: str | Path = TABLE_PATH) -> list[Row]:
    """Read and check every row. Raises NewsTableError naming the row and the problem."""
    try:
        raw = tomllib.loads(Path(path).read_text())
    except FileNotFoundError:
        raise NewsTableError(f"The news table {path} does not exist.") from None
    except tomllib.TOMLDecodeError as e:
        raise NewsTableError(f"The news table {path} is not valid TOML: {e}") from None
    unknown = set(raw) - {s for s, _ in SECTIONS}
    if unknown:
        raise NewsTableError(f"Unknown section(s) in the news table: {', '.join(sorted(unknown))}.")
    rows: list[Row] = []
    for section, tier in SECTIONS:
        for i, r in enumerate(raw.get(section, []), 1):
            where = f"[[{section}]] row {i} ({r.get('rule', '?')})"
            allowed = {"rule", "all_of", "name_is", "same_day"} | ({"currency", "tier"} if section == "override" else set())
            extra = set(r) - allowed
            if extra:
                raise NewsTableError(f"{where}: unknown field(s) {', '.join(sorted(extra))}.")
            rule = r.get("rule")
            if not isinstance(rule, str) or not re.fullmatch(r"[a-z0-9_]+", rule or ""):
                raise NewsTableError(f"{where}: rule must be a lower-case name like us_cpi, got {rule!r}")
            if ("all_of" in r) == ("name_is" in r):
                raise NewsTableError(f"{where}: needs exactly one of all_of or name_is.")
            all_of = _group(r["all_of"], f"{where} all_of") if "all_of" in r else ()
            name_is = r.get("name_is")
            if name_is is not None and (not isinstance(name_is, str) or not name_is.strip()):
                raise NewsTableError(f"{where}: name_is must be a name, got {name_is!r}")
            same_day = r.get("same_day", [])
            if not isinstance(same_day, list):
                raise NewsTableError(f"{where}: same_day must be a list of keyword groups")
            groups = tuple(_group(g, f"{where} same_day") for g in same_day)
            currency = None
            row_tier = tier
            if section == "override":
                currency = r.get("currency")
                if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
                    raise NewsTableError(f"{where}: an override needs its currency, like GBP, got {currency!r}")
                row_tier = r.get("tier")
                if row_tier not in (BIG, MEDIUM):
                    raise NewsTableError(f"{where}: tier must be big or medium, got {row_tier!r}")
            rows.append(Row(section, rule, row_tier, currency, all_of, name_is, groups))
    if not rows:
        raise NewsTableError("The news table has no rows.")
    return rows


def classify(rows: list[Row], settings: Any, currency: str | None, name: str, impact: Any,
             same_day_names: Iterable[str] = ()) -> Match:
    """The tier of one release (see the module text for the order)."""
    if str(impact or "").lower() not in settings.news.table_impacts:
        return Match(SMALL, "impact_not_matched", None)
    others = [n.lower() for n in same_day_names if n.lower() != name.lower()]
    for section, _ in SECTIONS:
        for row in rows:
            if row.section != section or (section == "override" and row.currency != currency):
                continue
            if not row.matches_name(name):
                continue
            if row.same_day and not any(all(k in o for k in g) for g in row.same_day for o in others):
                continue
            return Match(row.tier, row.rule, row)
    return Match(SMALL, "default_small", None)


class UnmatchedLog:
    """Logs each release that matches no row once (kept on disk across restarts)."""

    def __init__(self, settings: Any):
        self.path = Path(settings.news.folder) / UNMATCHED_FILE

    def seen(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, ValueError):
            return {}

    def note(self, currency: str | None, name: str, time_utc: str) -> bool:
        key = f"{currency}|{name}"
        seen = self.seen()
        if key in seen:
            return False
        seen[key] = {"currency": currency, "name": name, "first_seen_release_utc": time_utc}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        safe_write(self.path, (json.dumps(seen, indent=1, sort_keys=True) + "\n").encode())
        log.info("News release in no row of the news table, so SMALL: %s %r (release %s). Add it to "
                 "config/news_table.toml to place it.", currency, name, time_utc)
        return True
