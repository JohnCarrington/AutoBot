"""Logging for the whole bot.

* Every line shows UK time (GMT or BST).
* Log files are rotated by size AND by age: a new file is started when the
  current one reaches housekeeping.log_max_file_mb, or is older than
  housekeeping.log_new_file_every_hours. At most housekeeping.log_keep_files
  old files are kept, and any older than housekeeping.log_max_age_days are
  deleted. So logs can never use more than about
  log_max_file_mb x (log_keep_files + 1) of disk.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


class UKTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        t = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone(UK)
        return t.strftime("%Y-%m-%d %H:%M:%S %Z")


class SizeAndAgeRotatingHandler(RotatingFileHandler):
    """Starts a new file when the current one is too big or too old, and
    deletes old files beyond the count or age limits."""

    def __init__(self, path: Path, max_bytes: int, new_file_every_seconds: float,
                 keep_files: int, max_age_seconds: float, clock=time.time):
        self.new_file_every = new_file_every_seconds
        self.max_age = max_age_seconds
        self.clock = clock
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(path, maxBytes=max_bytes, backupCount=keep_files, encoding="utf-8")
        self.opened_at = self._file_started()
        self.remove_old_files()

    def _stamp(self) -> Path:
        return Path(self.baseFilename + ".started")

    def _file_started(self) -> float:
        """When the current log file was started (kept in <log>.started)."""
        try:
            return float(self._stamp().read_text())
        except (FileNotFoundError, ValueError):
            now = self.clock()
            self._stamp().write_text(str(now))
            return now

    def shouldRollover(self, record) -> bool:
        if self.clock() - self.opened_at >= self.new_file_every and os.path.getsize(self.baseFilename) > 0:
            return True
        return bool(super().shouldRollover(record))

    def doRollover(self) -> None:
        super().doRollover()
        self.opened_at = self.clock()
        self._stamp().write_text(str(self.opened_at))
        self.remove_old_files()

    def remove_old_files(self) -> None:
        base = Path(self.baseFilename)
        for n in range(1, self.backupCount + 50):
            p = base.with_name(f"{base.name}.{n}")
            if not p.exists():
                continue
            if n > self.backupCount or self.clock() - p.stat().st_mtime > self.max_age:
                p.unlink()


def setup_logging(hk: Any, name: str = "autobot", *, console: bool = True,
                  level: int = logging.INFO) -> SizeAndAgeRotatingHandler:
    """Send all of the bot's log lines to <log_folder>/<name>.log (rotated) and,
    if asked, to the screen."""
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        if getattr(h, "_autobot", False):
            root.removeHandler(h)
            h.close()
    fmt = UKTimeFormatter(FORMAT)
    handler = SizeAndAgeRotatingHandler(
        Path(hk.log_folder) / f"{name}.log",
        max_bytes=hk.log_max_file_mb * 1024 * 1024,
        new_file_every_seconds=hk.log_new_file_every_hours * 3600,
        keep_files=hk.log_keep_files,
        max_age_seconds=hk.log_max_age_days * 86400,
    )
    handler.setFormatter(fmt)
    handler._autobot = True
    root.addHandler(handler)
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        ch._autobot = True
        root.addHandler(ch)
    # The streaming library is quiet unless asked; keep it that way.
    logging.getLogger("lightstreamer").setLevel(logging.WARNING)
    return handler
