from typing import Any

from core.config import get_settings


def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    from ddgs import DDGS

    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })
    return results


def _search_tavily(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    import httpx

    api_key = get_settings().secret_value("tavily_api_key")
    if not api_key:
        return []

    resp = httpx.post(
        "https://api.tavily.com/search",
        json={"api_key": api_key, "query": query, "max_results": max_results},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
        }
        for r in data.get("results", [])
    ]


def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web. Uses Tavily if TAVILY_API_KEY is set, else DuckDuckGo."""
    if get_settings().tavily_api_key:
        try:
            results = _search_tavily(query, max_results=max_results)
            if results:
                return results
        except Exception:
            pass

    try:
        return _search_duckduckgo(query, max_results=max_results)
    except Exception:
        return []


def format_search_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No web results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', 'Untitled')}")
        lines.append(f"    URL: {r.get('url', '')}")
        lines.append(f"    {r.get('snippet', '')}")
    return "\n".join(lines)


def search_for_startup(extracted: dict, max_results_per_query: int = 4) -> tuple[str, list[dict[str, Any]]]:
    """Run multiple queries and return combined text + deduplicated sources."""
    solution = extracted.get("solution", "")
    if isinstance(solution, list):
        solution = " ".join(str(s) for s in solution)
    business = extracted.get("business_model", "")
    if isinstance(business, list):
        business = " ".join(str(b) for b in business)
    target = extracted.get("target_customer", "")
    if isinstance(target, list):
        target = " ".join(str(t) for t in target)

    topic = " ".join(filter(None, [str(solution)[:120], str(business)[:80], str(target)[:60]])).strip()
    if not topic:
        topic = "technology startup"

    queries = [
        f"{topic} market size TAM 2025",
        f"{topic} competitors startups",
        f"{topic} industry growth rate trends",
    ]

    all_sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    combined_blocks: list[str] = []

    for q in queries:
        results = web_search(q, max_results=max_results_per_query)
        combined_blocks.append(f"Query: {q}\n{format_search_results(results)}")
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_sources.append({**r, "query": q})

    return "\n\n".join(combined_blocks), all_sources
