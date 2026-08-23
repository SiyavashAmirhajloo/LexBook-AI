"""Resource curation for V5 Internet Intelligence.

Takes topics extracted by a V3 study session, searches the web, ranks
reputable sources first, then rewrites each hit into an *original*
summary and generates *original* practice questions.

COPYRIGHT (docs/architecture.md, non-negotiable):
- Only links + original AI-written summaries are persisted.
- Provider snippets are used transiently as summarisation input and are
  never stored or returned to the client.
- Practice questions are generated from the topic, never copied from a
  source page.
"""
import json
import os
import re

import httpx

from app.services.search import SearchProvider, SearchResult, get_search_provider

# Official + educational domains from docs/architecture.md. Ranked first.
REPUTABLE_DOMAINS = {
    # Official test makers
    "ets.org": "official",
    "britishcouncil.org": "official",
    "takeielts.britishcouncil.org": "official",
    "ielts.org": "official",
    "idp.com": "official",
    "ieltsidp.com": "official",
    # Educational providers
    "magoosh.com": "educational",
    "testglider.com": "educational",
    "bestmytest.com": "educational",
    "ieltsliz.com": "educational",
    "e2language.com": "educational",
    # Secondary
    "youtube.com": "secondary",
    "reddit.com": "secondary",
}

# Query suffix per skill so search hits match the intended practice type.
SKILL_QUERIES = {
    "reading": "IELTS reading practice passage",
    "listening": "IELTS listening practice",
    "writing": "IELTS writing task practice",
    "speaking": "IELTS speaking questions practice",
    "grammar": "IELTS grammar explanation exercises",
    "vocabulary": "IELTS academic vocabulary practice",
}

_TYPE_KEYWORDS = {
    "reading": ("reading", "passage", "comprehension"),
    "listening": ("listening", "audio", "podcast"),
    "writing": ("writing", "essay", "task 1", "task 2"),
    "speaking": ("speaking", "part 1", "part 2", "interview"),
    "grammar": ("grammar", "clause", "tense", "voice", "conditional"),
    "vocabulary": ("vocabulary", "word", "collocation", "lexis"),
}


def classify_resource_type(title: str, url: str) -> str:
    """Infer which IELTS/TOEFL skill a resource targets."""
    haystack = f"{title} {url}".lower()
    for resource_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            return resource_type
    return "general"


def source_tier(domain: str) -> str:
    """Return official | educational | secondary | other for a domain."""
    for known, tier in REPUTABLE_DOMAINS.items():
        if domain == known or domain.endswith(f".{known}"):
            return tier
    return "other"


def build_queries(topics: list[str]) -> list[tuple[str, str]]:
    """Build (topic, query) pairs biased toward IELTS/TOEFL practice material."""
    queries: list[tuple[str, str]] = []
    for topic in topics:
        skill = next(
            (s for s in SKILL_QUERIES if s in topic.lower()),
            None,
        )
        suffix = SKILL_QUERIES.get(skill, "IELTS TOEFL practice exercises explanation")
        queries.append((topic, f"{topic} {suffix}"))
    return queries


def rank_results(results: list[SearchResult]) -> list[SearchResult]:
    """Sort so official sources come first, then educational, then the rest."""
    tier_order = {"official": 0, "educational": 1, "secondary": 2, "other": 3}
    return sorted(results, key=lambda r: tier_order[source_tier(r.domain)])


CURATION_PROMPT = """You are an IELTS/TOEFL tutor curating study resources.

For EACH numbered resource below, write an ORIGINAL description in your own \
words explaining what a student would gain from it. Do NOT copy or paraphrase \
the provided excerpt sentence-by-sentence — the excerpt is only a hint about \
the page's subject.

Then write 2 ORIGINAL practice questions about the TOPIC itself (not about the \
resource). Invent them from scratch; never reproduce questions from any source.

Topic: {topic}

Resources:
{resource_list}

Return ONLY valid JSON, no markdown fences:
{{
  "resources": [
    {{"index": 1, "summary": "<1-2 sentences, your own words>"}}
  ],
  "practice_questions": ["<original question 1>", "<original question 2>"]
}}
"""


async def curate_with_llm(topic: str, results: list[SearchResult]) -> dict:
    """Rewrite search hits into original summaries + generate original questions.

    Returns {"summaries": {index: str}, "practice_questions": [str]}.
    Falls back to empty summaries (links only) if no LLM is configured or the
    call fails — links alone are always copyright-safe.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not results:
        return {"summaries": {}, "practice_questions": []}

    resource_list = "\n".join(
        f"{i}. {r.title} ({r.domain})\n   excerpt hint: {r.snippet[:200]}"
        for i, r in enumerate(results, start=1)
    )
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    prompt = CURATION_PROMPT.format(topic=topic, resource_list=resource_list)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url, json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            )
            resp.raise_for_status()
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        parsed = json.loads(raw)
        summaries = {
            int(item["index"]): item.get("summary", "")
            for item in parsed.get("resources", [])
            if "index" in item
        }
        return {
            "summaries": summaries,
            "practice_questions": parsed.get("practice_questions", []),
        }
    except Exception:
        return {"summaries": {}, "practice_questions": []}


async def curate_resources_for_topics(
    topics: list[str], per_topic: int = 4, provider: SearchProvider | None = None
) -> list[dict]:
    """Search + rank + summarise resources for each topic.

    Returns dicts ready for StudyResource persistence. Provider snippets are
    deliberately absent from the output.
    """
    provider = provider or get_search_provider()
    curated: list[dict] = []
    seen_urls: set[str] = set()

    errors: list[str] = []
    for topic, query in build_queries(topics):
        try:
            hits = await provider.search(query, limit=per_topic * 2)
        except Exception as exc:
            # Surface search failures instead of silently returning nothing.
            print(f"[internet] search failed for {topic!r}: {exc}")
            errors.append(topic)
            continue

        ranked = [r for r in rank_results(hits) if r.url not in seen_urls][:per_topic]
        if not ranked:
            continue
        seen_urls.update(r.url for r in ranked)

        curation = await curate_with_llm(topic, ranked)
        questions = curation["practice_questions"]

        for i, hit in enumerate(ranked, start=1):
            tier = source_tier(hit.domain)
            curated.append(
                {
                    "topic": topic,
                    "url": hit.url,
                    "title": hit.title,
                    "source_domain": hit.domain,
                    "summary": curation["summaries"].get(i) or None,
                    "resource_type": classify_resource_type(hit.title, hit.url),
                    "is_reputable": tier in ("official", "educational"),
                    # Questions belong to the topic; attach to the first result only.
                    "practice_questions": questions if i == 1 else [],
                }
            )

    if not curated and errors:
        # Every topic failed — tell the caller why instead of an empty success.
        raise RuntimeError(
            f"Web search failed for all topics (rate-limited by provider): {errors}"
        )
    return curated
