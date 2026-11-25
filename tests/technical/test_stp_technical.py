"""Technical tests for the STP technical forecast (planner/technical.py, GitHub issue #3). Made-up candles only, except
where marked (the real store, server only). No IG, no orders, no trading records."""
import ast
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from functools import lru_cache
from pathlib import Path

import pytest

from planner import technical as T
from planner.measure import snapshot
from prices.indicators import ema, rsi
from prices.model import Candle
from tests.functional.test_planner_scenarios import S, START, waypoints
from tests.planner_helpers import Over, market, section, with_folder

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
PULLBACK_END = ((10, -70), (20, -120), (27, -100), (27.4, -90), (28, -99), (29, -101))


@lru_cache(maxsize=None)
def pullback_market():
    return market(S, START, waypoints(list(PULLBACK_END)))


def end(store):
    return store.by_tf["5m"][-1].end


def c(o, h, l, cl, start=datetime(2026, 11, 20, 7, tzinfo=UTC)):
    o, h, l, cl = (D(str(x)) for x in (o, h, l, cl))
    return Candle("1h", start, start + timedelta(hours=1), o, h, l, cl, o, h, l, cl)


# ---- candle shapes ---------------------------------------------------------------------------------------------------

def test_candle_shapes_doji_rejections_and_bodies():
    assert T.shape(c(100, 110, 99, 101), "sell").kind == "bearish rejection"     # long upper wick, close low
    assert T.shape(c(100, 101, 90, 99), "sell").kind == "bullish rejection"
    assert T.shape(c(100, 105, 95.5, 100.5), "sell").kind == "doji"              # small body, wicks under half each
    assert T.shape(c(100, 101, 90, 91), "sell").kind == "bearish body"
    assert T.shape(c(91, 101, 90, 100), "sell").kind == "bullish body"
    assert T.shape(c(100, 100, 100, 100), "sell").kind == "doji"                 # no range at all


# ---- indicators: the bot's own code, finished candles only -----------------------------------------------------------

def test_the_chart_read_uses_the_bots_own_ema_and_rsi_on_finished_hourly_candles():
    st = pullback_market()
    t = end(st)
    snap = snapshot(S, st, t)
    r = T.read_h1(S, snap)
    cs = snap.h1.candles
    assert all(x.end <= t for x in cs)                                              # closure: finished candles only
    assert r.ema == ema(cs, "sell", S.stp_technical.h1_ema_period)[cs[-1].start]
    assert r.rsi == rsi(cs, "sell", S.stp_technical.rsi_periods)[cs[-1].start]
    assert r.close == cs[-1].sell_close and r.last[-1].start == cs[-1].start
    assert r.avg_range == sum((x.sell_high - x.sell_low for x in cs[-14:]), D(0)) / 14


def test_time_alignment_the_forecast_names_the_last_finished_hour_and_never_a_running_one():
    st = pullback_market()
    t = end(st) - timedelta(minutes=25)                                            # in the middle of an hour
    f = T.technical_at(S, st.until(t), t)
    h1 = datetime.fromisoformat(f["h1_candle_utc"].replace("Z", "+00:00"))
    assert h1 + timedelta(hours=1) <= t and t - (h1 + timedelta(hours=1)) < timedelta(hours=1)


def test_no_lookahead_the_full_store_and_a_store_cut_at_the_time_give_the_same_forecast():
    st = pullback_market()
    t = end(st) - timedelta(hours=6)
    assert T.technical_at(S, st, t) == T.technical_at(S, st.until(t), t)


def test_deterministic_output():
    st = pullback_market()
    t = end(st)
    a, b = T.technical_at(S, st, t), T.technical_at(S, st, t)
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


# ---- data gaps, weekends, warm-up -------------------------------------------------------------------------------------

def test_stale_data_over_a_gap_or_weekend_gives_no_forecast_with_the_reason():
    st = pullback_market()
    t = end(st) + timedelta(hours=5)                                               # nothing new for five hours
    f = T.technical_at(S, st, t)
    assert f["opportunity"] is None and f["no_opportunity"].startswith("the data is not fresh")


def test_too_little_history_gives_no_forecast_with_the_reason():
    st = market(S, START, [(0, 12300), (30, 12350), (60, 12320)])
    f = T.technical_at(S, st, end(st))
    assert f["opportunity"] is None and f["no_opportunity"]


# ---- volatility units (GBP/USD: 1 point = 1 pip) ----------------------------------------------------------------------

def test_stop_buffer_is_the_larger_of_the_break_rule_and_a_share_of_the_h1_average_range():
    f = T.technical_at(S, pullback_market(), end(pullback_market()))
    o, ch = f["opportunity"], f["chart"]
    buf = max(D(3), (D("0.3") * D(ch["h1_average_range_pips"])))
    assert abs(D(ch["stop_buffer_pips"]) - buf) <= D("0.1")
    assert D(o["stop"]["price"]) - D(o["entry_zone"]["high"]) == D(ch["stop_buffer_pips"]).quantize(D("0.1"))
    assert D(o["stop"]["pips_from_entry"]) == abs(D(o["stop"]["price"]) - D(o["reference_entry"]))
    assert D(o["intermediate_target"]["pips_from_entry"]) == abs(D(o["intermediate_target"]["price"]) - D(o["reference_entry"]))


# ---- zone selection and targets ---------------------------------------------------------------------------------------

def test_targets_lie_beyond_the_entry_zone_and_beyond_price_with_no_minimum_distance():
    f = T.technical_at(S, pullback_market(), end(pullback_market()))
    o = f["opportunity"]
    t1, low, p = D(o["intermediate_target"]["price"]), D(o["entry_zone"]["low"]), D(f["price"])
    assert o["trade"] == "SELL" and t1 < low and t1 < p
    assert D(o["intermediate_target"]["pips_from_entry"]) < 15                       # a short target is kept
    if o["extended_target"]:
        assert D(o["extended_target"]["price"]) < t1


def test_a_target_price_is_already_inside_is_not_used(monkeypatch):
    """The D-1 principle: a destination price has already reached is not a destination."""
    from planner.zones import Zone
    snap = snapshot(S, pullback_market(), end(pullback_market()))
    read = T.read_h1(S, snap)
    p = snap.price
    inside = Zone(p - 2, p + 1, [], ["structure"], "Moderate", False)
    below = Zone(p - 12, p - 9, [], ["structure"], "Moderate", False)
    ctx = T.Context(S, snap, read, {}, [inside, below], None, D(6), D(3), D(3), D(4))
    t1, _ = T.targets(ctx, "SELL", p + 3, p + 8)
    assert t1[0] == p - 9


# ---- lifecycle: separate files, off by default --------------------------------------------------------------------------

def test_writing_is_off_when_switched_off_and_writes_nothing(tmp_path):
    # The deployment (deploy/stp-technical-20261120) switches it on in settings.toml; switched off, it writes nothing.
    s = Over(with_folder(S, tmp_path), stp_technical=section(S.stp_technical, enabled=False))
    assert s.stp_technical.enabled is False
    assert T.write(s, pullback_market(), end(pullback_market())) is None
    assert not any(tmp_path.rglob("*"))


def test_when_switched_on_it_writes_only_its_own_files_once_per_hour(tmp_path):
    s = Over(with_folder(S, tmp_path), stp_technical=section(S.stp_technical, enabled=True))
    st = pullback_market()
    t = end(st)
    T.write(s, st, t)
    T.write(s, st, t)                                                              # same hour: no second history line
    folder = tmp_path / "GBPUSD"
    assert sorted(p.name for p in folder.iterdir()) == ["technical.json", "technical.jsonl"]
    assert len((folder / "technical.jsonl").read_text().splitlines()) == 1
    assert json.loads((folder / "technical.json").read_text())["observe_only"] == T.OBSERVE_ONLY
    assert not (folder / "current.json").exists() and not (folder / "recommendations.jsonl").exists()


def test_a_technical_failure_in_the_planner_run_never_stops_the_keeper(monkeypatch, tmp_path):
    import planner.__main__ as pm
    calls = []
    monkeypatch.setattr("planner.keeper.Keeper.run", lambda self, now: calls.append("keeper"))
    monkeypatch.setattr(T, "write", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(pm, "load_settings", lambda **kw: type("X", (), {"for_pair": lambda self, p: with_folder(S, tmp_path)})())
    monkeypatch.setattr("housekeeping.logs.setup_logging", lambda *a, **k: None)
    assert pm.main(["run"]) == 0 and calls == ["keeper"]


# ---- no broker side effects --------------------------------------------------------------------------------------------

FORBIDDEN = ("ig", "orders", "trading", "trade_manager", "strategies", "safety", "requests")


def test_the_technical_module_imports_no_broker_or_trading_code():
    for f in (ROOT / "planner/technical.py", ROOT / "research/stp_technical/replay.py", ROOT / "research/stp_technical/score.py"):
        tree = ast.parse(f.read_text())
        mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | \
               {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not [m for m in mods if m.split(".")[0] in FORBIDDEN], (f.name, mods)


def test_a_forecast_carries_no_order_fields_and_says_observe_only():
    f = T.technical_at(S, pullback_market(), end(pullback_market()))
    assert f["observe_only"] == "OBSERVE ONLY - DOES NOT CONTROL TRADING"
    assert not {"size", "stake", "deal_id", "order", "epic"} & (set(f) | set(f["opportunity"]))


# ---- approved rules preserved ----------------------------------------------------------------------------------------

def test_the_approved_planner_settings_are_unchanged():
    p = S.planner
    assert (p.historical_daily_swing_lookback_weeks, p.daily_swing_lookback_weeks, p.break_beyond_pips,
            p.zone_width_adr_share, p.min_entry_class) == (156, 48, D("3"), D("0.15"), "Moderate")
    assert tuple(S.indicators.ema_periods) == (7, 13, 21, 100, 200) and S.indicators.rsi_periods == 3


def test_the_existing_plan_is_identical_with_the_technical_module_present():
    from planner.assess import plan_at
    st = pullback_market()
    t = end(st)
    before = plan_at(S, st, t, calendar=[]).as_dict()
    T.technical_at(S, st, t)
    assert plan_at(S, st, t, calendar=[]).as_dict() == before


# ---- the real PIA First example time (server only, read only) -------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    from prices.store import CandleStore
    if not (S.candles.folder / "1h").is_dir():
        pytest.skip("the real candle store is only on the server")
    return CandleStore(S.candles.folder, S.candles.compress_after_days)


def test_real_20_november_0800_is_an_h1_ema20_pullback_sell_with_the_evidence_shown(real):
    f = T.technical_at(S, real, datetime(2026, 11, 20, 8, 0, 5, tzinfo=UTC))
    o = f["opportunity"]
    assert o["type"] == "PULLBACK" and o["trade"] == "SELL" and not o["countertrend"]
    ema20 = D(f["chart"]["h1_ema20"])
    assert D(o["entry_zone"]["low"]) <= ema20 <= D(o["entry_zone"]["high"])
    texts = " | ".join(e["text"] for e in o["evidence"])
    assert "4-hour direction (existing STP) is BEARISH" in texts and "bearish rejection" in texts
    assert 8 <= D(o["intermediate_target"]["pips_from_entry"]) <= 15                 # a 13-pip opportunity is kept
