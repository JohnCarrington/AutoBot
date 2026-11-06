"""Free disk space warning (housekeeping.min_free_disk_mb)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Callable

log = logging.getLogger("autobot.housekeeping.disk")


def free_mb(path: Path) -> int:
    p = Path(path)
    while not p.exists():
        p = p.parent
    return shutil.disk_usage(p).free // (1024 * 1024)


def check_free_space(path: Path, min_free_mb: int, warn: Callable[[str], None] | None = None,
                     measure: Callable[[Path], int] = free_mb) -> int:
    """Write a warning if free space is below the set level. Returns free MB."""
    free = measure(path)
    if free < min_free_mb:
        (warn or log.warning)(f"LOW DISK SPACE: {free} MB free on the disk holding {path}, "
                              f"below the warning level of {min_free_mb} MB.")
    return free
