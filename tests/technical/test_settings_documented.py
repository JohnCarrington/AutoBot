"""Fails if any setting in config/settings.toml is not described in docs/SETTINGS.md.

A setting counts as described when docs/SETTINGS.md has a table row whose first
column is the setting's name in backticks, `section.name`, followed by a
non-empty description and value.
"""

import re
import tomllib
from pathlib import Path

from config.settings_loader import DEFAULT_PATH

DOC = Path(__file__).resolve().parents[2] / "docs" / "SETTINGS.md"
ROW = re.compile(r"^\|\s*`([a-z_]+\.[a-z_]+)`\s*\|(.*)\|\s*$")


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
    return {f"{s}.{k}" for s, items in raw.items() for k in items}


def test_every_setting_is_described_in_settings_doc():
    missing = sorted(_in_settings_file() - set(_documented()))
    assert not missing, (
        "These settings are in config/settings.toml but not described in "
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
        f"docs/SETTINGS.md describes settings that are not in config/settings.toml: {', '.join(extra)}"
    )
