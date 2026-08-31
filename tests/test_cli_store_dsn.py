"""`--store` without a DSN fails before collecting (exit 2, one stderr line)."""

from pcos_litwatch import cli, store

ARGS = ["--store", "--pubmed", "0", "--trials", "0", "--arxiv", "0", "--quiet"]


def test_store_without_dsn_exits_2_before_collect(monkeypatch, capsys):
    monkeypatch.delenv("HERMES_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    collected: list[dict] = []
    monkeypatch.setattr(cli, "collect", lambda **kw: collected.append(kw) or ([], []))

    rc = cli.main(ARGS)
    captured = capsys.readouterr()

    assert rc == 2
    assert "Traceback" not in captured.err
    lines = [ln for ln in captured.err.splitlines() if ln.strip()]
    assert len(lines) == 1, lines
    assert "--store" in lines[0]
    assert captured.out == ""
    assert collected == []


def test_store_with_dsn_proceeds_to_collect(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_DATABASE_URL", "postgresql://dummy/dummy")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    collected: list[dict] = []
    monkeypatch.setattr(cli, "collect", lambda **kw: collected.append(kw) or ([], []))

    class FakeConn:
        def close(self):
            pass

    monkeypatch.setattr(store, "connect", lambda *a, **k: FakeConn())
    monkeypatch.setattr(store, "start_run", lambda *a, **k: 1)
    monkeypatch.setattr(store, "upsert_sources", lambda *a, **k: {"n": 0, "ids": []})
    monkeypatch.setattr(store, "finish_run", lambda *a, **k: None)

    rc = cli.main(ARGS)
    capsys.readouterr()

    assert rc == 0
    assert len(collected) == 1
