"""
LLM service — thin wrapper around the local OpenAI-compatible endpoint.

The local LLM server (e.g. LM Studio / Ollama openai-compat) exposes the
same API as OpenAI, so we use the openai Python client pointed at the
configured LLM_BASE_URL (see config.py / compose.yml).

Main functions:
  extract_recipe(html_text)  → {"ingredients": [...], "instructions": [...]}
  generate_ideas(prefs, favorites, n) → [{"title": ..., "url": ..., "description": ...}]
"""
import json
import logging
import re

from openai import OpenAI

from config import get_settings

logger = logging.getLogger(__name__)


def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        base_url=settings.llm_base_url,
        api_key="not-needed",       # local server doesn't require a real key
        timeout=settings.llm_timeout,
    )


def _chat(messages: list[dict], temperature: float = 0.1, max_tokens: int | None = None) -> str:
    """Send a chat request and return the assistant's reply as a string."""
    settings = get_settings()
    kwargs = dict(model=settings.llm_model, messages=messages, temperature=temperature)
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = _client().chat.completions.create(**kwargs)
    return resp.choices[0].message.content.strip()


def _parse_json_from_reply(text: str) -> dict | list:
    """
    Extract JSON from an LLM reply that may:
    - Wrap it in markdown code fences
    - Append extra commentary after the JSON (causes json.loads "Extra data" error)
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    # Seek to the first JSON container character so any preamble is skipped
    start = next((i for i, c in enumerate(cleaned) if c in "{["), 0)
    cleaned = cleaned[start:]

    # raw_decode stops at the end of the first valid JSON value, ignoring trailing text
    obj, _ = json.JSONDecoder().raw_decode(cleaned)
    return obj


# ── Recipe extraction ──────────────────────────────────────────────────────────

EXTRACT_SYSTEM_PROMPT = (
    "You are a recipe parser. Extract recipe details from the provided text. "
    "Return ONLY raw JSON with exactly two keys: "
    '"ingredients" (array of strings, one ingredient per item including quantity) and '
    '"instructions" (array of strings, one step per item). '
    "No markdown, no extra keys, no explanation."
)


def extract_recipe(cleaned_html: str) -> dict:
    """
    Parse a cleaned recipe page body into structured ingredients + instructions.
    Returns {"ingredients": [...], "instructions": [...]}.
    """
    # Truncate aggressively — ingredients + instructions rarely exceed 5 KB
    # Keeping input small is critical for response speed on a local LLM
    truncated = cleaned_html[:6_000]

    reply = _chat(
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": truncated},
        ],
        temperature=0.1,
        max_tokens=800,
    )

    try:
        data = _parse_json_from_reply(reply)
        # Normalise: remove leading bullets/dashes that some pages include
        data["ingredients"] = [
            re.sub(r"^[-•*]\s*", "", ing).strip()
            for ing in data.get("ingredients", [])
            if ing.strip()
        ]
        data["instructions"] = [
            s.strip() for s in data.get("instructions", []) if s.strip()
        ]
        return data
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to parse LLM recipe response: %s\nRaw: %s", exc, reply)
        raise ValueError(f"LLM returned unparseable JSON: {exc}") from exc


# ── Instant-chef idea generation ──────────────────────────────────────────────

IDEAS_SYSTEM_PROMPT = (
    "You are a creative chef assistant. Given a user's dietary preferences and a list "
    "of their favourite recipes, suggest {n} diverse meal ideas they might enjoy. "
    "Return ONLY a JSON array. Each element must have exactly three keys: "
    '"title" (string), "description" (one-sentence description, string), '
    '"search_query" (a short Tavily search query to find a good recipe for this meal, string). '
    "No markdown, no explanation."
)


def generate_meal_ideas(
    dietary_preferences: str,
    favorites: list[str],
    n: int = 10,
) -> list[dict]:
    """
    Ask the LLM to suggest n meal ideas based on user prefs + favorites.
    Returns list of {"title": ..., "description": ..., "search_query": ...}.
    """
    favs_text = "\n".join(f"- {f}" for f in favorites[:20]) or "(none yet)"
    user_msg = (
        f"Dietary preferences / restrictions: {dietary_preferences or 'none'}\n\n"
        f"Favourite recipes:\n{favs_text}\n\n"
        f"Suggest {n} meal ideas."
    )

    reply = _chat(
        messages=[
            {
                "role": "system",
                "content": IDEAS_SYSTEM_PROMPT.format(n=n),
            },
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,  # higher temp for creative variety
        max_tokens=600,
    )

    try:
        ideas = _parse_json_from_reply(reply)
        # LLM sometimes wraps the array in an object — unwrap it
        if isinstance(ideas, dict):
            ideas = next(v for v in ideas.values() if isinstance(v, list))
        if not isinstance(ideas, list):
            raise ValueError("Expected a JSON array")
        return ideas[:n]
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse LLM ideas response: %s\nRaw: %s", exc, reply)
        raise ValueError(f"LLM returned unparseable ideas: {exc}") from exc
