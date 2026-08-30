# pcos-litwatch

Stdlib Python collector for a long-running PCOS literature watch.

It pulls recent records from PubMed E-utilities, ClinicalTrials.gov v2, and arXiv. It does **not** diagnose, treat, or claim a cure. The optional Postgres sink is for a research ledger, not a medical record.

This repo is the public, testable core. The Hermes jobs that tag novelty (local Qwen) and write briefs (Grok) live next to it, not inside it.

## Why this exists

PCOS (also discussed as polyendocrine metabolic ovarian syndrome / PMOS) is common, heterogeneous, and still without a disease-modifying cure. A durable search needs:

1. A collector that does not invent papers.
2. A store that remembers what was already seen.
3. A cheap model that only tags "is this new / on-mechanism".
4. A strong model that actually reads.

Most days this pipeline will find nothing that changes the map. That is the expected result.

## Install

```bash
python -m pip install -e ".[dev]"
make test
```

Live collect (no database):

```bash
python -m pcos_litwatch.cli --pubmed 10 --trials 5 --arxiv 5
```

Optional Postgres (`CREATE SCHEMA` from `schema/001_init.sql` first):

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
src/pcos_litwatch/   collector, parsers, optional store
schema/001_init.sql  ledger tables
tests/               fixture parsers, no network in CI
```

## License

MIT
