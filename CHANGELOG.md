# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Ruff lint-only CI job (`ruff check`; no format)
- Python 3.11 and 3.12 test matrix
- CLI rejects negative `--pubmed` / `--trials` / `--arxiv` with exit 2; zero skips that source
- `--store` without `HERMES_DATABASE_URL` or `DATABASE_URL` exits 2 before collect (no traceback)
- Empty `py.typed` marker so type checkers treat the install as typed
- CONTRIBUTING.md
- SECURITY.md (GitHub private advisory; HTTPS collectors; optional Postgres DSN; no PDFs; not medical advice)
- Weekly Dependabot for pip and github-actions (python-deps group, no auto-merge)

### Tests

- `get_bytes` passes the timeout kwarg through to `urlopen` (timeout=7 and default 30; no network)

## [0.1.0] - 2026-08-30

### Added

- Public MIT extract of the PCOS literature collector
- Stdlib HTTPS pulls from PubMed E-utilities, ClinicalTrials.gov v2, and arXiv
- PubMed pagination, professor `needs` queue, and corpus backfill
- Heuristic pre-filter and batched HTTP for a local Qwen tagging pass
- Optional Postgres ledger (`psycopg2` extra); collector itself is zero-dep
- CLI (`pcos-litwatch`) and fixture-based parser tests (no network in CI)

[Unreleased]: https://github.com/jwilson411/pcos-litwatch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jwilson411/pcos-litwatch/releases/tag/v0.1.0
