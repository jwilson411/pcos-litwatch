"""PubMed E-utilities fetch. Sequential. No API key required for low volume."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable

from .http import encode_query, get_bytes, get_json, sleep_polite
from .record import Record

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_TERM = '"polycystic ovary syndrome"[MeSH Terms] OR PCOS[Title] OR "polyendocrine metabolic ovarian syndrome"[Title]'


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def parse_pubmed_xml(xml_bytes: bytes) -> list[Record]:
    root = ET.fromstring(xml_bytes)
    out: list[Record] = []
    for art in root.findall(".//PubmedArticle"):
        medline = art.find("MedlineCitation")
        if medline is None:
            continue
        pmid = _text(medline.find("PMID"))
        article = medline.find("Article")
        if not pmid or article is None:
            continue
        title = _text(article.find("ArticleTitle")) or f"PMID {pmid}"
        abstract_bits = [_text(n) for n in article.findall("Abstract/AbstractText")]
        abstract = "\n".join(b for b in abstract_bits if b) or None
        authors = []
        for au in article.findall("AuthorList/Author"):
            last = _text(au.find("LastName"))
            initials = _text(au.find("Initials"))
            if last:
                authors.append(f"{last} {initials}".strip())
            else:
                collab = _text(au.find("CollectiveName"))
                if collab:
                    authors.append(collab)
        journal = _text(article.find("Journal/Title")) or None
        pub_date = article.find("Journal/JournalIssue/PubDate")
        published_on = None
        if pub_date is not None:
            y = _text(pub_date.find("Year"))
            m = _text(pub_date.find("Month"))
            d = _text(pub_date.find("Day"))
            if y:
                published_on = f"{y}-{_month_to_num(m):02d}-{int(d or '1'):02d}"
        doi = None
        for aid in article.findall("ELocationID"):
            if (aid.get("EIdType") or "").lower() == "doi":
                doi = _text(aid)
                break
        if not doi:
            for aid in art.findall(".//ArticleId"):
                if (aid.get("IdType") or "").lower() == "doi":
                    doi = _text(aid)
                    break
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        pub_types = [_text(n).lower() for n in article.findall("PublicationTypeList/PublicationType")]
        source_type = "guideline" if any("guideline" in p or "practice guideline" in p for p in pub_types) else "pubmed"
        if any("review" in p for p in pub_types) and source_type == "pubmed":
            source_type = "review"
        out.append(
            Record(
                source_type=source_type,
                external_id=pmid,
                title=title,
                url=url,
                doi=doi,
                abstract=abstract,
                authors="; ".join(authors) if authors else None,
                journal=journal,
                published_on=published_on,
                raw={"pmid": pmid, "pub_types": pub_types, "doi": doi},
            )
        )
    return out


def _month_to_num(m: str) -> int:
    if not m:
        return 1
    if m.isdigit():
        return max(1, min(12, int(m)))
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    return months.get(m[:3].lower(), 1)


def parse_esearch(data: dict) -> dict:
    """Pull idlist + count from an E-utilities esearch JSON body."""
    result = data.get("esearchresult") or {}
    ids = [str(x) for x in (result.get("idlist") or [])]
    try:
        count = int(result.get("count") or 0)
    except (TypeError, ValueError):
        count = 0
    try:
        retstart = int(result.get("retstart") or 0)
    except (TypeError, ValueError):
        retstart = 0
    return {"ids": ids, "count": count, "retstart": retstart}


def esearch_page(term: str, retstart: int = 0, retmax: int = 40) -> dict:
    q = encode_query(
        {
            "db": "pubmed",
            "retmode": "json",
            "retmax": str(retmax),
            "retstart": str(retstart),
            "sort": "pub date",
            "term": term,
        }
    )
    data = get_json(f"{EUTILS}/esearch.fcgi?{q}")
    parsed = parse_esearch(data)
    parsed["term"] = term
    parsed["retmax"] = retmax
    return parsed


def esearch_ids(term: str, retmax: int = 40) -> list[str]:
    return esearch_page(term, retstart=0, retmax=retmax)["ids"]


def efetch(pmids: Iterable[str], batch_size: int = 50) -> list[Record]:
    ids = [p for p in pmids if p]
    if not ids:
        return []
    out: list[Record] = []
    for i in range(0, len(ids), batch_size):
        chunk = ids[i : i + batch_size]
        q = encode_query({"db": "pubmed", "retmode": "xml", "id": ",".join(chunk)})
        xml_bytes = get_bytes(f"{EUTILS}/efetch.fcgi?{q}")
        out.extend(parse_pubmed_xml(xml_bytes))
        if i + batch_size < len(ids):
            sleep_polite(0.4)
    return out


def fetch_pubmed(term: str = DEFAULT_TERM, retmax: int = 40, retstart: int = 0) -> list[Record]:
    page = esearch_page(term, retstart=retstart, retmax=retmax)
    sleep_polite(0.4)
    return efetch(page["ids"])


def fetch_pubmed_page(term: str = DEFAULT_TERM, retstart: int = 0, retmax: int = 200) -> dict:
    """One cursor page: records plus NCBI's total so a backfill can walk the corpus."""
    page = esearch_page(term, retstart=retstart, retmax=retmax)
    sleep_polite(0.4)
    records = efetch(page["ids"])
    next_start = retstart + len(page["ids"])
    exhausted = (not page["ids"]) or next_start >= page["count"]
    return {
        "records": records,
        "ids": page["ids"],
        "count": page["count"],
        "retstart": retstart,
        "next_start": next_start,
        "exhausted": exhausted,
    }
