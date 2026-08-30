from pcos_litwatch.trials import parse_studies


def test_parse_studies_minimal():
    payload = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT01234567",
                        "briefTitle": "Letrozole vs clomiphene in PCOS",
                    },
                    "descriptionModule": {"briefSummary": "A trial."},
                    "statusModule": {
                        "overallStatus": "RECRUITING",
                        "startDateStruct": {"date": "2025-03"},
                    },
                    "conditionsModule": {"conditions": ["Polycystic Ovary Syndrome"]},
                }
            }
        ]
    }
    recs = parse_studies(payload)
    assert len(recs) == 1
    r = recs[0]
    assert r.source_type == "trial"
    assert r.external_id == "NCT01234567"
    assert r.url.endswith("/NCT01234567")
    assert r.published_on == "2025-03-01"
