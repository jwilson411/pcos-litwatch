from pcos_litwatch.arxiv_src import parse_atom

ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <title>A toy PCOS model</title>
    <published>2024-01-02T00:00:00Z</published>
    <summary>Abstract here.</summary>
    <author><name>Ada Lovelace</name></author>
  </entry>
</feed>
"""


def test_parse_atom():
    recs = parse_atom(ATOM)
    assert len(recs) == 1
    r = recs[0]
    assert r.source_type == "preprint"
    assert r.external_id == "2401.00001v1"
    assert r.url == "https://arxiv.org/abs/2401.00001v1"
    assert r.published_on == "2024-01-02"
    assert r.authors == "Ada Lovelace"
