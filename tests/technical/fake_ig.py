"""A pretend IG for tests. It plays back scripted replies, one per request, in
order, and records every request. It never touches the network."""

from __future__ import annotations

import json as jsonlib
from dataclasses import dataclass, field
from typing import Any

import requests
from requests.structures import CaseInsensitiveDict

from ig.secrets import IGCredentials

CREDS = IGCredentials(
    username="test-user-name",
    password="Pa55#word-SECRET",
    api_key="APIKEY-0123456789abcdef",
    account_id="ZX9Q7ACC1",
)
OTHER_ACCOUNT = "OTHERACC55"
STREAMING = "https://demo-apd.lightstreamer.example"
SECRETS = (CREDS.username, CREDS.password, CREDS.api_key, CREDS.account_id,
           OTHER_ACCOUNT, STREAMING, "CST-token-1", "XST-token-1", "CST-token-2", "XST-token-2")


@dataclass
class Reply:
    status_code: int
    body: Any = None
    headers: dict = field(default_factory=dict)
    raw_text: str | None = None

    def __post_init__(self):
        self.headers = CaseInsensitiveDict(self.headers)

    def json(self):
        if self.raw_text is not None:
            return jsonlib.loads(self.raw_text)
        if self.body is None:
            raise ValueError("no body")
        return self.body

    @property
    def text(self):
        return self.raw_text if self.raw_text is not None else jsonlib.dumps(self.body)


class NoReply:
    """Stands in for a network failure (no reply from IG)."""


@dataclass
class Sent:
    method: str
    url: str
    path: str
    headers: dict
    json: Any
    timeout: Any


class FakeIG:
    BASE = "https://demo-api.ig.com/gateway/deal"

    def __init__(self, *replies):
        self.replies = list(replies)
        self.sent: list[Sent] = []

    def request(self, method, url, headers=None, json=None, timeout=None):
        assert url.startswith(self.BASE), url
        self.sent.append(Sent(method, url, url[len(self.BASE):], dict(headers or {}), json, timeout))
        if not self.replies:
            raise AssertionError(f"Unexpected extra IG call: {method} {url[len(self.BASE):]}")
        reply = self.replies.pop(0)
        if isinstance(reply, NoReply):
            raise requests.ConnectionError("pretend network failure")
        return reply

    def calls(self):
        return [(s.method, s.path) for s in self.sent]

    def all_used(self):
        return not self.replies


# ---- ready-made replies -----------------------------------------------------

def login_ok(n=1, endpoint=STREAMING, current=OTHER_ACCOUNT):
    body = {"accountType": "CFD", "currentAccountId": current, "clientId": "123"}
    if endpoint is not None:
        body["lightstreamerEndpoint"] = endpoint
    return Reply(200, body, {"CST": f"CST-token-{n}", "X-SECURITY-TOKEN": f"XST-token-{n}"})


def accounts_ok(*ids):
    ids = ids or (OTHER_ACCOUNT, CREDS.account_id)
    return Reply(200, {"accounts": [
        {"accountId": i, "accountType": "CFD" if k == 0 else "SPREADBET", "preferred": k == 0}
        for k, i in enumerate(ids)
    ]})


def switch_ok(token="XST-switched"):
    return Reply(200, {"trailingStopsEnabled": False}, {"X-SECURITY-TOKEN": token})


def error(status, code=None):
    return Reply(status, {"errorCode": code} if code else None)


def logout_ok():
    return Reply(204, None)
