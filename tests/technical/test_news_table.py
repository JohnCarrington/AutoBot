"""AutoBot's news table (config/news_table.toml, matched by news/table.py):
every row is valid, and the matching follows the owner's order: overrides
first, then big rules, then medium rules, otherwise small (logged once), with
the two same-day rules and the added "Interest Rate" row."""

import json
import logging
from pathlib import Path

import pytest

from news.table import BIG, MEDIUM, SMALL, TABLE_PATH, NewsTableError, UnmatchedLog, classify, load_table
from tests.technical.test_pairs import pretend

ROWS = load_table()


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path)


def c(st, currency, name, same_day=(), impact="high", rows=ROWS):
    return classify(rows, st, currency, name, impact, same_day)


# ---- every row is valid -----------------------------------------------------------------------

def test_the_table_is_161s_77_rows_plus_the_owners_five():
    by = {s: [r for r in ROWS if r.section == s] for s in ("override", "big", "middle")}
    assert (len(by["override"]), len(by["big"]), len(by["middle"])) == (12, 45, 25)
    # rule names: ours + 161's 4 override, 12 big and 15 medium rule names (161's README says 13 and 13;
    # the CSV, which is what was copied, has 12 and 15)
    names = lambda s: {r.rule for r in ROWS if r.section == s}  # noqa: E731
    assert (len(names("override")), len(names("big")), len(names("middle"))) == (9, 12, 15)
    assert by["override"][0].rule == "gbp_interest_rate" and by["override"][0].name_is == "Interest Rate"


@pytest.mark.parametrize("row", ROWS, ids=[f"{r.section}-{r.rule}-{'+'.join(r.all_of) or r.name_is}" for r in ROWS])
def test_every_row_is_valid(row):
    assert row.section in ("override", "big", "middle") and row.rule
    assert row.tier == (BIG if row.section == "big" else MEDIUM if row.section == "middle" else row.tier)
    assert row.tier in ((BIG, MEDIUM, SMALL) if row.section == "override" else (BIG, MEDIUM))
    assert (row.currency is not None) == (row.section == "override")
    assert bool(row.all_of) != bool(row.name_is)                       # exactly one way of matching
    assert all(k and k == k.lower() for k in row.all_of)
    assert all(g and all(k == k.lower() for k in g) for g in row.same_day)


@pytest.mark.parametrize("text,problem", [
    ('[[big]]\nrule = "x"\n', "needs exactly one of all_of or name_is"),
    ('[[big]]\nrule = "x"\nall_of = ["CPI"]\n', "must be lower case"),
    ('[[big]]\nrule = "x"\nall_of = []\n', "non-empty list"),
    ('[[override]]\nrule = "x"\ntier = "big"\nall_of = ["cpi"]\n', "needs its currency"),
    ('[[override]]\nrule = "x"\ncurrency = "GBP"\ntier = "huge"\nall_of = ["cpi"]\n', "tier must be big, medium or small"),
    ('[[big]]\nrule = "x"\nall_of = ["cpi"]\ncolour = "red"\n', "unknown field"),
    ('[[small]]\nrule = "x"\nall_of = ["cpi"]\n', "Unknown section"),
])
def test_a_bad_row_is_named_with_its_problem(tmp_path, text, problem):
    p = tmp_path / "t.toml"
    p.write_text(text)
    with pytest.raises(NewsTableError, match=problem):
        load_table(p)


# ---- the matching order --------------------------------------------------------------------------

def test_overrides_come_first_and_only_for_their_currency(st):
    # GBP CPI: the GBP override wins over the any-currency big rule us_cpi
    assert (c(st, "GBP", "Inflation Rate YoY").rule, c(st, "USD", "Inflation Rate YoY").rule) == (
        "uk_cpi_override", "us_cpi")
    # GBP GDP MoM: the override makes it MEDIUM; for USD no override applies
    assert (c(st, "GBP", "GDP MoM").tier, c(st, "GBP", "GDP MoM").rule) == (MEDIUM, "gbp_gdp_mom_override")
    assert c(st, "USD", "GDP Growth Rate QoQ Adv").rule == "usd_gdp_adv_override"
    assert c(st, "GBP", "GDP Growth Rate QoQ Adv").tier == SMALL                 # gdp + adv override is USD only,
    assert c(st, "GBP", "GDP Growth Rate QoQ Prel").rule == "uk_gdp"             # and 161's UK rule says "prel"


def test_big_rules_come_before_medium_rules(st):
    rows = load_table_text(st, '[[middle]]\nrule = "m"\nall_of = ["cpi"]\n[[big]]\nrule = "b"\nall_of = ["cpi"]\n')
    m = c(st, "USD", "CPI", rows=rows)
    assert (m.tier, m.rule) == (BIG, "b")                                       # big rows tried before middle rows
    assert c(st, "USD", "Core PCE Price Index MoM").rule == "core_pce"         # the first medium row that matches


def load_table_text(st, text):
    p = Path(st.news.folder).parent / "t.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return load_table(p)


def test_within_a_section_the_first_matching_row_decides(st):
    assert c(st, "USD", "Core Inflation Rate MoM").rule == "us_core_cpi"       # before us_cpi
    assert c(st, "USD", "FOMC Minutes").rule == "us_fomc"                      # "fomc" comes before the minutes rule


@pytest.mark.parametrize("currency,name,tier,rule", [
    ("GBP", "BoE Interest Rate Decision", BIG, "uk_boe_rate"),
    ("GBP", "Interest Rate", BIG, "gbp_interest_rate"),                         # the added row
    ("USD", "Non Farm Payrolls", BIG, "us_nfp"),
    ("USD", "Fed Interest Rate Decision", BIG, "us_fomc"),
    ("USD", "Fed Press Conference", BIG, "usd_fed_press_conf_override"),
    ("GBP", "MPC Meeting Minutes", BIG, "central_bank_minutes"),
    ("USD", "ISM Manufacturing PMI", MEDIUM, "ism_manufacturing_pmi"),
    ("USD", "Initial Jobless Claims", MEDIUM, "initial_jobless_claims"),
    ("GBP", "Retail Sales MoM", MEDIUM, "retail_sales"),
    ("USD", "Existing Home Sales", SMALL, "usd_existing_home_sales"),          # placed as small
    ("USD", "Building Permits Prel", SMALL, "usd_building_permits_prel"),
    ("USD", "Housing Starts", SMALL, "usd_housing_starts"),
    ("GBP", "Unemployment Rate", BIG, "gbp_unemployment_rate"),                 # big on any day
    ("USD", "Personal Income MoM", SMALL, "default_small"),
])
def test_real_names(st, currency, name, tier, rule):
    m = c(st, currency, name)
    assert (m.tier, m.rule) == (tier, rule)


def test_the_added_interest_rate_row_is_gbp_only_and_exact(st):
    assert c(st, "GBP", "interest rate").tier == BIG                            # case does not matter
    assert c(st, "USD", "Interest Rate").tier == SMALL                          # GBP only
    assert c(st, "GBP", "Interest Rate Expectations").tier == SMALL             # the exact name only


def test_us_unemployment_rate_is_big_only_on_payrolls_day_but_the_uk_one_always(st):
    assert c(st, "GBP", "Unemployment Rate").tier == BIG
    assert c(st, "USD", "Unemployment Rate").tier == SMALL
    m = c(st, "USD", "Unemployment Rate", same_day=["Non Farm Payrolls", "Average Hourly Earnings MoM"])
    assert (m.tier, m.rule) == (BIG, "us_unemployment_with_nfp")


def test_a_fed_chair_speech_is_big_only_on_a_rate_decision_day(st):
    assert c(st, "USD", "Fed Chair Warsh Speech").tier == SMALL
    assert c(st, "USD", "Fed Chair Warsh Speech", same_day=["Fed Interest Rate Decision"]).tier == BIG


def test_only_high_impact_releases_are_matched(st):
    assert c(st, "GBP", "BoE Interest Rate Decision", impact="medium").rule == "impact_not_matched"
    assert c(st, "USD", "Non Farm Payrolls", impact="low").tier == SMALL
    assert st.news.table_impacts == ("high",)


def test_a_release_in_no_row_is_logged_once(st, caplog):
    caplog.set_level(logging.INFO)
    u = UnmatchedLog(st)
    assert u.note("USD", "Personal Income MoM", "2026-11-09T15:00:00Z")
    assert not u.note("USD", "Personal Income MoM", "2026-12-09T15:00:00Z")     # once, even later
    assert not UnmatchedLog(st).note("USD", "Personal Income MoM", "2027-01-09T15:00:00Z")   # and after a restart
    assert caplog.text.count("Personal Income MoM") == 1
    assert json.loads(u.path.read_text())["USD|Personal Income MoM"]["first_seen_release_utc"] == "2026-11-09T15:00:00Z"


def test_the_windows_use_the_table_and_log_unmatched_releases(st):
    from datetime import datetime, timezone
    from news.calendar import big_news_windows
    cal = [{"time_utc": "2026-11-06T13:30:00Z", "country": "US", "event": "Non Farm Payrolls", "impact": "high",
            "estimate": 65, "prev": 60},
           {"time_utc": "2026-11-06T13:30:00Z", "country": "US", "event": "Unemployment Rate", "impact": "high",
            "estimate": 4.3, "prev": 4.3},
           {"time_utc": "2026-11-06T15:00:00Z", "country": "US", "event": "Personal Income MoM", "impact": "high"},
           {"time_utc": "2026-11-06T15:00:00Z", "country": "US", "event": "Existing Home Sales", "impact": "high"},
           {"time_utc": "2026-11-06T09:00:00Z", "country": "GB", "event": "MPC Meeting Minutes", "impact": "medium"}]
    ws = big_news_windows(st, "GBPUSD", datetime(2026, 11, 6, tzinfo=timezone.utc),
                          datetime(2026, 11, 7, tzinfo=timezone.utc), cal)
    assert [w.event for w in ws] == ["Non Farm Payrolls", "Unemployment Rate"]   # unemployment: payrolls day
    assert "USD|Personal Income MoM" in UnmatchedLog(st).seen()                 # in no row: logged
    assert "USD|Existing Home Sales" not in UnmatchedLog(st).seen()             # placed as small: not logged
    assert "GBP|MPC Meeting Minutes" not in UnmatchedLog(st).seen()             # medium impact: not matched at all
