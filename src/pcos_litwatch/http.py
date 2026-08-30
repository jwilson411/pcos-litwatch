"""Tiny stdlib HTTP helper with a polite User-Agent."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = "pcos-litwatch/0.1 (+https://github.com/jwilson411/pcos-litwatch)"
DEFAULT_TIMEOUT = 30


def get_bytes(url: str, timeout: int = DEFAULT_TIMEOUT, extra_headers: dict[str, str] | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Any:
    raw = get_bytes(url, timeout=timeout, extra_headers={"Accept": "application/json"})
    return json.loads(raw.decode("utf-8"))


def get_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    return get_bytes(url, timeout=timeout).decode("utf-8", errors="replace")


def sleep_polite(seconds: float = 0.4) -> None:
    time.sleep(seconds)


def encode_query(params: dict[str, str]) -> str:
    return urllib.parse.urlencode(params)
