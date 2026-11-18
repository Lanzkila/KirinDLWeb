from __future__ import annotations

import socket

import pytest

from kirindl_server.security import UnsafeURLError, validate_public_http_url


def _public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]


def test_accepts_public_https_url(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    value = validate_public_http_url("https://example.com/watch?v=abc#section")
    assert value == "https://example.com/watch?v=abc"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "http://localhost/admin",
        "http://127.0.0.1:8080/",
        "http://user:pass@example.com/",
        "https://example.com:8443/",
    ],
)
def test_rejects_unsafe_url_shapes(url):
    with pytest.raises(UnsafeURLError):
        validate_public_http_url(url)


def test_rejects_private_dns_result(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.9", 443)),
        ],
    )
    with pytest.raises(UnsafeURLError):
        validate_public_http_url("https://rebound.example/")


def test_rejects_mixed_public_and_private_dns(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.20", 443)),
        ],
    )
    with pytest.raises(UnsafeURLError):
        validate_public_http_url("https://mixed.example/")
