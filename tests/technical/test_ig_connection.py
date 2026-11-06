"""Technical tests for the IG connection (ig/), using a pretend IG.
None of these tests can reach the real IG: tests/conftest.py blocks the network."""

import io
import logging
import re
import threading
from pathlib import Path

import pytest
import requests

from config.settings_loader import load_settings
from ig import check
from ig.client import IGClient
from ig.errors import LOGIN_FAILURE_EXIT_CODE, IGLoginFailure, IGRequestError, stop_bot
from ig.secrets import IGCredentials, last4, load_credentials
from tests.technical.fake_ig import (
    CREDS, OTHER_ACCOUNT, SECRETS, STREAMING, FakeIG, NoReply, Reply,
    accounts_ok, error, login_ok, logout_ok, switch_ok,
)

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = load_settings()

SLOWED = [
    "error.public-api.exceeded-api-key-allowance",
    "error.public-api.exceeded-account-allowance",
    "error.public-api.exceeded-account-trading-allowance",
]
STOP_AT_ONCE = [
    "error.security.client-suspended",
    "error.security.account-suspended",
    "error.security.account-locked",
    "error.security.api-key-invalid",
    "error.security.api-key-disabled",
    "error.security.api-key-revoked",
    "error.security.invalid-details",
]


def make(*replies, retries=True):
    fake = FakeIG(*replies)
    waits = []
    client = IGClient(SETTINGS.ig, CREDS, http=fake, sleep=waits.append, retries=retries)
    return client, fake, waits


def connected(*more_replies):
    """A client that has logged in and switched account, then more replies."""
    client, fake, waits = make(login_ok(), accounts_ok(), switch_ok(), *more_replies)
    client.connect()
    return client, fake, waits


# =============================================================================
# 1. The IG part and its settings
# =============================================================================

def test_uses_the_demo_address_from_the_settings_file():
    assert SETTINGS.ig.demo_base_url == "https://demo-api.ig.com/gateway/deal"
    client, fake, _ = make(login_ok())
    client.login()
    assert fake.sent[0].url == "https://demo-api.ig.com/gateway/deal/session"


def test_every_call_has_a_timeout_from_the_settings_file():
    client, fake, _ = connected()
    assert {s.timeout for s in fake.sent} == {SETTINGS.ig.request_timeout_seconds}


def test_uses_requests_not_trading_ig():
    for f in (ROOT / "ig").glob("*.py"):
        assert "trading_ig" not in f.read_text(), f
    assert "import requests" in (ROOT / "ig" / "client.py").read_text()


def test_requests_version_is_pinned():
    lines = (ROOT / "requirements.txt").read_text().split()
    assert f"requests=={requests.__version__}" in lines


def test_ig_is_the_only_part_that_talks_to_ig():
    """No other part of the bot can make web requests or holds IG's address.
    (config/ may name the address: it checks the settings file's value.)"""
    for f in ROOT.rglob("*.py"):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in ("ig", "tests", ".venv"):
            continue
        text = f.read_text()
        for http_library in ("import requests", "from requests", "urllib", "http.client", "socket",
                             "import lightstreamer", "from lightstreamer"):
            assert http_library not in text, (rel, http_library)
        if rel.parts[0] != "config":
            assert "ig.com" not in text, rel


# =============================================================================
# 2. Logging in
# =============================================================================

def test_login_uses_version_2_and_sends_the_login_details():
    client, fake, _ = make(login_ok())
    client.login()
    s = fake.sent[0]
    assert (s.method, s.path) == ("POST", "/session")
    assert s.headers["Version"] == "2"
    assert s.headers["X-IG-API-KEY"] == CREDS.api_key
    assert s.json == {"identifier": CREDS.username, "password": CREDS.password}
    assert "CST" not in s.headers and "X-SECURITY-TOKEN" not in s.headers


def test_login_keeps_both_tokens_and_the_streaming_address():
    client, fake, _ = make(login_ok(), accounts_ok())
    client.login()
    assert client.logged_in
    assert client.streaming_endpoint == STREAMING
    client.list_accounts()
    assert fake.sent[1].headers["CST"] == "CST-token-1"
    assert fake.sent[1].headers["X-SECURITY-TOKEN"] == "XST-token-1"


@pytest.mark.parametrize("endpoint", [None, "", "   "], ids=["missing", "empty", "blank"])
def test_missing_streaming_address_stops(endpoint):
    client, fake, _ = make(login_ok(endpoint=endpoint))
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert e.value.error == "missing-streaming-address"
    assert not client.logged_in
    assert fake.calls() == [("POST", "/session")]  # no retry


@pytest.mark.parametrize("drop", ["CST", "X-SECURITY-TOKEN"])
def test_missing_session_token_stops(drop):
    reply = login_ok()
    del reply.headers[drop]
    client, fake, _ = make(reply)
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert e.value.error == "missing-session-tokens"
    assert len(fake.sent) == 1


def test_only_one_login_at_a_time_second_login_refused():
    client, fake, _ = make(login_ok())
    client.login()
    with pytest.raises(RuntimeError, match="Only one login at a time"):
        client.login()
    assert fake.calls() == [("POST", "/session")]


def test_login_is_never_repeated_after_success():
    client, fake, _ = connected()
    assert fake.calls().count(("POST", "/session")) == 1


def test_two_threads_hitting_an_expired_session_cause_only_one_relogin():
    """Both threads see an expired session; only one may log in again. The
    other must reuse the new session."""
    client, _, _ = connected()
    gate = threading.Barrier(2)
    logins = []

    class SharedFake:
        def __init__(self):
            self.lock = threading.Lock()

        def request(self, method, url, headers=None, json=None, timeout=None):
            path = url[len(FakeIG.BASE):]
            if (method, path) == ("POST", "/session"):
                logins.append(1)
                return login_ok(n=2)
            if (method, path) == ("PUT", "/session"):
                return switch_ok()
            if headers.get("CST") == "CST-token-1":
                gate.wait(timeout=5)  # both threads hold the old session
                return error(401, "error.security.client-token-invalid")
            return Reply(200, {"ok": True})

    client._http = SharedFake()
    results = []

    def work():
        results.append(client.request("GET", "/x", "1", what="test").status_code)

    threads = [threading.Thread(target=work) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert results == [200, 200]
    assert len(logins) == 1


@pytest.mark.parametrize("status", [500, 503, 400, 404])
def test_other_login_failure_stops_without_retry(status):
    client, fake, waits = make(error(status, "error.something"))
    with pytest.raises(IGLoginFailure):
        client.login()
    assert len(fake.sent) == 1 and waits == []


def test_no_reply_to_login_stops_without_retry():
    client, fake, waits = make(NoReply())
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert e.value.error == "no-reply"
    assert len(fake.sent) == 1 and waits == []


# =============================================================================
# 3. Choosing the account
# =============================================================================

def test_ig_account_id_must_be_set_and_no_ig_call_is_made(tmp_path):
    env = tmp_path / ".env"
    env.write_text("IG_USERNAME=u\nIG_PASSWORD=p\nIG_API_KEY=k\nIG_ACCOUNT_ID=\n")
    with pytest.raises(IGLoginFailure) as e:
        load_credentials(env)
    assert e.value.error == "missing-secret"
    assert "IG_ACCOUNT_ID" in str(e.value)
    assert "No IG call was made" in str(e.value)


def test_account_not_in_igs_list_stops_and_does_not_switch():
    client, fake, _ = make(login_ok(), accounts_ok(OTHER_ACCOUNT, "THIRD9876"))
    client.login()
    with pytest.raises(IGLoginFailure) as e:
        client.choose_account(client.list_accounts())
    assert e.value.error == "account-not-found"
    assert ("PUT", "/session") not in fake.calls()
    msg = str(e.value)
    assert last4(CREDS.account_id) in msg
    assert CREDS.account_id not in msg and OTHER_ACCOUNT not in msg


def test_switch_does_not_change_the_default_account():
    client, fake, _ = connected()
    put = [s for s in fake.sent if (s.method, s.path) == ("PUT", "/session")]
    assert len(put) == 1
    assert put[0].json == {"accountId": CREDS.account_id, "defaultAccount": False}
    assert put[0].headers["Version"] == "1"


def test_switch_keeps_the_new_token_ig_sends():
    client, fake, _ = connected(Reply(200, {}))
    client.request("GET", "/x", "1", what="test")
    assert fake.sent[-1].headers["X-SECURITY-TOKEN"] == "XST-switched"


def test_412_means_already_active_and_is_fine():
    client, fake, _ = make(login_ok(), accounts_ok(), error(412))
    client.connect()
    assert client.account_active


@pytest.mark.parametrize("code", ["error.switch.accountId-must-be-different",
                                  "error.switch.accountid-must-be-different"])
def test_account_must_be_different_means_already_active_and_is_fine(code):
    client, fake, _ = make(login_ok(), accounts_ok(), error(400, code))
    client.connect()
    assert client.account_active


@pytest.mark.parametrize("reply", [error(400, "error.switch.invalid-account"), error(404), error(500),
                                   NoReply()], ids=["400", "404", "500", "no-reply"])
def test_any_other_switch_failure_stops(reply):
    client, fake, waits = make(login_ok(), accounts_ok(), reply)
    with pytest.raises(IGLoginFailure):
        client.connect()
    assert not client.account_active
    assert fake.calls().count(("PUT", "/session")) == 1 and waits == []


def test_bad_accounts_reply_stops():
    client, _, _ = make(login_ok(), Reply(200, {"nothing": []}))
    client.login()
    with pytest.raises(IGLoginFailure, match="bad-accounts-reply"):
        client.list_accounts()


def test_later_calls_refused_until_account_chosen():
    client, fake, _ = make(login_ok())
    client.login()
    with pytest.raises(RuntimeError, match="connect"):
        client.request("GET", "/x", "1", what="test")


# =============================================================================
# 4. Errors
# =============================================================================

@pytest.mark.parametrize("code", SLOWED)
def test_slowed_down_at_login_waits_60_90_120_180_then_succeeds(code):
    client, fake, waits = make(*[error(403, code)] * 4, login_ok())
    client.login()
    assert waits == [60, 90, 120, 180]
    assert fake.calls() == [("POST", "/session")] * 5


@pytest.mark.parametrize("code", SLOWED)
def test_still_slowed_down_after_the_last_wait_stops(code):
    client, fake, waits = make(*[error(403, code)] * 5)
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert waits == [60, 90, 120, 180]
    assert len(fake.sent) == 5 and fake.all_used()
    assert e.value.error == code.rsplit(".", 1)[-1]


def test_slow_down_waits_come_from_the_settings_file():
    assert SETTINGS.ig.slowed_down_waits_seconds == (60, 90, 120, 180)


def test_slowed_down_once_then_success_waits_only_60():
    client, fake, waits = make(error(403, SLOWED[0]), login_ok())
    client.login()
    assert waits == [60]


@pytest.mark.parametrize("code", SLOWED)
def test_slowed_down_on_a_later_call_uses_the_same_waits_and_never_logs_in_again(code):
    client, fake, waits = connected(*[error(403, code)] * 5)
    with pytest.raises(IGLoginFailure):
        client.request("GET", "/x", "1", what="test")
    assert waits == [60, 90, 120, 180]
    assert fake.calls().count(("POST", "/session")) == 1


def test_client_token_invalid_at_login_one_controlled_relogin_then_success():
    client, fake, waits = make(error(401, "error.security.client-token-invalid"), login_ok())
    client.login()
    assert client.logged_in
    assert fake.calls() == [("POST", "/session")] * 2 and waits == []


def test_client_token_invalid_twice_at_login_stops():
    client, fake, _ = make(*[error(401, "error.security.client-token-invalid")] * 2)
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert e.value.error == "client-token-invalid"
    assert len(fake.sent) == 2 and fake.all_used()


def test_client_token_invalid_on_a_later_call_relogs_in_once_and_switches_back():
    client, fake, _ = connected(
        error(401, "error.security.client-token-invalid"),
        login_ok(n=2), switch_ok(), Reply(200, {"ok": True}),
    )
    r = client.request("GET", "/x", "1", what="test")
    assert r.status_code == 200
    assert fake.calls()[3:] == [("GET", "/x"), ("POST", "/session"), ("PUT", "/session"), ("GET", "/x")]
    assert fake.sent[-1].headers["CST"] == "CST-token-2"
    assert fake.sent[5].json == {"accountId": CREDS.account_id, "defaultAccount": False}


def test_relogin_that_fails_stops():
    client, fake, _ = connected(
        error(401, "error.security.client-token-invalid"),
        error(401, "error.security.invalid-details"),
    )
    with pytest.raises(IGLoginFailure) as e:
        client.request("GET", "/x", "1", what="test")
    assert e.value.error == "invalid-details"
    assert fake.all_used()


def test_still_invalid_after_the_relogin_stops():
    client, fake, _ = connected(
        error(401, "error.security.client-token-invalid"),
        login_ok(n=2), switch_ok(),
        error(401, "error.security.client-token-invalid"),
    )
    with pytest.raises(IGLoginFailure) as e:
        client.request("GET", "/x", "1", what="test")
    assert e.value.error == "client-token-invalid"
    assert fake.calls().count(("POST", "/session")) == 2 and fake.all_used()


def test_switch_after_relogin_that_is_refused_stops():
    client, fake, _ = connected(
        error(401, "error.security.client-token-invalid"),
        login_ok(n=2), error(401, "error.security.client-token-invalid"),
    )
    with pytest.raises(IGLoginFailure):
        client.request("GET", "/x", "1", what="test")
    assert fake.calls().count(("POST", "/session")) == 2 and fake.all_used()


@pytest.mark.parametrize("code", ["error.security.client-token-missing",
                                  "error.security.account-token-invalid",
                                  "error.security.account-token-missing"])
def test_session_expired_401_on_a_later_call_is_treated_as_client_token_invalid(code):
    client, fake, _ = connected(error(401, code), login_ok(n=2), switch_ok(), Reply(200, {}))
    client.request("GET", "/x", "1", what="test")
    assert fake.calls().count(("POST", "/session")) == 2 and fake.all_used()


@pytest.mark.parametrize("code", STOP_AT_ONCE)
@pytest.mark.parametrize("status", [401, 403])
def test_stop_at_once_codes_at_login(code, status):
    client, fake, waits = make(error(status, code))
    with pytest.raises(IGLoginFailure) as e:
        client.login()
    assert e.value.error == code.rsplit(".", 1)[-1]
    assert len(fake.sent) == 1 and waits == []


@pytest.mark.parametrize("code", STOP_AT_ONCE)
def test_stop_at_once_codes_on_a_later_call(code):
    client, fake, waits = connected(error(403, code))
    with pytest.raises(IGLoginFailure):
        client.request("GET", "/x", "1", what="test")
    assert fake.calls().count(("POST", "/session")) == 1 and waits == []


@pytest.mark.parametrize("reply", [error(401), error(403), error(401, "error.security.something-new"),
                                   error(403, "error.public-api.forbidden"),
                                   Reply(401, raw_text="<html>not json</html>")],
                         ids=["401-no-code", "403-no-code", "401-unknown", "403-unknown", "401-not-json"])
def test_any_other_401_or_403_stops_at_once(reply):
    client, fake, waits = make(reply)
    with pytest.raises(IGLoginFailure):
        client.login()
    assert len(fake.sent) == 1 and waits == []


@pytest.mark.parametrize("reply", [error(401), error(401, "error.security.something-new"), error(403)],
                         ids=["401-no-code", "401-unknown", "403"])
def test_any_other_401_or_403_on_a_later_call_stops_at_once(reply):
    client, fake, waits = connected(reply)
    with pytest.raises(IGLoginFailure):
        client.request("GET", "/x", "1", what="test")
    assert fake.calls().count(("POST", "/session")) == 1 and waits == []


def test_other_errors_on_later_calls_go_back_to_the_caller():
    client, fake, _ = connected(error(500, "error.service.unavailable"), NoReply())
    with pytest.raises(IGRequestError) as e:
        client.request("GET", "/x", "1", what="test")
    assert e.value.status == 500
    with pytest.raises(IGRequestError):
        client.request("GET", "/x", "1", what="test")
    assert fake.calls().count(("POST", "/session")) == 1


def test_login_failure_exit_code_is_78():
    assert LOGIN_FAILURE_EXIT_CODE == 78


def test_stop_writes_a_clear_message_and_exits_78(capsys):
    with pytest.raises(SystemExit) as e:
        stop_bot(IGLoginFailure("account-suspended", "IG refused the login (HTTP 403)."))
    assert e.value.code == 78
    err = capsys.readouterr().err
    assert "AutoBot STOPPED" in err
    assert "[account-suspended]" in err
    assert "Exit code 78" in err


def test_exit_code_is_documented():
    doc = (ROOT / "docs" / "IG_CONNECTION.md").read_text()
    assert f"exit code {LOGIN_FAILURE_EXIT_CODE}" in doc.lower()
    assert f"RestartPreventExitStatus={LOGIN_FAILURE_EXIT_CODE}" in doc


def test_every_error_code_in_the_rules_is_documented():
    doc = (ROOT / "docs" / "IG_CONNECTION.md").read_text()
    for code in SLOWED + STOP_AT_ONCE + ["client-token-invalid", "accountId-must-be-different"]:
        assert code.rsplit(".", 1)[-1] in doc, code


# =============================================================================
# Secrets
# =============================================================================

def test_secrets_never_appear_in_logs_messages_or_reprs(caplog, capsys):
    caplog.set_level(logging.DEBUG)
    texts = [repr(CREDS), str(CREDS)]
    scenarios = [
        lambda: make(login_ok(), accounts_ok(), switch_ok())[0].connect(),
        lambda: make(login_ok(), accounts_ok(OTHER_ACCOUNT))[0].connect(),
        lambda: make(error(403, STOP_AT_ONCE[1]))[0].login(),
        lambda: make(*[error(403, SLOWED[0])] * 5)[0].login(),
        lambda: make(login_ok(), accounts_ok(), error(400, "error.switch.x"))[0].connect(),
        lambda: make(login_ok(endpoint=None))[0].login(),
    ]
    for run in scenarios:
        try:
            run()
        except IGLoginFailure as e:
            texts.append(str(e))
    client, _, _ = connected()
    texts += [repr(client.calls), repr(client.list_accounts.__func__), repr(vars(client).get("_creds"))]
    texts.append(caplog.text)
    out = capsys.readouterr()
    texts += [out.out, out.err]
    joined = "\n".join(texts)
    for secret in SECRETS:
        assert secret not in joined, f"secret leaked: {secret[:3]}..."
    assert last4(CREDS.account_id) in joined


def test_last4_shows_only_the_last_4_characters():
    assert last4("ABCDEFGH") == "****EFGH"
    assert last4("") == "(none)"


def test_env_file_parsing(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "# comment\n\nIG_USERNAME=user1\nIG_PASSWORD='pa#ss word'\n"
        'export IG_API_KEY="key-1"\nIG_ACCOUNT_ID = ACC123\nTELEGRAM_BOT_TOKEN=x\n'
    )
    c = load_credentials(env)
    assert (c.username, c.password, c.api_key, c.account_id) == ("user1", "pa#ss word", "key-1", "ACC123")


def test_missing_env_file_stops(tmp_path):
    with pytest.raises(IGLoginFailure) as e:
        load_credentials(tmp_path / "nope")
    assert e.value.error == "missing-env-file"


@pytest.mark.parametrize("key", ["IG_USERNAME", "IG_PASSWORD", "IG_API_KEY", "IG_ACCOUNT_ID"])
def test_each_missing_secret_stops_and_is_named_without_values(tmp_path, key):
    values = {"IG_USERNAME": "u-SECRET", "IG_PASSWORD": "p-SECRET", "IG_API_KEY": "k-SECRET",
              "IG_ACCOUNT_ID": "a-SECRET"}
    del values[key]
    env = tmp_path / ".env"
    env.write_text("".join(f"{k}={v}\n" for k, v in values.items()))
    with pytest.raises(IGLoginFailure) as e:
        load_credentials(env)
    assert key in str(e.value)
    assert "SECRET" not in str(e.value)


def test_env_file_is_ignored_by_git():
    lines = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in lines


# =============================================================================
# 5. Tests never call the real IG
# =============================================================================

def test_the_network_is_blocked_during_tests():
    with pytest.raises(Exception, match="Test tried to"):
        requests.get("https://demo-api.ig.com/gateway/deal/session", timeout=1)


def test_a_client_without_a_pretend_ig_cannot_reach_ig_in_tests():
    client = IGClient(SETTINGS.ig, CREDS, sleep=lambda s: None)
    with pytest.raises(Exception, match="Test tried to"):
        client.login()


# =============================================================================
# 6. The check command (with a pretend IG)
# =============================================================================

def run_check(*replies, creds=CREDS):
    fake = FakeIG(*replies)
    out = io.StringIO()
    code = None
    try:
        code = check.run(SETTINGS, credentials_loader=lambda: creds, http=fake, out=out)
    except SystemExit as e:
        code = e.code
    return code, out.getvalue(), fake


def test_check_makes_exactly_four_ig_calls_and_shows_no_secrets(capsys):
    code, out, fake = run_check(login_ok(), accounts_ok(), switch_ok(), logout_ok())
    assert code == 0
    assert fake.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session"),
                            ("DELETE", "/session")]
    assert "Streaming address received: yes" in out
    assert "IG calls made: 4" in out
    assert "Check passed." in out
    assert last4(CREDS.account_id) in out and last4(OTHER_ACCOUNT) in out
    for secret in SECRETS:
        assert secret not in out + capsys.readouterr().err
    # Only the last 4 characters of any account number are shown.
    for line in out.splitlines():
        for acc in (CREDS.account_id, OTHER_ACCOUNT):
            assert acc[:-4] not in line or "IG address" in line


def test_check_stops_with_78_and_still_logs_out_if_the_account_is_missing(capsys):
    code, out, fake = run_check(login_ok(), accounts_ok(OTHER_ACCOUNT), logout_ok())
    assert code == 78
    assert fake.calls() == [("POST", "/session"), ("GET", "/accounts"), ("DELETE", "/session")]
    assert "account-not-found" in capsys.readouterr().err


def test_check_never_retries_a_slowed_down_login(capsys):
    code, out, fake = run_check(error(403, SLOWED[0]))
    assert code == 78
    assert fake.calls() == [("POST", "/session")]


def test_check_never_relogs_in(capsys):
    code, out, fake = run_check(error(401, "error.security.client-token-invalid"))
    assert code == 78
    assert fake.calls() == [("POST", "/session")]


def test_check_stops_with_78_on_missing_secret(capsys):
    def missing():
        raise IGLoginFailure("missing-secret", "These must be set: IG_ACCOUNT_ID.")
    fake = FakeIG()
    with pytest.raises(SystemExit) as e:
        check.run(SETTINGS, credentials_loader=missing, http=fake, out=io.StringIO())
    assert e.value.code == 78
    assert fake.sent == []
