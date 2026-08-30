from pathlib import Path

from pcos_litwatch.pubmed import parse_pubmed_xml
from pcos_litwatch.record import Record, content_hash

FIXTURE = Path(__file__).parent / "fixtures" / "pubmed_sample.xml"


def test_parse_pubmed_sample():
    recs = parse_pubmed_xml(FIXTURE.read_bytes())
    assert len(recs) == 2
    by_id = {r.external_id: r for r in recs}
    g = by_id["37580314"]
    assert g.source_type == "guideline"
    assert "polycystic ovary" in g.title.lower()
    assert g.doi
    assert g.url.endswith("/37580314/")
    r = by_id["38637590"]
    assert r.source_type == "review"
    assert r.abstract and "PCOS" in r.abstract


def test_content_hash_stable():
    rec = Record(
        source_type="pubmed",
        external_id="1",
        title="Hello",
        url="https://example.com/1",
        abstract="Abs",
        published_on="2024-01-01",
    )
    assert rec.hash() == content_hash(["pubmed", "1", "Hello", "Abs", "2024-01-01"])
    assert rec.hash() == rec.hash()
