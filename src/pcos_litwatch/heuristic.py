"""Cheap skip rules so Qwen never sees the whole nightly pile.

These are title/type heuristics only. They do not decide science.
Qwen still tags the remainder in batches of 5.
"""

from __future__ import annotations

import re

from .record import Record

_SKIP_TITLE = re.compile(
    r"\b("
    r"expression of concern|retract(?:ion|ed)|corrigendum|erratum|"
    r"nomenclature|terminology change|renam(?:e|ed|ing)|"
    r"network pharmacology|in silico|molecular docking|"
    r"traditional chinese|ethnopharmacolog|"
    r"case report\b"
    r")\b",
    re.I,
)

_REVIEW_TITLE = re.compile(
    r"\b(narrative review|systematic review|literature review|scoping review|"
    r"mini[- ]review|a review\b|review:)\b",
    re.I,
)

_ANIMAL = re.compile(
    r"\b(rat|rats|mouse|mice|murine|zebrafish|rodent|ovine|porcine)\b",
    re.I,
)

_HUMAN_HINT = re.compile(
    r"\b(women|woman|patient|patients|trial|randomized|randomised|"
    r"placebo|ivf)\b",
    re.I,
)

_PRIORITY = re.compile(
    r"\b(randomized|randomised|clinical trial|meta-analysis|metaanalysis|"
    r"phase [123]|double[- ]blind|placebo)\b",
    re.I,
)


def skip_reason_for(title: str, source_type: str | None = None, abstract: str | None = None) -> str | None:
    text = title or ""
    if _SKIP_TITLE.search(text):
        return "heuristic:title-skip"
    if source_type == "review" or _REVIEW_TITLE.search(text):
        if not _PRIORITY.search(text):
            return "heuristic:review"
    blob = f"{text} {abstract or ''}"
    if _ANIMAL.search(blob) and not _HUMAN_HINT.search(blob):
        return "heuristic:animal-only"
    return None


def skip_reason_for_record(rec: Record) -> str | None:
    return skip_reason_for(rec.title, rec.source_type, rec.abstract)


def is_priority_title(title: str) -> bool:
    return bool(_PRIORITY.search(title or ""))
