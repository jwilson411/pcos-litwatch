"""CLI: collect, print JSON, optionally write Postgres."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .collect import collect
from .record import records_to_json


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pcos-litwatch", description="Collect PCOS literature records.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--pubmed", type=int, default=40, help="PubMed retmax")
    p.add_argument("--trials", type=int, default=20, help="ClinicalTrials.gov page size")
    p.add_argument("--arxiv", type=int, default=15, help="arXiv max_results")
    p.add_argument("--store", action="store_true", help="Upsert into Postgres (needs HERMES_DATABASE_URL)")
    p.add_argument("--quiet", action="store_true", help="Do not print records")
    args = p.parse_args(argv)

    for flag, n in (("--pubmed", args.pubmed), ("--trials", args.trials), ("--arxiv", args.arxiv)):
        if n < 0:
            print(f"pcos-litwatch: {flag} must be >= 0 (got {n})", file=sys.stderr)
            return 2

    if args.store and not (os.environ.get("HERMES_DATABASE_URL") or os.environ.get("DATABASE_URL")):
        print(
            "pcos-litwatch: --store requires a database DSN; set HERMES_DATABASE_URL or DATABASE_URL",
            file=sys.stderr,
        )
        return 2

    records, errors = collect(pubmed_n=args.pubmed, trial_n=args.trials, arxiv_n=args.arxiv)
    stats = {
        "n": len(records),
        "by_type": {},
        "errors": errors,
    }
    for r in records:
        stats["by_type"][r.source_type] = stats["by_type"].get(r.source_type, 0) + 1

    store_stats = None
    if args.store:
        from .store import connect, finish_run, start_run, upsert_sources

        conn = connect()
        run_id = start_run(conn, "collect")
        try:
            store_stats = upsert_sources(conn, records)
            store_stats["errors"] = errors
            finish_run(conn, run_id, ok=not errors or bool(records), stats=store_stats, error="; ".join(errors) or None)
        except Exception as e:
            finish_run(conn, run_id, ok=False, stats={"n": len(records)}, error=str(e))
            raise
        finally:
            conn.close()
        stats["store"] = {k: v for k, v in store_stats.items() if k != "ids"}

    if not args.quiet:
        print(records_to_json(records))
    print(json.dumps({"stats": stats}, indent=2), file=sys.stderr)
    return 1 if errors and not records else 0


if __name__ == "__main__":
    raise SystemExit(main())
