"""Reads KEY=value lines from /opt/autobot/.env.

.env holds the IG secrets AND the switches (config/switches.py). This module
only splits the file into keys and values; it never prints or logs anything.

Lines starting with # are comments. Values may be in quotes. A # inside a
value is kept (passwords may contain #).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
# Tests point this at a pretend file, so they never read the real .env.
ENV_PATH_VAR = "AUTOBOT_ENV_FILE"


def env_path() -> Path:
    return Path(os.environ.get(ENV_PATH_VAR) or ENV_PATH)


def parse(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values
