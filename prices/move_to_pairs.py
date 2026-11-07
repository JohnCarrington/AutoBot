"""One-off move of the existing GBPUSD candles and records into the per-pair
folders. Contacts nobody.

  .venv/bin/python -m prices.move_to_pairs plan     shows what would move; changes nothing
  .venv/bin/python -m prices.move_to_pairs go       moves it, then proves nothing was lost

What moves (everything that belongs to GBPUSD alone):
  data/candles/{5m,1h,4h,1d,1w}, gaps.csv, archive_22h_layout -> data/candles/GBPUSD/
  data/levels/current.json                                    -> data/levels/GBPUSD/
  data/history/ig_daily_candles.csv, one_off_fill_done.json  -> data/history/GBPUSD/
What stays (shared by all pairs): data/history/ledger.json, ig_allowance.json,
daily_record.csv and BLOCKED.json (the history door's budget and IG's allowance).

Safety:
  * "go" refuses to run while the price service is running (systemctl is-active).
  * It refuses if anything unexpected is in the folders, or if a destination
    already exists. Nothing is ever deleted or overwritten: each item is
    renamed (same disk, one step each).
  * Before and after: every candle is counted (every timeframe, every row of
    every file, the archive too), every file's SHA-256 fingerprint is taken,
    and the store checks are run. "go" fails loudly if any of them differ.
  * The before/after record is written to data/moved_to_pair_folders.json.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from config.settings_loader import load_settings
from prices.calendar import Boundaries, MarketHours
from prices.checks import check_store
from prices.model import TIMEFRAMES
from prices.store import CandleStore

PAIR = "GBPUSD"           # the existing data is GBPUSD's: this one-off move is about that data only
SERVICE = "autobot-prices"
CANDLE_ITEMS = ("5m", "1h", "4h", "1d", "1w", "gaps.csv", "archive_22h_layout")
LEVEL_ITEMS = ("current.json",)
HISTORY_ITEMS = ("ig_daily_candles.csv", "one_off_fill_done.json")
HISTORY_SHARED = ("ledger.json", "ig_allowance.json", "daily_record.csv", "BLOCKED.json")
RECORD = "moved_to_pair_folders.json"


def roots(settings: Any) -> dict[str, Path]:
    return {"candles": Path(settings.candles.folder), "levels": Path(settings.levels.folder),
            "history": Path(settings.history.folder)}


def moves(settings: Any) -> list[tuple[Path, Path]]:
    r = roots(settings)
    out = []
    for key, items in (("candles", CANDLE_ITEMS), ("levels", LEVEL_ITEMS), ("history", HISTORY_ITEMS)):
        for name in items:
            src = r[key] / name
            if src.exists():
                out.append((src, r[key] / PAIR / name))
    return out


def unexpected(settings: Any) -> list[str]:
    r = roots(settings)
    allowed = {"candles": set(CANDLE_ITEMS), "levels": set(LEVEL_ITEMS),
               "history": set(HISTORY_ITEMS) | set(HISTORY_SHARED)}
    out = []
    for key, folder in r.items():
        if folder.is_dir():
            for p in folder.iterdir():
                if p.name not in allowed[key] and not (p.is_dir() and p.name == PAIR):
                    out.append(str(p))
    return out


def _rows(p: Path) -> int:
    data = gzip.decompress(p.read_bytes()) if p.name.endswith(".gz") else p.read_bytes()
    lines = [x for x in data.decode().splitlines() if x.strip()]
    return max(0, len(lines) - 1)        # minus the header line


def snapshot(candles_root: Path, levels_root: Path, history_root: Path, settings: Any) -> dict:
    """Counts, fingerprints and store checks for the GBPUSD data at these places."""
    files: dict[str, str] = {}
    for base, label in ((candles_root, "candles"), (levels_root, "levels"), (history_root, "history")):
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                files[f"{label}/{p.relative_to(base).as_posix()}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    counts: dict[str, int] = {}
    for tf in TIMEFRAMES:
        folder = candles_root / tf
        counts[tf] = sum(_rows(p) for p in folder.glob("*.csv*")) if folder.is_dir() else 0
    archive = candles_root / "archive_22h_layout"
    if archive.is_dir():
        for p in sorted(archive.rglob("*.csv*")):
            key = f"archive {p.parent.relative_to(archive).as_posix()}"
            counts[key] = counts.get(key, 0) + _rows(p)
    store = CandleStore(candles_root, settings.candles.compress_after_days, warn=lambda m: None)
    hours = MarketHours(settings.market_hours)
    chk = check_store(store, Boundaries(settings.candles, hours))
    return {"candle_rows": counts, "candles_read_by_store": dict(chk.candles),
            "store_problems": list(chk.problems),
            "gaps": [g.describe() for g in chk.gaps], "gaps_not_recorded": len(chk.new_gaps),
            "recorded_gaps": len(store.recorded_gaps()), "files": files}


def _strip(files: dict[str, str]) -> dict[str, str]:
    """Paths without the pair folder, so before and after can be compared."""
    out = {}
    for k, v in files.items():
        label, rest = k.split("/", 1)
        if rest.startswith(PAIR + "/"):
            rest = rest[len(PAIR) + 1:]
        out[f"{label}/{rest}"] = v
    return out


def service_state() -> str:
    try:
        r = subprocess.run(["systemctl", "is-active", SERVICE], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def show(snap: dict, say: Callable[[str], None]) -> None:
    say("  candles counted, row by row: " + ", ".join(f"{k} {v}" for k, v in snap["candle_rows"].items()))
    say(f"    total {sum(snap['candle_rows'].values())}")
    say("  candles read by the store: " + ", ".join(f"{k} {v}" for k, v in snap["candles_read_by_store"].items())
        + f" (total {sum(snap['candles_read_by_store'].values())})")
    say(f"  store checks: {len(snap['store_problems'])} problem(s); {len(snap['gaps'])} gap(s), "
        f"{snap['gaps_not_recorded']} not recorded; {snap['recorded_gaps']} gap record(s)")
    for p in snap["store_problems"]:
        say("    " + p)
    for g in snap["gaps"]:
        say("    " + g)
    say(f"  files fingerprinted: {len(snap['files'])}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args not in (["plan"], ["go"]):
        print(__doc__)
        return 2
    say = lambda t="": print(t, flush=True)  # noqa: E731
    settings = load_settings()          # the settings file only: this tool needs no switches and no secrets
    gbp = settings.for_pair(PAIR)
    r = roots(settings)
    todo = moves(settings)
    odd = unexpected(settings)
    say(f"Move of the existing {PAIR} data into per-pair folders ({'PLAN, nothing changed' if args == ['plan'] else 'GO'})")
    say(f"Price service {SERVICE}: {service_state()}")
    if not todo:
        say("Nothing to move: the data is already in the per-pair folders.")
        return 0
    for src, dst in todo:
        say(f"  {src}  ->  {dst}")
    say("Stays where it is (shared by every pair): " +
        ", ".join(str(r['history'] / n) for n in HISTORY_SHARED if (r['history'] / n).exists()))
    if odd:
        say("UNEXPECTED items (not moved; the move will not run until they are explained): " + ", ".join(odd))
    clash = [str(dst) for _, dst in todo if dst.exists()]
    if clash:
        say("ALREADY EXIST at the destination (the move will not run): " + ", ".join(clash))
    say("")
    say("BEFORE:")
    before = snapshot(r["candles"], r["levels"], r["history"], gbp)
    show(before, say)
    if args == ["plan"]:
        return 0

    state = service_state()
    if state != "inactive":
        say(f"STOPPED: the price service is '{state}', not 'inactive'. Stop it first (sudo systemctl stop {SERVICE}).")
        return 3
    if odd or clash:
        say("STOPPED: unexpected items or existing destinations (above). Nothing was moved.")
        return 3
    for src, dst in todo:
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dst)              # same disk: one step; never overwrites (destination checked above)
        say(f"  moved {src.name}")
    say("")
    say("AFTER:")
    after = snapshot(Path(gbp.candles.folder), Path(gbp.levels.folder), r["history"], gbp)
    show(after, say)
    same = {
        "candle rows": before["candle_rows"] == after["candle_rows"],
        "candles read by the store": before["candles_read_by_store"] == after["candles_read_by_store"],
        "store problems": before["store_problems"] == after["store_problems"],
        "gaps": before["gaps"] == after["gaps"] and before["recorded_gaps"] == after["recorded_gaps"],
        "every file's fingerprint": _strip(before["files"]) == _strip(after["files"]),
    }
    say("")
    say("BEFORE vs AFTER:")
    for k, ok in same.items():
        say(f"  {k}: {'SAME' if ok else 'DIFFERENT'}")
    record = {"moved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "moves": [[str(a), str(b)] for a, b in todo], "before": before, "after": after, "same": same}
    (Path(settings.candles.folder).parent / RECORD).write_text(json.dumps(record, indent=1) + "\n")
    say(f"Record written: {Path(settings.candles.folder).parent / RECORD}")
    if not all(same.values()):
        say("SOMETHING DIFFERS: stop and look before starting the service.")
        return 1
    say("Nothing was lost.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
