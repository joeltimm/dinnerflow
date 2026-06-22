# Iron Skillet — Feature Audit & Development Roadmap

_Audit date: 2026-06-22. Reflects `main` at commit `334d779`._

This document inventories what's built, identifies gaps between the documented
intent and the actual code, and proposes a prioritized path for the next stage.

---

## 1. Current state — what's solid

The app is **feature-complete for its core loop** and surprisingly mature on ops:

| Area | Status |
| :--- | :--- |
| Auth (email/password, bcrypt, 30-day session cookies) | ✅ Solid |
| Cookbook CRUD + ratings + favorites + image upload + cook history | ✅ Solid |
| AI recipe import (scrape → LLM extract → save) | ✅ Solid |
| Instant Chef (LLM ideas + web search) | ✅ Solid |
| Tonight smart-pick + cook logging | ✅ Solid |
| Weekly meal-plan email (per-user delivery days, async "Add to Recipes") | ✅ Solid |
| Todoist sync (v4 client, encrypted tokens) | ✅ Solid |
| Onboarding / first-run UX / empty states | ✅ Solid |
| GDPR/CAN-SPAM (consent, unsubscribe, export, deletion, retention cron) | ✅ Solid |
| Ops (backups+rotation, health endpoint, log rotation, disk/DB monitoring) | ✅ Solid |
| CI (dep-install + syntax check + frontend build) | ✅ Present |
| Claude review/security/checklist bots on Forgejo | ✅ Present |

This is a credible portfolio artifact. The gaps below are about **closing the
distance between "works for the owner" and "production-grade / demonstrably
robust"** — which is exactly the story worth telling for a RevOps/systems portfolio.

---

## 2. Gap analysis

### 🔴 P0 — Risk / correctness (do first)

1. **Zero automated tests.** Confirmed: no `backend/tests/`, no `conftest.py`,
   no frontend tests. CI only byte-compiles Python and runs `vite build`. The
   highest-risk paths are completely uncovered:
   - HMAC-signed email action tokens (`auth/tokens.py`) — a signing/expiry bug
     silently breaks every "Add to My Recipes" link or, worse, lets a forged
     token import to the wrong account.
   - GDPR cascade deletion (`routers/account.py`) — a missed table = a
     compliance failure and orphaned data.
   - Async `scrape_and_save_recipe` Celery task — failure modes are invisible
     (the click already returned "success").
   - Auth (session creation/expiry, rate limits).
   This is tracked as "issue #1" but the reference still says **GitHub
   `joeltimm/dinnerflow`** — the project now lives on **Forgejo**. The issue
   pointer is stale (see P2-6).

2. **LLM is a hard single point of failure with a 20-minute timeout.**
   `llm_timeout: 1200`. Instant Chef's `/api/chef/instant-ideas` is synchronous —
   if the local llama.cpp endpoint is slow or down, the request hangs up to 20
   min then fails with no graceful degradation. No retry, no fallback model, no
   circuit breaker, no user-facing "AI is busy" state.

### 🟠 P1 — Unrealized / incomplete features

3. **pgvector is installed but completely unused.** The extension is enabled and
   `recipes.embedding vector(1536)` exists in the schema — but **no code ever
   writes or queries an embedding** (grep: zero hits). This is dead
   infrastructure today and the single biggest unrealized feature:
   - Semantic recipe search ("something with chickpeas and lemon").
   - **Duplicate detection on import** — right now nothing stops the same
     recipe being saved twice from different URLs.
   - "More like this" recommendations feeding Tonight / Instant Chef.

4. **Shopping list is an island.** It's a manual checklist, disconnected from
   recipes. Ingredients sync to *Todoist* on cook, but there's no "add this
   recipe's ingredients to my shopping list" — the most obvious feature a meal
   planner should have. The data (ingredients as jsonb) is right there.

5. **Single hardcoded timezone.** Meal-plan emails fire at `10:30 America/Chicago`
   for everyone. `email_days` is per-user but the time/TZ is not. Fine for a
   single owner; a gap the moment a second user in another zone signs up.

### 🟡 P2 — Tech debt / hygiene

6. **Legacy Gmail-API cruft throughout.** Superseded by the SMTP relay but still
   present: `backend/scripts/generate_gmail_token.py`, the four `google-auth*`
   packages in `requirements.txt`, and `google_auth_path` / `sender_email` in
   `config.py`. Dead code that bloats the image and confuses new readers.

7. **Naming schism: dinnerflow vs. Iron Skillet.** DB name `dinnerflow`,
   `dinnerflow_schema.sql`, volume `dinnerflow_postgres_data`, README dual title,
   vs. `ironskillet_*` containers. Decide on one brand and make the
   user-facing/docs layer consistent (the DB/volume can stay for migration
   safety, but should be documented as "legacy internal name").

8. **Doc drift.** AGENTS.md describes TypeScript interfaces; the frontend is
   plain `.jsx`. AGENTS.md/CI reference a GitHub issue tracker the project left.
   Small, but these are the first things a reviewer notices.

9. **No app-level observability.** Only `/health` + logs. No error aggregation
   (a `.sentry-native` dir exists in `$HOME` but nothing is wired into this app),
   no metrics on LLM latency / scrape success rate / email delivery — the things
   most likely to fail silently.

### ⚪ P3 — Polish

10. Frontend has an `ErrorBoundary` but no test coverage and no client-side
    error reporting. No accessibility pass. No PWA/offline (relevant for a
    "what's for dinner" phone-in-kitchen use case).
11. Abuse surface: registration + AI endpoints are rate-limited via slowapi, but
    consider per-account email-send caps to prevent the relay being used as an
    open spam vector.

---

## 3. Proposed roadmap

Sequenced so each phase leaves the app shippable and tells a coherent story.

### Phase 1 — "Make it trustworthy" (foundation)
- [ ] Stand up `backend/tests/` + `conftest.py` (db fixture, test client, mocked
      LLM/email/Todoist). Add `pytest`, `ruff`, `mypy` steps to `ci.yml`.
- [ ] Cover the P0 paths first: token sign/verify/expiry, GDPR cascade deletion,
      async scrape task, auth/session lifecycle.
- [ ] Wrap LLM calls with timeout-per-call + retry + a graceful "AI unavailable"
      response; drop the 1200s synchronous ceiling on `instant-ideas`.
- [ ] Fix the stale issue-tracker reference (point at Forgejo).

### Phase 2 — "Make pgvector earn its place" (flagship feature)
- [ ] Generate + store recipe embeddings on save (backfill existing rows).
- [ ] Semantic search endpoint + UI in Cookbook.
- [ ] Duplicate detection on import (cosine-similarity threshold → "you may
      already have this").
- [ ] Optional: "more like this" wired into Tonight / Instant Chef.

### Phase 3 — "Close the product loop"
- [ ] "Add ingredients to shopping list" from any recipe / the meal-plan email.
- [ ] Per-user delivery time + timezone for meal-plan emails.
- [ ] Frontend tests (Vitest) on the critical components.

### Phase 4 — "Operability & polish"
- [ ] Remove legacy Gmail-API code, deps, and config.
- [ ] Resolve the dinnerflow/Iron Skillet naming; align docs.
- [ ] Wire error reporting (Sentry) + basic metrics (LLM latency, scrape success,
      email delivery rate) into `/health` or a `/metrics` endpoint.
- [ ] Accessibility + PWA pass.

---

## 4. Quick wins (< 1 hour each, high signal)

- Delete the Gmail-API cruft (P2-6) — pure subtraction, smaller image, clearer code.
- Fix the GitHub→Forgejo issue reference in AGENTS.md and `ci.yml` comment.
- Add a duplicate-URL guard on recipe import (cheap stopgap before full
  embedding-based dedup).
- Correct AGENTS.md's "TypeScript interfaces" claim to match the JSX reality.
</content>
</invoke>
