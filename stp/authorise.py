"""The STP authorisation check (STP_AUTHORISES_ENTRIES; owner, 24 November 2026; docs/design/
STP_STRATEGY_INTEGRATION_20261124.md sections 9 and 10; OD-03, OD-24, OD-25, OD-29, OD-32, OD-33). Called once from
trading/engine.py _place for an idea of a strategy in stp_authorisation.strategies, after the engine has recorded
the try (so a refused idea is never tried again, queued or sent later: section 9.5). Read only: it never writes STP's
file. It adds no confirmation: the strategy has already confirmed; this only says whether that confirmation happened
at a live STP opportunity in its direction.

An idea is authorised only if ALL of these hold (any failure refuses, with every reason recorded):
  1. STP_OPPORTUNITIES and STP_BIDIRECTIONAL are on (OD-24, OD-29) and ONE_SIGNAL_ONE_TRADE is on (OD-32);
  2. fresh data: STP's file was written by a tracker run no more than [analyser] out_of_date_after_minutes (10) ago,
     that run marked itself current (its "current": fresh candles and re-checked at the latest hourly candle; design
     section 4, "fail closed ... is not current"), and the live price (or, with none, the latest stored 5-minute
     candle) is no older than that (D-21 b, FC-08);
  3. its rejection candle (context["rejection_candle"], the setup's pierce candle) interacts with the zone of a live
     opportunity (WAITING or Watch & Wait) in its direction, by the tracker's own rule (planner/zones.py interacts,
     rejection.near_level_within_pips; D-29 A). The entry itself may be outside the zone;
  4. catch-up over the tracker's lag (section 9.3, OD-25): the tracker's OWN rules applied, read only, to what it has
     not yet seen: every finished 5-minute candle after its last step, the forming candle's high and low (built from
     every live price, so a touch earlier in the candle that has reversed counts) and the live price, for the primary
     destination; every finished hourly candle after its last re-plan for the zone break (D-20); every finished
     4-hour candle after its last 4-hour check for the structure break;
  5. the entry price is not at or beyond the zone-break price (FC-07).
Binding (section 10): among the opportunities that pass, the OLDEST (earliest lineage), then FC-03 (strongest class,
then nearest to the rejection candle), so a newly published opportunity never displaces an existing binding.
Key (OD-32): "<lineage id>#t<n>", n the D-25 test that contains the rejection candle; the idea's existing signal key
(if any) is kept in front of it, joined by "|"; rule 11 refuses the idea if either part was already used.
Phase 2 WP1 (owner, 27 November 2026): the lineage is the structural place (planner/lineage.py), so n is counted on
the LINEAGE's record (state["lineages"]), which republication, reissue and supersession share. The key also carries
  * the lineage's ALIAS keys for test n: keys of the same structural test issued under another id before the lineage
    registry existed (PD-4, planner/migrate_lineage.py), so a test traded under an old key stays traded;
  * the key of every OTHER live lineage of the same direction whose zone the rejection candle also reached (zones that
    only share an edge stay separate lineages), at that lineage's own test number,
so a trade consumes every key that names the structural test it used, and rule 11 refuses any later idea naming one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from planner.keeper import BEFORE, OVERLAPPED, candle_timing
from planner.lineage import test_number
from planner.measure import cl, ppp, side_of
from planner.zones import CLASS_RANK, interacts, wholly_clear
from prices.model import parse_iso, plain, uk_short
from stp.gate import bypassed, gated  # noqa: F401  (re-exported)

AUTHORISING = ("WAITING", "ACTIVE")


@dataclass
class Verdict:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    opportunity: dict | None = None
    stp_key: str | None = None
    signal: str | None = None
    bypass: frozenset = frozenset()
    steps: list[str] = field(default_factory=list)
    lineage: str | None = None
    test: int | None = None
    keys: list[str] = field(default_factory=list)


def _d(x: Any) -> Decimal:
    return Decimal(str(x))


def _five(store: Any, start: datetime) -> Any:
    got = [c for c in store.read_range("5m", start, start + timedelta(minutes=5)) if c.start == start]
    return got[0] if got else None


def which_test(settings: Any, store: Any, low: Decimal, high: Decimal, since: datetime | None,
               rejection_start: datetime, tests: dict | None = None) -> int:
    """The D-25 test that contains the rejection candle (planner/lineage.py test_number, the tracker's own rule):
    the tests recorded before the rejection candle's hour, the hours after the record counted against the current
    zone, plus one if the count is armed then; 0 before the lineage's seeded history. Without a record (a file written
    before it existed), every hour since `since` is counted against the current zone."""
    return test_number(settings, store, low, high, tests, rejection_start, since)


def unreconciled(state: dict, o: dict) -> list[str]:
    """PD-5 B (owner, 27 November 2026): why this opportunity's history cannot be relied on yet: a recorded data gap
    in its life not yet re-checked on recovered candles, or an uncertain hour in its lineage's D-25 count."""
    out = [f"STP data gap {g['from_utc']} to {g['to_utc']} not reconciled" + (" (left for review)"
                                                                            if g.get("status") == "review" else "")
           for g in o.get("data_gaps") or [] if g.get("status") != "reconciled"]
    t = (_lineage(state, o).get("tests") or {})
    if t.get("uncertain"):
        out.append(f"STP data gap: the D-25 count of its lineage has uncertain hour(s) {', '.join(t['uncertain'])}")
    return out


def _lineage(state: dict, o: dict) -> dict:
    return (state.get("lineages") or {}).get(o.get("lineage") or o["id"]) or {}


def _keys(settings: Any, store: Any, state: dict, o: dict, rc_start: datetime) -> tuple[str, int, list[str]]:
    """The opportunity's lineage key for the rejection candle, its test number, and its alias keys for that test."""
    lin = _lineage(state, o)
    lid = o.get("lineage") or o["id"]
    since = o.get("lineage_created_utc") or o.get("created_utc")
    n = which_test(settings, store, _d(o["entry_zone"]["low"]), _d(o["entry_zone"]["high"]),
                   parse_iso(since) if since else None, rc_start, tests=lin.get("tests") or o.get("tests"))
    return f"{lid}#t{n}", n, list((lin.get("aliases") or {}).get(str(n), []))


def _catch_up(settings: Any, store: Any, state: dict, o: dict, now: datetime, partial: Any, tick: Any,
              previous: Any = None, partial_covered: bool = False) -> list[str]:
    """The tracker's own destination, zone-break and structure-break rules on what it has not yet seen."""
    side = side_of(settings)
    out: list[str] = []
    sell = o["trade"] == "SELL"
    dz = o["destinations"]["primary"]["zone"]
    dlow, dhigh = _d(dz["low"]), _d(dz["high"])
    applies = (o.get("invalidation") or {}).get("destination_first_applies", True) or o.get("ever_active")
    since = parse_iso(state["m5_checked_until"]) if state.get("m5_checked_until") else None
    seen: list = []
    if since is not None:
        seen = [c for c in store.read_range("5m", since, now) if c.start >= since and c.end <= now]
    if partial is not None and (since is None or partial.start >= since) and partial.start not in {c.start for c in seen}:
        seen.append(partial)
    # review R3: every finished 5-minute interval after the tracker's last step, the most recent included, must be
    # either stored or seen whole by the engine from the live prices (the candle IG has not yet published: its own
    # timing); one neither stored nor seen whole is a gap the authorisation cannot check (PD-5)
    unseen: list = []
    if since is not None:
        from planner.gaps import missing_fives
        from prices.calendar import floor_5m
        engine = [x for x, whole in ((previous, previous is not None), (partial, partial_covered)) if x is not None and whole]
        for a, b in missing_fives(settings, store, since, floor_5m(now)):
            s_ = a
            while s_ < b:
                got = next((x for x in engine if x.start == s_), None)
                if got is None:
                    unseen.append(s_)
                elif got.start not in {c.start for c in seen}:
                    seen.append(got)
                s_ += timedelta(minutes=5)
    if tick is not None:
        seen.append(SimpleNamespace(start=tick.time, end=tick.time + timedelta(microseconds=1), tick=True,
                                    **{f"{k}_{x}": getattr(tick, k) for k in ("buy", "sell")
                                       for x in ("open", "high", "low", "close")}))
    if applies:
        for c in seen:
            if candle_timing(c, o.get("created_utc")) in (BEFORE, OVERLAPPED):
                continue                                # the tracker's own rule: only evidence after creation
            if interacts(settings, c, dlow, dhigh, from_below=not sell):
                when = "the live price" if getattr(c, "tick", False) else (
                    "the forming 5-minute candle" if c is partial else f"the {uk_short(c.start)} 5-minute candle")
                out.append(f"the primary destination {o['destinations']['primary']['price']} was reached by {when}, "
                           f"after the tracker's last step: the opportunity has ended")
                break
    if unseen:                                         # PD-5: a candle the tracker has not seen and nobody holds
        out.append(f"no 5-minute candle stored or seen whole for {', '.join(uk_short(x) for x in unseen)}, after "
                   f"the tracker's last step: the opportunity's state is unknown (PD-5)")
    inv = o.get("invalidation") or {}
    zb = inv.get("zone_break_close")
    h1_since = parse_iso(state["validated_h1_end"]) if state.get("validated_h1_end") else None
    if zb is not None and h1_since is not None:
        for c in store.read_range("1h", h1_since, now):
            if c.start >= h1_since and c.end <= now and ((cl(c, side) >= _d(zb)) if sell else (cl(c, side) <= _d(zb))):
                out.append(f"the {uk_short(c.start)} hourly candle closed at {plain(cl(c, side))}, at or "
                           f"{'above' if sell else 'below'} the zone break {zb}, after the tracker's last re-plan")
                break
    sb = inv.get("structure_break_close")
    h4_since = parse_iso(state["h4_checked_until"]) if state.get("h4_checked_until") else None
    if sb is not None and h4_since is not None:
        for c in store.read_range("4h", h4_since, now):
            if c.start >= h4_since and c.end <= now and ((cl(c, side) >= _d(sb)) if sell else (cl(c, side) <= _d(sb))):
                out.append(f"the {uk_short(c.start)} 4-hour candle closed at {plain(cl(c, side))}, at or "
                           f"{'above' if sell else 'below'} the structure break {sb}, after the tracker's last check")
                break
    return out


def authorise(settings: Any, store: Any, idea: Any, now: datetime, source: Any, partial: Any = None,
              tick: Any = None, previous: Any = None, partial_covered: bool = False) -> Verdict:
    sw = settings.switches
    side = side_of(settings)
    sell = idea.direction == "sell"
    limit = timedelta(minutes=int(settings.analyser.out_of_date_after_minutes))
    refuse = lambda *why: Verdict(False, list(why))     # noqa: E731
    if not (getattr(sw, "stp_opportunities", False) and getattr(sw, "stp_bidirectional", False)):
        return refuse("STP authorisation needs STP_OPPORTUNITIES and STP_BIDIRECTIONAL on (OD-24, OD-29)")
    if not getattr(sw, "one_signal_one_trade", False):
        return refuse("STP authorisation needs ONE_SIGNAL_ONE_TRADE on: duplicates could not be refused (OD-32)")
    state = source.state_at(now) if source is not None else None
    if not state or not isinstance(state.get("opportunities"), list) or not state.get("written_utc"):
        return refuse("STP not current: its opportunities file is missing or unreadable")
    age = now - parse_iso(state["written_utc"])
    if age > limit:
        return refuse(f"STP not current: its tracker last ran {int(age.total_seconds() // 60)} minutes ago "
                      f"(more than {limit.seconds // 60})")
    if state.get("current") is not True:          # the tracker's own verdict on its last run (review, 25 Nov 2026):
        why = "; ".join(state.get("not_current_reasons") or []) or (    # stale candles, or no re-plan at the latest
            "its data is not fresh" if state.get("data_fresh") is False else "it is not marked current")  # hourly
        return refuse(f"STP not current: the tracker's last run says {why}")
    if tick is not None:
        if now - tick.time > limit:
            return refuse(f"stale price: the live price is from {tick.time:%H:%M:%S} UTC")
    else:
        from analyser.indicators import last_candles
        last = last_candles(store, "5m", now, 1)
        if not last or now - last[-1].end > limit:
            return refuse("stale price: no 5-minute candle within the freshness limit")
    rc_text = (getattr(idea, "context", None) or {}).get("rejection_candle")
    if not rc_text:
        return refuse("no rejection candle in the idea's context: cannot check it against the STP zones")
    rc_start = parse_iso(rc_text)
    rc = _five(store, rc_start)
    if rc is None and partial is not None and partial.start == rc_start:
        rc = partial
    if rc is None:
        return refuse(f"the rejection candle {rc_text} is not in the candle store")
    want = "SELL" if sell else "BUY"
    live = [o for o in state["opportunities"] if o.get("status") in AUTHORISING]
    near = [o for o in live if o["trade"] == want and
            interacts(settings, rc, _d(o["entry_zone"]["low"]), _d(o["entry_zone"]["high"]), from_below=sell)]
    if not near:
        shown = "; ".join(f"{o['trade']} {o['id']} {o['entry_zone']['low']}-{o['entry_zone']['high']}" for o in live) or "none"
        return refuse(f"no live STP {want} opportunity whose zone the rejection candle ({uk_short(rc.start)}) reached "
                      f"(live: {shown})")
    edge = (lambda o: _d(o["entry_zone"]["low"])) if sell else (lambda o: _d(o["entry_zone"]["high"]))
    ext = getattr(rc, f"{side}_high") if sell else getattr(rc, f"{side}_low")
    near.sort(key=lambda o: (o.get("lineage_created_utc") or o.get("created_utc") or "",
                             -CLASS_RANK.get(o["entry_zone"].get("class"), 0), abs(edge(o) - ext)))
    reasons: list[str] = []
    for o in near:
        why = unreconciled(state, o) + _catch_up(settings, store, state, o, now, partial, tick, previous,
                                                 partial_covered)
        zb = (o.get("invalidation") or {}).get("zone_break_close")
        price = _d(idea.entry_price)
        if zb is not None and ((price >= _d(zb)) if sell else (price <= _d(zb))):
            why.append(f"the entry {plain(price)} is at or {'above' if sell else 'below'} the zone break {zb} (FC-07)")
        if why:
            reasons += [f"{o['id']}: {w}" for w in why]
            continue
        lineage = o.get("lineage") or o["id"]
        key, n, aliases = _keys(settings, store, state, o, rc_start)
        parts = [key] + aliases
        for o2 in near:                                 # every other lineage this rejection candle reached
            if (o2.get("lineage") or o2["id"]) != lineage:
                k2, _, a2 = _keys(settings, store, state, o2, rc_start)
                parts += [k2] + a2
        parts = list(dict.fromkeys(parts))
        existing = (getattr(idea, "context", None) or {}).get("signal")
        signal = "|".join(([existing] if existing else []) + parts)
        steps = [f"STP authorised: the rejection candle {uk_short(rc.start)} reached the live {want} opportunity "
                 f"{o['id']} ({o.get('label') or o['status']}, zone {o['entry_zone']['low']}-{o['entry_zone']['high']}); "
                 f"test {n}; duplicate key {signal}; filters not applied for it: "
                 f"{', '.join(settings.stp_authorisation.bypass_filters)}"]
        return Verdict(True, [], o, key, signal, frozenset(settings.stp_authorisation.bypass_filters), steps,
                       lineage=lineage, test=n, keys=parts)
    return Verdict(False, reasons)
