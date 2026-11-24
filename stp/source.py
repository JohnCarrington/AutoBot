"""Where the integration reads STP's opportunities from: the tracker's current.json (planner.folder/<PAIR>/), read
only. A missing, unreadable or damaged file gives None: the levels add nothing and the authorisation check refuses."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


class FileSource:
    """The live file, read again only when it changes (its modification time and size)."""

    def __init__(self, settings: Any):
        self.path = Path(settings.planner.folder) / settings.market.pair / "current.json"
        self._seen: tuple | None = None
        self._state: dict | None = None

    def version(self) -> tuple | None:
        try:
            st = self.path.stat()
        except OSError:
            return None
        return (st.st_mtime_ns, st.st_size)

    def state_at(self, t: datetime | None = None) -> dict | None:
        v = self.version()
        if v is None:
            self._seen, self._state = None, None
            return None
        if v != self._seen:
            try:
                got = json.loads(self.path.read_text())
                self._state = got if isinstance(got, dict) and isinstance(got.get("opportunities"), list) else None
            except (OSError, ValueError):
                self._state = None
            self._seen = v
        return self._state


class ReplaySource:
    """Offline (tests and replays): the tracker's file as it stood at each moment, from snapshots taken after each
    tracker run: state_at(t) is the latest snapshot written at or before t."""

    def __init__(self, snapshots: list[dict], now: Callable[[], datetime] | None = None):
        from prices.model import parse_iso
        self.snaps = sorted(((parse_iso(x["written_utc"]), x) for x in snapshots if x.get("written_utc")),
                            key=lambda p: p[0])
        self.now = now

    def _at(self, t: datetime | None) -> datetime | None:
        return self.now() if self.now is not None else t

    def version(self, t: datetime | None = None) -> Any:
        s = self.state_at(t)
        return None if s is None else s.get("written_utc")

    def state_at(self, t: datetime | None = None) -> dict | None:
        t = self._at(t)
        best = None
        for w, x in self.snaps:
            if t is not None and w <= t:
                best = x
            else:
                break
        return best


def source_for(settings: Any) -> FileSource | None:
    """The live source while STP_AUTHORISES_ENTRIES is on, else None (nothing is read)."""
    if getattr(getattr(settings, "switches", None), "stp_authorises_entries", False):
        return FileSource(settings)
    return None
