"""arXiv Atom search. Sequential. PCOS hits are sparse; keep the query tight."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .http import encode_query, get_bytes
from .record import Record

ATOM = "http://www.w3.org/2005/Atom"
ARXIV = "http://arxiv.org/schemas/atom"
EXPORT = "https://export.arxiv.org/api/query"
DEFAULT_QUERY = 'all:"polycystic ovary" OR all:PCOS OR all:"polycystic ovarian"'


def parse_atom(xml_bytes: bytes) -> list[Record]:
    root = ET.fromstring(xml_bytes)
    ns = {"a": ATOM, "arxiv": ARXIV}
    out: list[Record] = []
    for entry in root.findall("a:entry", ns):
        raw_id = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        arxiv_id = raw_id.rsplit("/abs/", 1)[-1]
        if not arxiv_id:
            continue
        title = " ".join((entry.findtext("a:title", default="", namespaces=ns) or "").split())
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip() or None
        published = (entry.findtext("a:published", default="", namespaces=ns) or "")[:10] or None
        authors = [
            (a.findtext("a:name", default="", namespaces=ns) or "").strip()
            for a in entry.findall("a:author", ns)
        ]
        doi = None
        doi_el = entry.find("arxiv:doi", ns)
        if doi_el is not None and doi_el.text:
            doi = doi_el.text.strip()
        out.append(
            Record(
                source_type="preprint",
                external_id=arxiv_id,
                title=title or arxiv_id,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                doi=doi,
                abstract=summary,
                authors="; ".join(a for a in authors if a) or None,
                journal="arXiv",
                published_on=published,
                raw={"arxiv_id": arxiv_id},
            )
        )
    return out


def fetch_arxiv(query: str = DEFAULT_QUERY, max_results: int = 15) -> list[Record]:
    q = encode_query(
        {
            "search_query": query,
            "start": "0",
            "max_results": str(max_results),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    xml_bytes = get_bytes(f"{EXPORT}?{q}")
    return parse_atom(xml_bytes)
