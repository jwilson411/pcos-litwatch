from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


def content_hash(parts: list[str]) -> str:
    blob = "\n".join(p or "" for p in parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass
class Record:
    source_type: str
    external_id: str
    title: str
    url: str
    doi: str | None = None
    abstract: str | None = None
    authors: str | None = None
    journal: str | None = None
    published_on: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def hash(self) -> str:
        return content_hash(
            [
                self.source_type,
                self.external_id,
                self.title,
                self.abstract or "",
                self.published_on or "",
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.hash()
        return d


def records_to_json(records: list[Record]) -> str:
    return json.dumps([r.to_dict() for r in records], indent=2, sort_keys=True)
