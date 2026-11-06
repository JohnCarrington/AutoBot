"""Safe writes: a crash or power cut at any moment leaves either the old file
or the new one, complete, never a damaged file."""

from __future__ import annotations

import os
from pathlib import Path

TMP_MARK = ".tmp-"


def fsync_dir(folder: Path) -> None:
    fd = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def safe_write(path: Path, data: bytes) -> None:
    """Write the whole new file to a temporary file in the same folder, flush
    it to disk, rename it over the old one in one step, then flush the folder."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}{TMP_MARK}{os.getpid()}")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(path.parent)
