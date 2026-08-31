"""Count validation (negative -> exit 2) and zero-means-skip behaviour."""

import sys

import pytest

from pcos_litwatch import cli
from pcos_litwatch.collect import collect

# `pcos_litwatch.collect` is re-exported as the function, so grab the module itself.
collect_mod = sys.modules["pcos_litwatch.collect"]


@pytest.fixture
def calls(monkeypatch):
    """Record fetcher calls instead of hitting the network."""
    seen: list[str] = []

    def fake(name):
        def _f(**kwargs):
            seen.append(name)
            return []

        return _f

    monkeypatch.setattr(collect_mod, "fetch_pubmed", fake("pubmed"))
    monkeypatch.setattr(collect_mod, "fetch_trials", fake("trials"))
    monkeypatch.setattr(collect_mod, "fetch_arxiv", fake("arxiv"))
    monkeypatch.setattr(collect_mod, "sleep_polite", lambda *a, **k: None)
    return seen


@pytest.mark.parametrize("flag", ["--pubmed", "--trials", "--arxiv"])
def test_negative_count_exits_2_with_one_stderr_line(flag, calls, monkeypatch, capsys):
    collected: list[tuple] = []
    monkeypatch.setattr(cli, "collect", lambda **kw: collected.append(kw) or ([], []))

    rc = cli.main([flag, "-1"])
    captured = capsys.readouterr()

    assert rc == 2
    assert "Traceback" not in captured.err
    assert "ValueError" not in captured.err
    lines = [ln for ln in captured.err.splitlines() if ln.strip()]
    assert len(lines) == 1, lines
    assert flag in lines[0]
    assert captured.out == ""
    assert collected == []
    assert calls == []


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"pubmed_n": 0, "trial_n": 5, "arxiv_n": 0}, ["trials"]),
        ({"pubmed_n": 5, "trial_n": 0, "arxiv_n": 0}, ["pubmed"]),
        ({"pubmed_n": 0, "trial_n": 0, "arxiv_n": 5}, ["arxiv"]),
        ({"pubmed_n": 0, "trial_n": 0, "arxiv_n": 0}, []),
        ({"pubmed_n": 1, "trial_n": 2, "arxiv_n": 3}, ["pubmed", "trials", "arxiv"]),
    ],
)
def test_zero_skips_that_source(kwargs, expected, calls):
    records, errors = collect(**kwargs)

    assert calls == expected
    assert records == []
    assert errors == []


def test_cli_all_zero_returns_0_without_fetching(calls, capsys):
    rc = cli.main(["--pubmed", "0", "--trials", "0", "--arxiv", "0", "--quiet"])
    capsys.readouterr()

    assert rc == 0
    assert calls == []
