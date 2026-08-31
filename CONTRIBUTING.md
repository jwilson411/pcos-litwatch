# Contributing

## Setup

Python 3.11+. Create a venv, then:

```bash
python -m pip install -e ".[dev]"
```

`psycopg2` is optional (`pip install -e ".[postgres]"`). The collector itself is stdlib.

## Tests

CI runs `ruff check` (lint only, no format) and `pytest` on 3.11 and 3.12. Locally:

```bash
make lint
make test
```

`make test` is `python3 -m pytest -q`. Parsers use `tests/fixtures` (and in-file fixture bytes). CI has no network.

Live collect is opt-in. It is not in Actions:

```bash
python -m pcos_litwatch.cli --pubmed 10 --trials 5 --arxiv 5
```

`--store` needs `HERMES_DATABASE_URL` (or `DATABASE_URL`). Do not add a CI job that hits PubMed, ClinicalTrials.gov, or arXiv.

## Adding a source

1. Add a module under `src/pcos_litwatch/` with a pure parser (`bytes -> list[Record]`) and a fetch helper.
2. Add a fixture test under `tests/` that never opens the network. Prefer `tests/fixtures/` for XML/JSON.
3. Wire the fetch into `collect.py` so a failure in that source does not kill the others.
4. If the source is counted on the CLI, add a non-negative count check like the existing PubMed/trials/arXiv flags.

This repo is not medical advice. Do not add PDF downloads or a cure claim.

Open a PR against `main`. Keep secrets and `/mnt/defiant` paths out of the tree.
