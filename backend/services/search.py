"""
Web search service for finding recipe URLs.

Strategy (applied in this order):
  1. Tavily  — best quality, AI-focused results, but has a free-tier credit limit.
  2. DuckDuckGo — free, no API key, no credit limits; used automatically when Tavily
                  is unavailable (no key, quota exceeded, any HTTP error).

Both backends return the same shape:
  [{"title": str, "url": str, "description": str}, ...]

Usage:
  from services.search import search_recipes
  results = search_recipes("easy chicken tikka masala recipe", max_results=2)
"""
import logging

logger = logging.getLogger(__name__)


def search_recipes(query: str, max_results: int = 2) -> list[dict]:
    """
    Search for recipe URLs matching `query`.

    Tries Tavily first; falls back to DuckDuckGo automatically on any failure.
    Returns up to `max_results` results as {"title", "url", "description"} dicts.
    """
    from config import get_settings
    settings = get_settings()

    if settings.tavily_api_key:
        try:
            return _tavily_search(settings.tavily_api_key, query, max_results)
        except Exception as exc:
            logger.warning(
                "Tavily search failed ('%s'): %s — falling back to DuckDuckGo",
                query, exc,
            )

    # Tavily unavailable or failed — use DuckDuckGo
    try:
        return _ddg_search(query, max_results)
    except Exception as exc:
        logger.error("DuckDuckGo fallback also failed ('%s'): %s", query, exc)
        return []


# ── Tavily ────────────────────────────────────────────────────────────────────

def _tavily_search(api_key: str, query: str, max_results: int) -> list[dict]:
    from tavily import TavilyClient
    client = TavilyClient(api_key=api_key)
    raw = client.search(query=query, max_results=max_results, search_depth="basic")
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": (r.get("content") or "")[:200],
        }
        for r in raw.get("results", [])
        if r.get("url")
    ]


# ── DuckDuckGo ────────────────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int) -> list[dict]:
    from duckduckgo_search import DDGS
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "description": (r.get("body") or "")[:200],
            })
    return results
