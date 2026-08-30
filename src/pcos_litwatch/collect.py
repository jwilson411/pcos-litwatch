"""Fan-in collector. Failures in one source do not kill the others."""

from __future__ import annotations

from .arxiv_src import fetch_arxiv
from .http import sleep_polite
from .pubmed import fetch_pubmed
from .record import Record
from .trials import fetch_trials


def collect(pubmed_n: int = 40, trial_n: int = 20, arxiv_n: int = 15) -> tuple[list[Record], list[str]]:
    records: list[Record] = []
    errors: list[str] = []

    try:
        records.extend(fetch_pubmed(retmax=pubmed_n))
    except Exception as e:
        errors.append(f"pubmed:{type(e).__name__}:{e}")

    sleep_polite(0.5)

    try:
        records.extend(fetch_trials(page_size=trial_n))
    except Exception as e:
        errors.append(f"trials:{type(e).__name__}:{e}")

    sleep_polite(0.5)

    try:
        records.extend(fetch_arxiv(max_results=arxiv_n))
    except Exception as e:
        errors.append(f"arxiv:{type(e).__name__}:{e}")

    seen: set[tuple[str, str]] = set()
    unique: list[Record] = []
    for r in records:
        key = (r.source_type, r.external_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique, errors
