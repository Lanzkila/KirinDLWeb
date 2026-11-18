from __future__ import annotations

import io
import json
from urllib.error import URLError

import pytest

from kirindl_server.turnstile import (
    TurnstileUnavailableError,
    TurnstileVerificationError,
    verify_turnstile_token,
)


def _response(payload: dict):
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


def test_accepts_valid_token_for_allowed_hostname_and_action(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["data"] = request.data.decode("ascii")
        captured["timeout"] = timeout
        return _response({
            "success": True,
            "hostname": "lanzkila.github.io",
            "action": "download",
        })

    monkeypatch.setattr("kirindl_server.turnstile.urlopen", fake_urlopen)
    verify_turnstile_token("token-value", "secret-value", {"lanzkila.github.io"})
    assert captured["url"].endswith("/siteverify")
    assert "secret=secret-value" in captured["data"]
    assert "response=token-value" in captured["data"]


def test_rejects_invalid_or_replayed_token(monkeypatch):
    monkeypatch.setattr(
        "kirindl_server.turnstile.urlopen",
        lambda *_args, **_kwargs: _response({"success": False, "error-codes": ["timeout-or-duplicate"]}),
    )
    with pytest.raises(TurnstileVerificationError, match="expired"):
        verify_turnstile_token("old-token", "secret", {"lanzkila.github.io"})


def test_rejects_wrong_hostname(monkeypatch):
    monkeypatch.setattr(
        "kirindl_server.turnstile.urlopen",
        lambda *_args, **_kwargs: _response({
            "success": True,
            "hostname": "evil.example",
            "action": "download",
        }),
    )
    with pytest.raises(TurnstileVerificationError, match="unrecognised"):
        verify_turnstile_token("token", "secret", {"lanzkila.github.io"})


def test_rejects_wrong_action(monkeypatch):
    monkeypatch.setattr(
        "kirindl_server.turnstile.urlopen",
        lambda *_args, **_kwargs: _response({
            "success": True,
            "hostname": "lanzkila.github.io",
            "action": "login",
        }),
    )
    with pytest.raises(TurnstileVerificationError, match="action"):
        verify_turnstile_token("token", "secret", {"lanzkila.github.io"})


def test_siteverify_network_error_is_reported_as_unavailable(monkeypatch):
    monkeypatch.setattr(
        "kirindl_server.turnstile.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline")),
    )
    with pytest.raises(TurnstileUnavailableError):
        verify_turnstile_token("token", "secret", {"lanzkila.github.io"})


def test_rejects_empty_token_before_network_call():
    with pytest.raises(TurnstileVerificationError):
        verify_turnstile_token("", "secret", {"lanzkila.github.io"})
