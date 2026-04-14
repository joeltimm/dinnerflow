# Dinnerflow / Iron Skillet

**Self-hosted, AI-powered meal planning.**

FastAPI backend + React frontend + PostgreSQL. AI scraping, recipe extraction, weekly meal plan emails, and Todoist sync — all handled internally by Python, no external automation required.

---

## Services

| Service | Technology | Port | Description |
| :--- | :--- | :--- | :--- |
| **backend** | FastAPI (Python 3.11) | 8010 (debug) | API, scheduler, email, LLM, scraping |
| **web** | React 18 + Vite + nginx | 80 | UI |
| **dinner-db** | PostgreSQL 15 + pgvector | 5436 | Database |

---

## Features

- **Accounts** — Email/password auth, HTTP-only session cookies (30-day), bcrypt hashing
- **Onboarding** — First-run welcome hero on Tonight page, sidebar progress checklist (add recipe, set dietary prefs, log a cook), actionable empty states with starter recipe suggestions throughout the app
- **Cookbook** — Add recipes manually or import directly from a URL (AI scrapes and extracts); edit, delete, upload images; 5-star ratings, favorites, full cook history per recipe. Empty-state includes inline URL import and one-click starter recipes
- **Instant Chef** — Generate 10 AI meal ideas on demand (LLM + Tavily web search); selecting one scrapes and saves the recipe. Works for new users without favourites or dietary preferences
- **Tonight** — Smart pick for what to cook now based on cook history; log it with a rating. New users see a welcome hero with getting-started guidance
- **Shopping List** — Manual grocery list with check-off and clear-checked actions
- **Dashboard** — Most-cooked and highest-rated charts; recipe, cook, and favourite counts. Empty state shows motivational message with CTAs instead of zeros
- **Weekly email plan** — Scheduled Tue/Sat 10:30 AM (opt-in only); also triggerable on demand. Emails a personalized meal plan with one-click "Add to My Recipes" links and an unsubscribe link
- **Settings** — Dietary preferences; Todoist integration (encrypted token, syncs ingredients on cook); email preferences toggle; data export; account deletion
- **Privacy & compliance** — Email opt-in consent at registration, one-click unsubscribe, GDPR data export/deletion, privacy policy page, cookie notice, automated data retention cleanup

---

## Project Structure

```
dinnerflow/
├── compose.yml
├── .env.example
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Env-var settings (pydantic-settings)
│   ├── database.py              # Connection pool
│   ├── dependencies.py          # get_current_user dependency
│   ├── celery_app.py            # Celery broker + beat schedule
│   ├── tasks.py                 # Background tasks (email, meal plans, monitoring)
│   ├── auth/
│   │   ├── router.py            # /api/auth — register, login, logout, me
│   │   └── utils.py             # Password hashing, session tokens, Fernet
│   ├── limiter.py               # Rate limiting (slowapi)
│   ├── routers/
│   │   ├── account.py           # /api/account — data export, deletion, email prefs, unsubscribe (GDPR)
│   │   ├── admin.py             # /api/admin — user management, impersonation, admin deletion
│   │   ├── chef.py              # /api/chef — instant-ideas, cook, email-plan, select-from-email
│   │   ├── dashboard.py         # /api/dashboard + /api/onboarding — stats, charts, first-run checklist
│   │   ├── recipes.py           # /api/recipes — CRUD, ratings, favorites, images, history
│   │   ├── settings.py          # /api/settings — preferences, Todoist config
│   │   ├── shopping.py          # /api/shopping — shopping list CRUD
│   │   └── tonight.py           # /api/tonight — smart pick, cooking log
│   ├── services/
│   │   ├── email.py             # Gmail send (OAuth, mirrors calendar_bot)
│   │   ├── llm.py               # Recipe extraction + meal idea generation
│   │   ├── scheduler.py         # Meal plan builder (called by Celery tasks)
│   │   ├── scraper.py           # URL fetch + HTML cleaning
│   │   ├── search.py            # Tavily (+ DuckDuckGo fallback) recipe search
│   │   └── todoist.py           # Todoist API — sync ingredients as tasks
│   ├── alembic/                 # Database migrations (Alembic)
│   │   ├── env.py
│   │   └── versions/            # Migration scripts (001_baseline, 002_add_indexes, ...)
│   ├── alembic.ini
│   └── scripts/
│       └── generate_gmail_token.py  # One-time Gmail OAuth setup
├── scripts/
│   ├── backup-db.sh             # Automated pg_dump with rotation (7 daily + 4 weekly)
│   └── restore-db.sh            # Interactive database restore from backup
├── web/
│   ├── src/
│   │   ├── api/client.js        # Axios API client (all endpoints)
│   │   ├── context/             # React context providers (Auth, Chef, Onboarding)
│   │   ├── pages/               # Dashboard, Recipes, Chef, Tonight, ShoppingList, Settings, Login, Privacy
│   │   └── components/          # Layout, Sidebar, RecipeCard, StarRating, ProtectedRoute, CookieBanner, etc.
│   └── nginx.conf               # Proxies /api/ and /uploads/ to backend
├── dinnerflow_schema.sql        # DB schema (apply on fresh install)
└── SCHEMA.md                    # Human-readable schema reference
```

---

## Setup

### Prerequisites

- Docker & Docker Compose
- Gmail OAuth token for email (see below)
- Tavily API key for recipe web search

### 1. Generate secret keys

```bash
# Fernet key (encrypts Todoist tokens at rest)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Secret key (signs email action tokens)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Environment variables

```bash
cp .env.example .env
# Fill in all values
```

Required:

```env
DINNER_DB_NAME=dinnerflow
DINNER_DB_USER=dinneruser
DINNER_DB_PASSWORD=changeme

FERNET_KEY=<generated above>
SECRET_KEY=<generated above>

LLM_BASE_URL=http://100.98.99.49:8081/v1
LLM_MODEL=gpt-4o-mini

TAVILY_API_KEY=<your key>

SENDER_EMAIL=you@gmail.com
GOOGLE_AUTH_PATH=/path/to/google_auth   # directory containing token_<suffix>.json

APP_BASE_URL=http://your-domain-or-ip
CORS_ORIGINS=http://your-domain-or-ip
```

### 3. Gmail OAuth (one-time)

The backend reuses an existing Gmail token if you have one (e.g. from `calendar_bot`). To generate a fresh token:

```bash
cd backend
python scripts/generate_gmail_token.py
```

The token file must include the `gmail.send` scope.

### 4. Docker volume

The database uses an external named volume so `docker compose down -v` cannot accidentally destroy recipe data. This volume was originally created by the old n8n stack. If it doesn't exist yet (fresh install):

```bash
docker volume create dinnerflow_postgres_data
```

### 5. Run

```bash
docker compose up -d --build
```

App is available at `http://localhost` (or your `APP_BASE_URL`).

### 6. Initialize migrations (existing DB)

If you already have a running database, stamp the current Alembic revision so future migrations can be tracked:

```bash
docker compose exec backend alembic stamp 002
```

For a fresh database, apply the schema first (`dinnerflow_schema.sql`), then stamp.

### 7. Set up backups (recommended)

Add a daily cron job for automated database backups:

```bash
crontab -e
# Add this line:
0 2 * * * /home/joel/dinnerflow/scripts/backup-db.sh >> /home/joel/dinnerflow/backups/backup.log 2>&1
```

Backups are saved to `backups/` with 7 daily + 4 weekly rotation. To customize the backup location:

```bash
BACKUP_DIR=/mnt/nas/dinnerflow-backups ./scripts/backup-db.sh
```

---

## Database Schema

```
users            — accounts (email, password_hash, dietary_preferences, email_consent)
recipes          — cookbook (title, source_url, ingredients jsonb, instructions jsonb, rating, is_favorite)
cooking_log      — per-session cook history (recipe_id, date_cooked, rating)
user_integrations — third-party tokens (Todoist API token — Fernet encrypted)
user_sessions    — session tokens (30-day expiry, cleaned up daily)
search_terms     — meal idea pool for weekly email scheduler
recipe_sync_logs — Todoist sync audit log
shopping_list_items — local grocery list
```

Apply schema on a fresh database:

```bash
psql -h localhost -p 5436 -U $DINNER_DB_USER -d $DINNER_DB_NAME \
  -f dinnerflow_schema.sql
```

See [SCHEMA.md](SCHEMA.md) for a full table-by-table reference.

### Migrations (Alembic)

Schema changes are tracked with [Alembic](https://alembic.sqlalchemy.org/) using raw SQL migrations (no SQLAlchemy ORM). Migrations live in `backend/alembic/versions/`.

```bash
# Check current revision
docker compose exec backend alembic current

# Apply pending migrations
docker compose exec backend alembic upgrade head

# Create a new migration
docker compose exec backend alembic revision -m "describe the change"

# Rollback one migration
docker compose exec backend alembic downgrade -1
```

---

## How it works

### Weekly meal plan email

Celery Beat triggers every Tuesday and Saturday at 10:30 AM. For each consented user it:
1. Fetches the user's `search_terms` from the DB
2. Asks the LLM to generate meal ideas
3. Enriches each idea with a real recipe URL via Tavily
4. Sends an HTML email with one-click "Add to My Recipes" links (HMAC-signed, 7-day expiry)

The same flow can be triggered manually via `POST /api/chef/email-plan`.

### Instant Chef

1. `POST /api/chef/instant-ideas` — LLM generates ideas, Tavily finds URLs
2. User selects one → `POST /api/chef/cook` — scrapes the URL, extracts recipe via LLM, saves to DB, syncs to Todoist

---

## Operations

### Backups & Restore

Automated daily backups via `scripts/backup-db.sh` (see Setup step 7). Retention: 7 daily + 4 weekly snapshots.

To restore from a backup:

```bash
./scripts/restore-db.sh backups/daily/dinnerflow_20260414_020000.sql.gz
```

This stops the application containers, drops and recreates the database, restores the dump, and restarts everything. Interactive confirmation required.

### Health Monitoring

The `/health` endpoint reports DB connectivity, database size, and disk usage:

```json
{
  "status": "ok",
  "checks": {
    "database": { "connected": true, "size_mb": 42.3 },
    "disk": { "used_percent": 61.2, "free_gb": 145.8 }
  }
}
```

Returns `"status": "degraded"` if DB is unreachable or disk usage exceeds 90%.

A daily Celery beat task (`check_disk_and_db_usage`, 4 AM) logs disk and database size with warnings at 80% and errors at 90%.

### Log Rotation

All containers use Docker's `json-file` log driver with 10 MB max size and 3-file rotation (configured via the `x-logging` anchor in `compose.yml`).

### Account Management (GDPR / CAN-SPAM)

- **Data export**: `GET /api/account/export-data` — downloads all user data as JSON (also available in Settings UI)
- **Self-service deletion**: `DELETE /api/account/delete` with `{"confirm": true}` (also available in Settings UI)
- **Admin deletion**: `DELETE /api/admin/users/{id}`
- **Email preferences**: `GET/PUT /api/account/email-preferences` — opt-in/out of meal plan emails (Settings UI toggle)
- **One-click unsubscribe**: `GET /api/account/unsubscribe?token=...` — signed link in every email, no login required
- **Privacy policy**: Served at `/privacy` (public page)
- **Cookie notice**: Dismissible banner on first visit (functional session cookie only, no tracking)

Deletion cascades through all tables (recipes, cooking log, shopping list, sessions, integrations, sync logs, search terms) and removes uploaded recipe images from disk.

### Scheduled Tasks (Celery Beat)

| Task | Schedule | Description |
| :--- | :--- | :--- |
| `send_all_meal_plans` | Tue/Sat 10:30 AM | Fan-out weekly meal plan emails to consented users |
| `cleanup_sessions` | Daily 3:00 AM | Purge expired session tokens |
| `check_disk_and_db_usage` | Daily 4:00 AM | Log disk + DB size, warn at 80%/90% |
| `cleanup_stale_data` | Sunday 4:30 AM | Data retention: delete search terms and sync logs older than 90 days |
