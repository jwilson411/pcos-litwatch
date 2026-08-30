"""Optional Postgres sink. Importing this module does not require psycopg2
until you call connect()."""

from __future__ import annotations

import json
import os
from typing import Any, Iterable

from .record import Record


def dsn_from_env() -> str:
    url = os.environ.get("HERMES_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("HERMES_DATABASE_URL or DATABASE_URL is not set")
    return url


def connect(dsn: str | None = None):
    import psycopg2

    return psycopg2.connect(dsn or dsn_from_env())


def upsert_source(cur, rec: Record) -> tuple[int, bool]:
    """Insert or refresh a source. Returns (id, inserted)."""
    cur.execute(
        """
        INSERT INTO pcos.sources (
            source_type, external_id, doi, title, abstract, authors, journal,
            published_on, url, raw, content_hash, first_seen_at, last_seen_at
        )
        VALUES (
            %(source_type)s, %(external_id)s, %(doi)s, %(title)s, %(abstract)s,
            %(authors)s, %(journal)s, %(published_on)s, %(url)s, %(raw)s::jsonb,
            %(content_hash)s, now(), now()
        )
        ON CONFLICT (source_type, external_id) DO UPDATE SET
            doi = COALESCE(EXCLUDED.doi, pcos.sources.doi),
            title = EXCLUDED.title,
            abstract = COALESCE(EXCLUDED.abstract, pcos.sources.abstract),
            authors = COALESCE(EXCLUDED.authors, pcos.sources.authors),
            journal = COALESCE(EXCLUDED.journal, pcos.sources.journal),
            published_on = COALESCE(EXCLUDED.published_on, pcos.sources.published_on),
            url = EXCLUDED.url,
            raw = EXCLUDED.raw,
            content_hash = EXCLUDED.content_hash,
            last_seen_at = now()
        RETURNING id, (xmax = 0) AS inserted
        """,
        {
            "source_type": rec.source_type,
            "external_id": rec.external_id,
            "doi": rec.doi,
            "title": rec.title,
            "abstract": rec.abstract,
            "authors": rec.authors,
            "journal": rec.journal,
            "published_on": rec.published_on,
            "url": rec.url,
            "raw": json.dumps(rec.raw or {}),
            "content_hash": rec.hash(),
        },
    )
    row = cur.fetchone()
    return int(row[0]), bool(row[1])


def upsert_sources(conn, records: Iterable[Record]) -> dict[str, Any]:
    inserted = 0
    refreshed = 0
    ids: list[int] = []
    with conn.cursor() as cur:
        for rec in records:
            sid, is_new = upsert_source(cur, rec)
            ids.append(sid)
            if is_new:
                inserted += 1
            else:
                refreshed += 1
    conn.commit()
    return {"inserted": inserted, "refreshed": refreshed, "ids": ids, "total": inserted + refreshed}


def start_run(conn, kind: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pcos.runs (kind) VALUES (%s) RETURNING id",
            (kind,),
        )
        run_id = int(cur.fetchone()[0])
    conn.commit()
    return run_id


def finish_run(conn, run_id: int, ok: bool, stats: dict[str, Any], error: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE pcos.runs
            SET finished_at = now(), ok = %s, stats = %s::jsonb, error = %s
            WHERE id = %s
            """,
            (ok, json.dumps(stats), error, run_id),
        )
    conn.commit()


def upsert_claim(cur, claim_key: str, statement: str, polarity: str, evidence_grade: str, notes: str | None = None) -> int:
    cur.execute(
        """
        INSERT INTO pcos.claims (claim_key, statement, polarity, evidence_grade, notes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (claim_key) DO UPDATE SET
            statement = EXCLUDED.statement,
            polarity = EXCLUDED.polarity,
            evidence_grade = EXCLUDED.evidence_grade,
            notes = COALESCE(EXCLUDED.notes, pcos.claims.notes),
            updated_at = now()
        RETURNING id
        """,
        (claim_key, statement, polarity, evidence_grade, notes),
    )
    return int(cur.fetchone()[0])


def link_claim_source(cur, claim_id: int, source_id: int) -> None:
    cur.execute(
        """
        INSERT INTO pcos.claim_sources (claim_id, source_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (claim_id, source_id),
    )


def insert_finding(
    conn,
    title: str,
    body: str,
    analyst: str,
    hypothesis_area: str | None = None,
    novelty: float | None = None,
    source_ids: list[int] | None = None,
    run_id: int | None = None,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pcos.findings (run_id, title, body, hypothesis_area, novelty, analyst, source_ids)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (run_id, title, body, hypothesis_area, novelty, analyst, source_ids or []),
        )
        fid = int(cur.fetchone()[0])
    conn.commit()
    return fid


def untagged_sources(conn, tagger: str, limit: int = 25) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.source_type, s.external_id, s.title, s.abstract, s.url, s.published_on
            FROM pcos.sources s
            LEFT JOIN pcos.source_tags t
              ON t.source_id = s.id AND t.tagger = %s
            WHERE t.id IS NULL
            ORDER BY s.published_on DESC NULLS LAST, s.id DESC
            LIMIT %s
            """,
            (tagger, limit),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def insert_tag(
    conn,
    source_id: int,
    tagger: str,
    novelty: float | None,
    mechanism_area: str | None,
    is_primary: bool | None,
    is_human: bool | None,
    claims_json: list[Any] | None,
    skip_reason: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pcos.source_tags (
                source_id, tagger, novelty, mechanism_area, is_primary, is_human,
                claims_json, skip_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (source_id, tagger) DO UPDATE SET
                novelty = EXCLUDED.novelty,
                mechanism_area = EXCLUDED.mechanism_area,
                is_primary = EXCLUDED.is_primary,
                is_human = EXCLUDED.is_human,
                claims_json = EXCLUDED.claims_json,
                skip_reason = EXCLUDED.skip_reason,
                tagged_at = now()
            """,
            (
                source_id,
                tagger,
                novelty,
                mechanism_area,
                is_primary,
                is_human,
                json.dumps(claims_json or []),
                skip_reason,
            ),
        )
    conn.commit()
