import httpx
import pytest

from ai_scientist.sources import TavilySource

TAVILY_RESPONSE = {
    "query": "sparse mixture-of-experts inference",
    "results": [
        {
            "title": "Sparse MoE Inference Tricks",
            "url": "https://example.com/post-1",
            "content": "An overview of routing strategies for sparse MoE.",
            "score": 0.92,
            "published_date": "2024-06-12",
        },
        {
            "title": "Speeding up Switch Transformers",
            "url": "https://example.com/post-2",
            "content": "Benchmarks of capacity-factor tuning at inference time.",
            "score": 0.87,
            "published_date": None,
        },
        {
            # Should be skipped — no URL means we cannot key it
            "title": "Bogus result",
            "url": "",
            "content": "no url",
        },
    ],
}


@pytest.mark.asyncio
async def test_tavily_search_parses(monkeypatch):
    seen: dict = {}

    async def fake_post(self, url, *a, **kw):
        seen["url"] = url
        seen["json"] = kw.get("json")
        return httpx.Response(
            200, json=TAVILY_RESPONSE, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    src = TavilySource(api_key="tvly-test-key", search_depth="basic")
    papers = await src.search("sparse mixture-of-experts inference", limit=5)

    assert seen["url"] == "https://api.tavily.com/search"
    assert seen["json"]["api_key"] == "tvly-test-key"
    assert seen["json"]["query"] == "sparse mixture-of-experts inference"
    assert seen["json"]["max_results"] == 5

    assert len(papers) == 2
    p = papers[0]
    assert p.source == "tavily"
    assert p.id.startswith("tavily:")
    assert p.title == "Sparse MoE Inference Tricks"
    assert "routing strategies" in p.abstract
    assert str(p.url) == "https://example.com/post-1"
    assert p.published is not None and p.published.year == 2024


@pytest.mark.asyncio
async def test_tavily_returns_empty_when_no_api_key():
    src = TavilySource(api_key=None)
    assert await src.search("anything") == []


@pytest.mark.asyncio
async def test_tavily_advanced_depth_and_answer(monkeypatch):
    captured: dict = {}

    async def fake_post(self, url, *a, **kw):
        captured["json"] = kw.get("json")
        return httpx.Response(
            200,
            json={
                "answer": "MoE inference can be sped up by selective expert activation.",
                "results": TAVILY_RESPONSE["results"],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    src = TavilySource(api_key="tvly-test", search_depth="advanced", include_answer="advanced")
    papers = await src.search("moe inference", limit=5)

    assert captured["json"]["search_depth"] == "advanced"
    assert captured["json"]["include_answer"] == "advanced"
    assert len(papers) == 2
    assert src.last_answer is not None
    assert "selective expert activation" in src.last_answer


@pytest.mark.asyncio
async def test_tavily_passes_domain_filters(monkeypatch):
    captured: dict = {}

    async def fake_post(self, url, *a, **kw):
        captured["json"] = kw.get("json")
        return httpx.Response(
            200, json={"results": []}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    src = TavilySource(
        api_key="tvly-test-key",
        include_domains=["arxiv.org"],
        exclude_domains=["spam.example"],
    )
    await src.search("foo", limit=3)

    assert captured["json"]["include_domains"] == ["arxiv.org"]
    assert captured["json"]["exclude_domains"] == ["spam.example"]
