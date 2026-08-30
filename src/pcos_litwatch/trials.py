"""ClinicalTrials.gov v2 search. No auth."""

from __future__ import annotations

from .http import encode_query, get_json
from .record import Record

BASE = "https://clinicaltrials.gov/api/v2/studies"
QUERY = "polycystic ovary syndrome OR PCOS OR PMOS"


def parse_studies(payload: dict) -> list[Record]:
    out: list[Record] = []
    for study in payload.get("studies") or []:
        proto = (study.get("protocolSection") or {})
        ident = proto.get("identificationModule") or {}
        nct = ident.get("nctId")
        if not nct:
            continue
        title = ident.get("briefTitle") or ident.get("officialTitle") or nct
        brief = ((proto.get("descriptionModule") or {}).get("briefSummary")) or None
        status = (proto.get("statusModule") or {})
        start = (status.get("startDateStruct") or {}).get("date")
        published_on = None
        if start and len(start) >= 7:
            published_on = start[:10] if len(start) >= 10 else f"{start}-01"
        conditions = (proto.get("conditionsModule") or {}).get("conditions") or []
        out.append(
            Record(
                source_type="trial",
                external_id=nct,
                title=title,
                url=f"https://clinicaltrials.gov/study/{nct}",
                abstract=brief,
                published_on=published_on,
                journal="ClinicalTrials.gov",
                raw={"nct": nct, "conditions": conditions, "overallStatus": status.get("overallStatus")},
            )
        )
    return out


def fetch_trials(query: str = QUERY, page_size: int = 20) -> list[Record]:
    q = encode_query(
        {
            "query.term": query,
            "pageSize": str(page_size),
            "sort": "LastUpdatePostDate:desc",
            "fields": "NCTId,BriefTitle,OfficialTitle,BriefSummary,OverallStatus,StartDate,Condition",
        }
    )
    payload = get_json(f"{BASE}?{q}")
    return parse_studies(payload)
