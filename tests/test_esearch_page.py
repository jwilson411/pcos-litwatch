from pcos_litwatch.pubmed import parse_esearch


def test_parse_esearch_page():
    data = {
        "esearchresult": {
            "count": "21685",
            "retmax": "3",
            "retstart": "200",
            "idlist": ["42365862", "42367168", "42176250"],
        }
    }
    parsed = parse_esearch(data)
    assert parsed["count"] == 21685
    assert parsed["retstart"] == 200
    assert parsed["ids"] == ["42365862", "42367168", "42176250"]


def test_parse_esearch_empty():
    parsed = parse_esearch({"esearchresult": {}})
    assert parsed["ids"] == []
    assert parsed["count"] == 0
