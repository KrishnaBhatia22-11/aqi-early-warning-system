"""The CPCB client pulls through the India relay when CPCB_RELAY_URL is set."""

import requests

from src.data import cpcb_client


class _Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body if body is not None else {"total": 2, "records": [{"a": 1}, {"b": 2}]}

    def json(self):
        return self._body


def _capture(monkeypatch, resp=None):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append({"url": url, "params": dict(params or {}), "headers": dict(headers or {})})
        return resp or _Resp()

    monkeypatch.setattr(cpcb_client.requests, "get", fake_get)
    monkeypatch.setattr(cpcb_client.time, "sleep", lambda _s: None)
    return calls


def test_relay_mode_sends_token_and_no_key(monkeypatch):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", "https://example.vercel.app/api/cpcb")
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_TOKEN", "secret-token")
    monkeypatch.setattr(cpcb_client, "DATA_GOV_API_KEY", "the-key")
    calls = _capture(monkeypatch)

    body = cpcb_client._get_page(0)

    assert body["total"] == 2
    call = calls[0]
    assert call["url"] == "https://example.vercel.app/api/cpcb"
    assert call["params"] == {"limit": 1000, "offset": 0}
    assert call["headers"]["X-Relay-Token"] == "secret-token"
    assert "api-key" not in call["params"]
    assert "User-Agent" in call["headers"]


def test_direct_mode_unchanged(monkeypatch):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", None)
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_TOKEN", None)
    monkeypatch.setattr(cpcb_client, "DATA_GOV_API_KEY", "the-key")
    calls = _capture(monkeypatch)

    cpcb_client._get_page(1000, limit=500)

    call = calls[0]
    assert call["url"] == cpcb_client.BASE_URL
    assert call["params"] == {"api-key": "the-key", "format": "json", "limit": 500, "offset": 1000}
    assert "X-Relay-Token" not in call["headers"]


def test_relay_mode_fetches_without_local_key(monkeypatch):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", "https://example.vercel.app/api/cpcb")
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_TOKEN", "secret-token")
    monkeypatch.setattr(cpcb_client, "DATA_GOV_API_KEY", None)
    _capture(monkeypatch)

    records, complete = cpcb_client.fetch_all_records()

    assert len(records) == 2 and complete


def test_no_source_configured_returns_nothing(monkeypatch):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", None)
    monkeypatch.setattr(cpcb_client, "DATA_GOV_API_KEY", None)
    calls = _capture(monkeypatch)

    assert cpcb_client.fetch_all_records() == ([], False)
    assert calls == []


def test_key_is_redacted_from_connection_errors(monkeypatch, capsys):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", None)
    monkeypatch.setattr(cpcb_client, "DATA_GOV_API_KEY", "SECRETKEY123")
    monkeypatch.setattr(cpcb_client.time, "sleep", lambda _s: None)

    def boom(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError(
            "Max retries exceeded with url: /resource/x?api-key=SECRETKEY123&format=json"
        )

    monkeypatch.setattr(cpcb_client.requests, "get", boom)

    assert cpcb_client._get_page(0) is None
    out = capsys.readouterr().out
    assert "SECRETKEY123" not in out
    assert "api-key=***" in out


def test_status_reports_relay(monkeypatch):
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_URL", "https://example.vercel.app/api/cpcb")
    monkeypatch.setattr(cpcb_client, "CPCB_RELAY_TOKEN", "secret-token")
    status = cpcb_client.cache_status()
    assert status["via_relay"] is True
    assert status["relay_token_present"] is True
