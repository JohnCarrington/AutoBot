"""Fails if any setting in config/settings.toml, or any switch in .env, is not
described in docs/SETTINGS.md.

A setting counts as described when docs/SETTINGS.md has a table row whose first
column is the setting's name in backticks, `section.name`, followed by a
non-empty description and value. Each pair's settings are described once, as
`pairs.PAIR.epic` and so on. A switch in .env is described by a row whose first
column is its .env name, e.g. `PAIRS_ON`.

The switches are taken from config/switches.py and .env.example (never the real
.env, which also holds the secrets): both must list the same switches.
"""

import re
import tomllib
from pathlib import Path

from config.settings_loader import DEFAULT_PATH
from config.switches import SWITCHES

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "SETTINGS.md"
EXAMPLE = ROOT / ".env.example"
ROW = re.compile(r"^\|\s*`([a-z_]+(?:\.[A-Za-z0-9_]+)+|[A-Z][A-Z_]+)`\s*\|(.*)\|\s*$")
SECRETS = {"IG_USERNAME", "IG_PASSWORD", "IG_API_KEY", "IG_ACCOUNT_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
           "FINNHUB_API_KEY"}


def _documented():
    rows = {}
    for line in DOC.read_text().splitlines():
        m = ROW.match(line)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            rows[m.group(1)] = cells
    return rows


def _in_settings_file():
    with DEFAULT_PATH.open("rb") as f:
        raw = tomllib.load(f)
    names = set()
    for s, items in raw.items():
        for k, v in items.items():
            if isinstance(v, dict):                     # [pairs.<PAIR>]: one row per field, for every pair
                names |= {f"{s}.PAIR.{field}" for field in v}
            else:
                names.add(f"{s}.{k}")
    return names | set(SWITCHES)


def _in_env_example():
    keys = set()
    for line in EXAMPLE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def test_every_setting_is_described_in_settings_doc():
    missing = sorted(_in_settings_file() - set(_documented()))
    assert not missing, (
        "These settings or switches are not described in "
        f"docs/SETTINGS.md: {', '.join(missing)}"
    )


def test_every_description_is_filled_in():
    rows = _documented()
    empty = sorted(name for name, cells in rows.items()
                   if len(cells) < 2 or not all(cells[:2]))
    assert not empty, f"These rows in docs/SETTINGS.md have an empty description or value: {', '.join(empty)}"


def test_doc_does_not_describe_settings_that_do_not_exist():
    extra = sorted(set(_documented()) - _in_settings_file())
    assert not extra, (
        f"docs/SETTINGS.md describes settings that do not exist: {', '.join(extra)}"
    )


def test_env_example_lists_every_switch_and_nothing_unknown():
    keys = _in_env_example()
    assert set(SWITCHES) <= keys, f"Missing from .env.example: {sorted(set(SWITCHES) - keys)}"
    assert keys - set(SWITCHES) <= SECRETS, f"Unknown keys in .env.example: {sorted(keys - set(SWITCHES) - SECRETS)}"


def test_env_example_switches_are_valid_and_hold_no_secrets(tmp_path):
    from config.settings_loader import load_settings
    st = load_settings(switches_from=EXAMPLE)          # the example's switch values pass the start-up checks
    assert st.switches.pairs_on == ("GBPUSD",)
    for line in EXAMPLE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() in SECRETS:
                assert v.strip() == "", f".env.example must not hold a value for {k.strip()}"
