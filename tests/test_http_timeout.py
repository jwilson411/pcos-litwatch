"""`get_bytes` passes its timeout through to urlopen (no network)."""

import urllib.request

from pcos_litwatch.http import DEFAULT_TIMEOUT, get_bytes

URL = "https://example.invalid/thing"


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b"ok"


def patch_urlopen(monkeypatch):
    calls: list[dict] = []

    def fake_urlopen(req, *args, **kwargs):
        calls.append({"req": req, "args": args, "kwargs": kwargs})
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


def test_get_bytes_honors_explicit_timeout(monkeypatch):
    calls = patch_urlopen(monkeypatch)

    assert get_bytes(URL, timeout=7) == b"ok"

    assert len(calls) == 1
    assert calls[0]["kwargs"]["timeout"] == 7


def test_get_bytes_uses_default_timeout(monkeypatch):
    calls = patch_urlopen(monkeypatch)

    assert get_bytes(URL) == b"ok"

    assert len(calls) == 1
    assert calls[0]["kwargs"]["timeout"] == DEFAULT_TIMEOUT == 30
