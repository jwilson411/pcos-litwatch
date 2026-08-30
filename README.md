# pcos-litwatch

Stdlib Python collector for a long-running PCOS literature watch.

It pulls records from PubMed E-utilities, ClinicalTrials.gov v2, and arXiv. It paginates PubMed so a ledger can grow into the tens of thousands. It does **not** diagnose, treat, or claim a cure. The optional Postgres sink is a research ledger, not a medical record.

This repo is the public, testable core. Hermes jobs that tag novelty (local Qwen) and write briefs (Grok) live next to it.

## Split of labor

1. **Undergrads (scripts)** walk PubMed by cursor and fill professor `needs` (tight MeSH queries).
2. **Qwen** tags novelty as JSON. It does not brief.
3. **Grok** reads, cites, files new needs when the ledger is too thin to answer a load-bearing question.

Most days nothing changes the "no established cure" map. That is expected.

## Install

```bash
python -m pip install -e ".[dev]"
make test
```

Live collect (no database):

```bash
python -m pcos_litwatch.cli --pubmed 10 --trials 5 --arxiv 5
```

Optional Postgres (`schema/001_init.sql` then `schema/002_needs.sql`):

```bash
export HERMES_DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/db
python -m pcos_litwatch.cli --store --quiet
```

`psycopg2` is an extra (`pip install -e ".[postgres]"`). The collector itself is stdlib.

## What it will not do

- Give medical advice
- Call a new paper a cure
- Download PDFs or model weights
- Store credentials

## Layout

```
src/pcos_litwatch/   collector, parsers, backfill cursor, optional store
schema/              001_init.sql + 002_needs.sql
tests/               fixture parsers, no network in CI
```

## License

MIT
