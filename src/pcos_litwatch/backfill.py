"""Walk PubMed by cursor and fill professor needs.

Corpus key is `pubmed-mesh-pcos`. Each need has key `need:<need_key>`.
"""

from __future__ import annotations

from typing import Any

from .heuristic import skip_reason_for_record
from .http import sleep_polite
from .pubmed import DEFAULT_TERM, fetch_pubmed_page
from .record import Record
from .store import (
    connect,
    finish_run,
    get_cursor,
    insert_tag,
    link_need_source,
    mark_need_filled,
    open_needs,
    set_cursor,
    start_run,
    upsert_source,
)

CORPUS_KEY = "pubmed-mesh-pcos"


def _store_records(conn, records: list[Record]) -> dict[str, Any]:
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


def apply_heuristics(conn, records: list[Record], source_ids: list[int]) -> int:
    n = 0
    for rec, sid in zip(records, source_ids):
        reason = skip_reason_for_record(rec)
        if not reason:
            continue
        insert_tag(
            conn,
            source_id=sid,
            tagger="heuristic",
            novelty=0.05,
            mechanism_area=None,
            is_primary=False,
            is_human=False,
            claims_json=[],
            skip_reason=reason,
        )
        n += 1
    return n


def run_one_page(
    conn,
    query_key: str,
    term: str,
    page_size: int = 200,
    kind: str = "backfill",
) -> dict[str, Any]:
    cursor = get_cursor(conn, query_key)
    if cursor and cursor.get("exhausted"):
        return {"skipped": True, "query_key": query_key, "exhausted": True, "inserted": 0}

    retstart = int(cursor["retstart"]) if cursor else 0
    size = int(cursor["page_size"]) if cursor else page_size
    run_id = start_run(conn, kind)
    try:
        page = fetch_pubmed_page(term=term, retstart=retstart, retmax=size)
        stored = _store_records(conn, page["records"])
        skipped = apply_heuristics(conn, page["records"], stored["ids"])
        set_cursor(
            conn,
            query_key=query_key,
            term=term,
            retstart=page["next_start"],
            page_size=size,
            total_reported=page["count"],
            exhausted=page["exhausted"],
        )
        stats = {
            "query_key": query_key,
            "retstart": retstart,
            "next_start": page["next_start"],
            "count": page["count"],
            "fetched": len(page["records"]),
            "inserted": stored["inserted"],
            "refreshed": stored["refreshed"],
            "heuristic_skipped": skipped,
            "exhausted": page["exhausted"],
            "source_ids": stored["ids"],
        }
        finish_run(conn, run_id, ok=True, stats={k: v for k, v in stats.items() if k != "source_ids"})
        stats["run_id"] = run_id
        return stats
    except Exception as e:
        finish_run(conn, run_id, ok=False, stats={"query_key": query_key, "retstart": retstart}, error=str(e))
        raise


def fill_open_needs(conn, max_needs: int = 2, page_size: int = 40) -> list[dict[str, Any]]:
    results = []
    for need in open_needs(conn, limit=max_needs):
        sleep_polite(0.4)
        key = f"need:{need['need_key']}"
        stats = run_one_page(
            conn,
            query_key=key,
            term=need["pubmed_term"],
            page_size=page_size,
            kind="gapfill",
        )
        source_ids = stats.get("source_ids") or []
        if source_ids:
            with conn.cursor() as cur:
                for sid in source_ids:
                    link_need_source(cur, int(need["id"]), int(sid))
            conn.commit()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM pcos.need_sources WHERE need_id = %s",
                (need["id"],),
            )
            linked = int(cur.fetchone()[0])
        # A need is "filled" only when the undergrad walk of that query is exhausted
        # and we linked at least one paper. Otherwise it stays open/filling.
        if stats.get("exhausted") and linked > 0:
            mark_need_filled(conn, int(need["id"]))
            status = "filled"
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pcos.needs SET status = 'filling', last_filled_at = now(), updated_at = now() WHERE id = %s AND status = 'open'",
                    (need["id"],),
                )
            conn.commit()
            status = "filling"
        stats["need_id"] = need["id"]
        stats["need_key"] = need["need_key"]
        stats["linked"] = linked
        stats["need_status"] = status
        results.append(stats)
    return results


def run_cycle(
    corpus_page_size: int = 200,
    corpus_pages: int = 2,
    need_page_size: int = 40,
    max_needs: int = 2,
    include_corpus: bool = True,
) -> dict[str, Any]:
    conn = connect()
    try:
        need_stats = fill_open_needs(conn, max_needs=max_needs, page_size=need_page_size)
        corpus_pages_out: list[dict[str, Any]] = []
        if include_corpus:
            for i in range(corpus_pages):
                if i:
                    sleep_polite(0.5)
                page = run_one_page(
                    conn,
                    query_key=CORPUS_KEY,
                    term=DEFAULT_TERM,
                    page_size=corpus_page_size,
                    kind="backfill",
                )
                corpus_pages_out.append(page)
                if page.get("exhausted") or page.get("skipped"):
                    break
        corpus = None
        if corpus_pages_out:
            corpus = {
                "pages": len(corpus_pages_out),
                "inserted": sum(int(p.get("inserted") or 0) for p in corpus_pages_out),
                "refreshed": sum(int(p.get("refreshed") or 0) for p in corpus_pages_out),
                "fetched": sum(int(p.get("fetched") or 0) for p in corpus_pages_out),
                "heuristic_skipped": sum(int(p.get("heuristic_skipped") or 0) for p in corpus_pages_out),
                "next_start": corpus_pages_out[-1].get("next_start"),
                "count": corpus_pages_out[-1].get("count"),
                "exhausted": corpus_pages_out[-1].get("exhausted"),
            }
        return {"needs": need_stats, "corpus": corpus}
    finally:
        conn.close()
