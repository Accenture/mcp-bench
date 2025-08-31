import json

from biomcp.articles.fetch import fetch_articles

pmids = [39293516, 34397683, 37296959]


async def test_fetch_full_text(anyio_backend):
    results = await fetch_articles(pmids, full=True, output_json=True)
    assert isinstance(results, str)
    data = json.loads(results)
    assert len(data) == 3
    for item in data:
        assert item["pmid"] in pmids
        assert len(item["title"]) > 10
        assert len(item["abstract"]) > 100
        assert item["full_text"] is not None


async def test_fetch_abstracts(anyio_backend):
    results = await fetch_articles(pmids, full=False, output_json=True)
    assert isinstance(results, str)
    data = json.loads(results)
    assert len(data) == 3
    for item in data:
        assert item["pmid"] in pmids
        assert len(item["title"]) > 10
        assert len(item["abstract"]) > 100
        assert "full_text" not in item
