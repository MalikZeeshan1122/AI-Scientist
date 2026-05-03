import httpx
import pytest

from ai_scientist.sources import ArxivSource
from ai_scientist.sources.arxiv import _build_query, _parse_feed, _strip_version

ARXIV_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v2</id>
    <updated>2024-01-15T00:00:00Z</updated>
    <published>2024-01-15T00:00:00Z</published>
    <title>A Test Paper About Foo</title>
    <summary>This paper studies foo extensively.</summary>
    <author><name>Alice Researcher</name></author>
    <author><name>Bob Scientist</name></author>
    <link href="http://arxiv.org/abs/2401.12345v2" rel="alternate" type="text/html"/>
    <link href="http://arxiv.org/pdf/2401.12345v2" rel="related" type="application/pdf"/>
    <arxiv:doi>10.1234/foo.bar</arxiv:doi>
    <arxiv:journal_ref>Journal of Foo, vol. 1, 2024</arxiv:journal_ref>
    <arxiv:comment>12 pages, 5 figures</arxiv:comment>
    <arxiv:primary_category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="stat.ML" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>"""

ERROR_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format_for_1234.12345</id>
    <title>Error</title>
    <summary>incorrect id format for 1234.12345</summary>
    <updated>2007-10-12T00:00:00-04:00</updated>
    <link href="http://arxiv.org/api/errors" rel="alternate"/>
  </entry>
</feed>"""


@pytest.mark.asyncio
async def test_arxiv_search_parses(monkeypatch):
    async def fake_get(self, url, *a, **kw):
        return httpx.Response(200, text=ARXIV_FEED, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    src = ArxivSource(rate_limit=False)
    papers = await src.search("foo", limit=5)
    assert len(papers) == 1
    p = papers[0]
    assert p.id == "arxiv:2401.12345"
    assert p.arxiv_id == "2401.12345"
    assert p.title == "A Test Paper About Foo"
    assert "Alice Researcher" in p.authors
    assert p.pdf_url and "pdf" in str(p.pdf_url)
    assert p.doi == "10.1234/foo.bar"
    assert p.venue == "Journal of Foo, vol. 1, 2024"
    assert p.journal_ref == "Journal of Foo, vol. 1, 2024"
    assert p.comment == "12 pages, 5 figures"
    assert p.primary_category == "cs.LG"
    # All <category> + the primary category, deduped, primary first.
    assert p.categories == ["cs.LG", "cs.AI", "stat.ML"]


@pytest.mark.asyncio
async def test_arxiv_search_passes_categories(monkeypatch):
    captured: dict[str, str] = {}

    async def fake_get(self, url, *a, **kw):
        captured["url"] = url
        return httpx.Response(200, text=ARXIV_FEED, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    src = ArxivSource(rate_limit=False)
    await src.search("foo", limit=3, categories=["cs.LG", "stat.ML"])
    # cat: clauses must be present and OR-ed
    assert "cat%3Acs.LG" in captured["url"]
    assert "cat%3Astat.ML" in captured["url"]
    assert "OR" in captured["url"]


def test_build_query_with_and_without_categories():
    assert _build_query("gnn", []) == "all:gnn"
    q = _build_query("gnn", ["cs.LG", "stat.ML"])
    assert q == "(all:gnn) AND (cat:cs.LG OR cat:stat.ML)"
    # Falsy / blank entries are ignored.
    assert _build_query("gnn", [" ", ""]) == "all:gnn"


def test_strip_version():
    assert _strip_version("2401.12345v2") == "2401.12345"
    assert _strip_version("2401.12345") == "2401.12345"
    # Old-style ids contain 'v' in the category; only the trailing v\d+ is the version.
    assert _strip_version("cond-mat/0207270v1") == "cond-mat/0207270"
    assert _strip_version("cond-mat/0207270") == "cond-mat/0207270"


def test_parse_feed_treats_error_entry_as_empty():
    assert _parse_feed(ERROR_FEED) == []


def test_parse_feed_falls_back_to_arxiv_when_no_journal_ref():
    feed_without_jr = ARXIV_FEED.replace(
        "<arxiv:journal_ref>Journal of Foo, vol. 1, 2024</arxiv:journal_ref>", ""
    )
    papers = _parse_feed(feed_without_jr)
    assert len(papers) == 1
    assert papers[0].venue == "arXiv"
