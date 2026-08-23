"""Search abstraction layer (V5).

Provider-agnostic web search as required by docs/tech-stack.md. The agent
can swap providers via the SEARCH_PROVIDER env var without any caller
changes.

Implemented: DuckDuckGo (no API key required).
Future: Tavily, Brave, SerpAPI, Google CSE — each becomes a subclass plus
one branch in get_search_provider().
"""
import asyncio
import html
import os
import re
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

import httpx

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)

# DDG serves ad rows through these redirect hosts; they are not real results.
_AD_MARKERS = ("duckduckgo.com/y.js", "ad_provider=", "ad_domain=")

_RESULT_RE = re.compile(
    r'result__a[^>]*href="(?P<url>.*?)".*?>(?P<title>.*?)</a>'
    r'.*?result__snippet[^>]*>(?P<snippet>.*?)</a>',
    re.S,
)


@dataclass
class SearchResult:
    """One web search hit.

    `snippet` is the provider's own excerpt. It is used only as input for
    LLM summarisation and is never persisted — see docs/architecture.md
    "Question Sourcing & Copyright".
    """

    url: str
    title: str
    snippet: str

    @property
    def domain(self) -> str:
        return urllib.parse.urlparse(self.url).netloc.removeprefix("www.")


class SearchProvider(ABC):
    """Abstract base for web search providers."""

    @abstractmethod
    async def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        """Return up to `limit` results for the query."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier for tracing."""


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo via its no-JS HTML endpoint. No API key needed."""

    ENDPOINT = "https://html.duckduckgo.com/html/"

    @property
    def name(self) -> str:
        return "duckduckgo"

    @staticmethod
    def _clean_text(raw: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(raw))).strip()

    @staticmethod
    def _resolve_url(raw: str) -> str:
        """Unwrap DDG's /l/?uddg=<encoded> redirect wrapper."""
        url = html.unescape(raw)
        if url.startswith("//"):
            url = f"https:{url}"
        if "duckduckgo.com/l/" in url:
            target = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("uddg")
            if target:
                return target[0]
        return url

    async def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        # ponytail: single short retry — DDG answers 202 + captcha page when
        # rate-limited; if a second attempt also gets 202 we surface an error
        # instead of silently returning zero results.
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(
                self.ENDPOINT, params={"q": query}, headers={"User-Agent": _BROWSER_UA}
            )
            if resp.status_code == 202:
                await asyncio.sleep(3)
                resp = await client.get(
                    self.ENDPOINT, params={"q": query}, headers={"User-Agent": _BROWSER_UA}
                )
            resp.raise_for_status()
            body = resp.text

        if "result__a" not in body:
            raise RuntimeError(
                "DuckDuckGo returned no results (likely rate-limited or bot-checked)"
            )

        results: list[SearchResult] = []
        for match in _RESULT_RE.finditer(body):
            url = self._resolve_url(match.group("url"))
            if any(marker in url for marker in _AD_MARKERS):
                continue
            results.append(
                SearchResult(
                    url=url,
                    title=self._clean_text(match.group("title")),
                    snippet=self._clean_text(match.group("snippet")),
                )
            )
            if len(results) >= limit:
                break
        return results


@lru_cache
def get_search_provider() -> SearchProvider:
    """Return the configured search provider (default: DuckDuckGo)."""
    name = os.getenv("SEARCH_PROVIDER", "duckduckgo").lower()
    if name == "duckduckgo":
        return DuckDuckGoProvider()
    raise ValueError(f"Unknown search provider: {name}")
