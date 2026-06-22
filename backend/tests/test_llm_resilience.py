"""LLM resilience tests: retry/timeout behavior + graceful 503 on the request path."""
import httpx
import pytest
from openai import APITimeoutError

from config import get_settings
from services import llm
from services.llm import LLMUnavailable
from tests.conftest import seed_session, seed_user


def test_chat_retries_then_raises_unavailable(monkeypatch):
    calls = {"n": 0}

    class _Boom:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    calls["n"] += 1
                    raise APITimeoutError(request=httpx.Request("POST", "http://llm/v1"))

    monkeypatch.setattr(llm, "_client", lambda timeout=None: _Boom)
    monkeypatch.setattr(llm.time, "sleep", lambda *_: None)  # no real backoff in tests

    with pytest.raises(LLMUnavailable):
        llm._chat([{"role": "user", "content": "hi"}], timeout=1)
    assert calls["n"] == get_settings().llm_max_attempts  # retried, didn't give up early


def test_instant_ideas_returns_503_when_llm_unavailable(client, db, mocks):
    uid = seed_user(db, email="ai@example.com")
    token = seed_session(db, uid)
    mocks.generate_meal_ideas.side_effect = LLMUnavailable("endpoint down")
    r = client.post("/api/chef/instant-ideas", headers={"Cookie": f"session_token={token}"})
    assert r.status_code == 503
    assert "busy" in r.json()["detail"].lower()


def test_cook_returns_503_when_llm_unavailable(client, db, mocks):
    uid = seed_user(db, email="cook@example.com")
    token = seed_session(db, uid)
    mocks.extract_recipe.side_effect = LLMUnavailable("endpoint down")
    r = client.post(
        "/api/chef/cook",
        json={"url": "https://example.com/r", "title": "T"},
        headers={"Cookie": f"session_token={token}"},
    )
    assert r.status_code == 503
