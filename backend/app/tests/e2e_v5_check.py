"""V5 end-to-end check: curation pipeline with a stub search provider.

Runs the REAL pipeline (rank → LLM summarize → original questions) against a
stub SearchProvider so it doesn't depend on DDG availability. Verifies the
copyright rule: no provider snippet text is ever persisted.

Run inside the backend container:
    python app/tests/e2e_v5_check.py
"""
import asyncio

from app.services.resources import (
    SearchResult,
    curate_resources_for_topics,
    source_tier,
)


class StubProvider:
    """Returns fixed hits shaped exactly like real DDG output."""

    name = "stub"

    SNIPPET = "SENTINEL-SNIPPET-TEXT that must never be persisted anywhere"

    HITS = [
        SearchResult(
            url="https://www.ieltsliz.com/subject-verb-agreement-practice/",
            title="Subject-Verb Agreement Practice for IELTS Writing",
            snippet=SNIPPET,
        ),
        SearchResult(
            url="https://www.ets.org/toefl/revised-prep/grammar-agreement",
            title="TOEFL Grammar: Agreement Rules - ETS Official Guide",
            snippet=SNIPPET,
        ),
        SearchResult(
            url="https://random-forum.example.net/thread/9912",
            title="Some forum thread about grammar",
            snippet=SNIPPET,
        ),
    ]

    async def search(self, query: str, limit: int = 8):
        return self.HITS[:limit]


async def main() -> None:
    topics = ["Academic Style", "Subject-Verb Agreement"]

    curated = await curate_resources_for_topics(topics, per_topic=3, provider=StubProvider())
    print(f"[e2e] curated {len(curated)} resources for {len(topics)} topics")

    assert curated, "expected resources from stub provider"
    assert all("SENTINEL" not in str(r) for r in curated), (
        "COPYRIGHT VIOLATION: provider snippet leaked into persisted data"
    )

    tiers = sorted({source_tier(r["source_domain"]) for r in curated})
    assert "official" in tiers or "educational" in tiers, "reputable sources not ranked"

    reputable = [r for r in curated if r["is_reputable"]]
    assert reputable, "no reputable resources flagged"
    assert reputable[0]["source_domain"].endswith(("ieltsliz.com", "ets.org"))

    with_summary = [r for r in curated if r["summary"]]
    print(f"[e2e] reputable={len(reputable)}  llm_summarized={len(with_summary)}")
    for r in curated:
        q = r["practice_questions"]
        assert all(isinstance(x, str) and len(x) < 500 for x in q)
        if q:
            print(f"[e2e] original questions for {r['topic']!r}: {q}")

    # Dedup across topics
    urls = [r["url"] for r in curated]
    assert len(urls) == len(set(urls)), "duplicate URLs across topics"

    print("[e2e] ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
