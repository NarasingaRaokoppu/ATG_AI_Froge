from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.services.research_digest_service import _fallback_query, parse_arxiv_feed
from app.services.research_digest_service import _search_arxiv


def test_parse_arxiv_feed_extracts_core_fields() -> None:
    xml_text = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2501.12345v1</id>
        <updated>2025-01-10T12:00:00Z</updated>
        <published>2025-01-09T09:30:00Z</published>
        <title>  A Test Paper for Research Digest  </title>
        <summary>  First line.\nSecond line.  </summary>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Jones</name></author>
        <arxiv:primary_category term="cs.CL" />
        <link href="http://arxiv.org/abs/2501.12345v1" rel="alternate" type="text/html" />
        <link title="pdf" href="http://arxiv.org/pdf/2501.12345v1" rel="related" type="application/pdf" />
      </entry>
    </feed>
    """

    papers = parse_arxiv_feed(xml_text)

    assert len(papers) == 1
    assert papers[0].arxiv_id == "2501.12345v1"
    assert papers[0].title == "A Test Paper for Research Digest"
    assert papers[0].summary == "First line. Second line."
    assert papers[0].authors == ["Alice Smith", "Bob Jones"]
    assert papers[0].primary_category == "cs.CL"
    assert papers[0].pdf_url == "http://arxiv.org/pdf/2501.12345v1"


def test_fallback_query_preserves_topic_and_missing_angles() -> None:
    query = _fallback_query(
        "retrieval augmented generation for legal research",
        ["enterprise deployments"],
    )

    assert 'all:"retrieval augmented generation for legal research"' in query
    assert 'all:"enterprise deployments"' in query


@pytest.mark.asyncio
async def test_search_arxiv_retries_after_429_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
  xml_text = """<?xml version="1.0" encoding="UTF-8"?>
  <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
    <entry>
    <id>http://arxiv.org/abs/2501.12345v1</id>
    <updated>2025-01-10T12:00:00Z</updated>
    <published>2025-01-09T09:30:00Z</published>
    <title>Retry Success Paper</title>
    <summary>Recovered after retry.</summary>
    <author><name>Alice Smith</name></author>
    </entry>
  </feed>
  """
  calls = {"count": 0}
  sleep_calls: list[float] = []

  class FakeClient:
    async def __aenter__(self) -> "FakeClient":
      return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
      return None

    async def get(self, url: str, params: dict[str, object]):
      calls["count"] += 1
      if calls["count"] == 1:
        request = httpx.Request("GET", url, params=params)
        response = httpx.Response(429, request=request, headers={"Retry-After": "0"})
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)
      return SimpleNamespace(
        text=xml_text,
        raise_for_status=lambda: None,
      )

  async def fake_sleep(seconds: float) -> None:
    sleep_calls.append(seconds)

  monkeypatch.setattr("app.services.research_digest_service.httpx.AsyncClient", lambda **_: FakeClient())
  monkeypatch.setattr("app.services.research_digest_service.asyncio.sleep", fake_sleep)

  papers = await _search_arxiv("all:\"retry test\"", 5)

  assert calls["count"] == 2
  assert sleep_calls == [2.0]
  assert len(papers) == 1
  assert papers[0].title == "Retry Success Paper"


@pytest.mark.asyncio
async def test_search_arxiv_returns_clear_error_after_repeated_429(monkeypatch: pytest.MonkeyPatch) -> None:
  class FakeClient:
    async def __aenter__(self) -> "FakeClient":
      return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
      return None

    async def get(self, url: str, params: dict[str, object]):
      request = httpx.Request("GET", url, params=params)
      response = httpx.Response(429, request=request)
      raise httpx.HTTPStatusError("rate limited", request=request, response=response)

  async def fake_sleep(_: float) -> None:
    return None

  monkeypatch.setattr("app.services.research_digest_service.httpx.AsyncClient", lambda **_: FakeClient())
  monkeypatch.setattr("app.services.research_digest_service.asyncio.sleep", fake_sleep)

  with pytest.raises(HTTPException) as exc_info:
    await _search_arxiv("all:\"retry failure\"", 5)

  assert exc_info.value.status_code == 503
  assert exc_info.value.detail["error"] == "arxiv_rate_limited"
