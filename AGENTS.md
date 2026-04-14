# Iron Skillet - Agent Guidelines

## Project Overview

Full-stack meal planning application with:
- **Backend**: Python/FastAPI on port 8010 (debug), 8000 inside container
- **Frontend**: React/Vite/Tailwind served via nginx on port 80
- **Database**: PostgreSQL 15 + pgvector on port 5436
- **Docker Compose** with external volume `dinnerflow_postgres_data`

---

## Commands

### Backend (inside container)

```bash
# Run development server
docker exec -it ironskillet_backend uvicorn main:create_app --reload --host 0.0.0.0 --port 8010

# Run single test file (when tests exist)
docker exec -it ironskillet_backend python -m pytest backend/tests/test_xxx.py::test_function -v

# Run all tests
docker exec -it ironskillet_backend python -m pytest backend/tests/ -v

# Lint with flake8 (when configured)
docker exec -it ironskillet_backend flake8 backend/

# Type check with mypy (when configured)
docker exec -it ironskillet_backend mypy backend/
```

### Frontend (inside container)

```bash
# Run development server
docker exec -it ironskillet_web npm run dev

# Build for production
docker exec -it ironskillet_web npm run build

# Run tests
docker exec -it ironskillet_web npm test

# Lint with ESLint
docker exec -it ironskillet_web npm run lint
```

### Database Migrations (Alembic)

```bash
# Check current migration revision
docker compose exec backend alembic current

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Rollback one migration
docker compose exec backend alembic downgrade -1

# Create a new migration (then edit the generated file)
docker compose exec backend alembic revision -m "describe the change"

# Stamp existing DB at a revision (skip running the migration)
docker compose exec backend alembic stamp 002
```

### Backups

```bash
# Run a backup manually
./scripts/backup-db.sh

# Restore from a backup (interactive — prompts for confirmation)
./scripts/restore-db.sh backups/daily/dinnerflow_20260414_020000.sql.gz

# Custom backup location
BACKUP_DIR=/mnt/nas/backups ./scripts/backup-db.sh
```

### Docker

```bash
# Start all services
docker compose up -d

# Rebuild after dependency changes (e.g. requirements.txt)
docker compose up -d --build backend

# View logs
docker compose logs -f backend
docker compose logs -f web
docker compose logs -f db

# Restart specific service
docker compose restart backend

# Check health (includes DB + disk status)
curl -s http://localhost:8010/health | python3 -m json.tool

# Check container status
docker compose ps
```

---

## Code Style Guidelines

### Python (Backend)

**Import Ordering:**
1. Standard library imports
2. Third-party imports
3. Local application imports
- Alphabetically sorted within each group

```python
import os  # stdlib
from typing import List, Optional  # stdlib
import bcrypt  # third-party
from fastapi import APIRouter, Depends  # third-party

from config import DATABASE_URL  # local
```

**Module Documentation:**
- Use docstrings at module level describing purpose and dependencies
- Include section separators: `# ── Function Name ──────────────────────`

**Type Hints:**
- Use type hints for all function parameters and return values
- Use `Optional[Type]` for nullable fields
- Use `List[Type]`, `Dict[str, Type]` for collections

```python
def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> Optional[Recipe]:
    """Fetch recipe by ID."""
    ...
```

**Error Handling:**
- Use HTTPException with descriptive messages and appropriate status codes
- Validate inputs at function boundaries
- Log errors using `logger = logging.getLogger(__name__)`

```python
from fastapi import HTTPException

if not user:
    raise HTTPException(status_code=404, detail="User not found")
```

**Constants:**
- Define at module level with UPPERCASE naming
- Document purpose in comments

```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB max file size
```

**Router Pattern:**
```python
router = APIRouter(prefix="/api/recipes", tags=["recipes"])

@router.get("/")
async def list_recisions(...):
    ...
```

### TypeScript/JavaScript (Frontend)

**Component Structure:**
- Functional components with React hooks
- Props defined with TypeScript interfaces
- Separate concerns: components, pages, context, api

**API Client:**
- Use Axios instance from `src/api/client.js`
- All endpoints defined in API client; call via client methods

```javascript
import apiClient from '@/api/client';

const recipes = await apiClient.getRecipes();
```

**Styling:**
- Tailwind CSS utility classes
- Responsive design with mobile-first approach

---

## Architecture Notes

### Database Schema
- Main tables: users, recipes, cooking_log, shopping_list_items, user_integrations, user_sessions, search_terms, recipe_sync_logs
- pgvector extension enabled (recipe embeddings column exists)
- Session-based auth with `user_sessions` table

### Key Services
- **services/llm.py**: Recipe extraction from URLs + meal idea generation
- **services/search.py**: Tavily + DuckDuckGo recipe search
- **services/scheduler.py**: Meal plan builder (called by Celery tasks)
- **services/todoist.py**: Todoist API integration for shopping lists
- **celery_app.py**: Celery broker config + beat schedule (meal plans Tue/Sat, session cleanup daily 3 AM, disk/DB monitoring daily 4 AM)
- **tasks.py**: Background task definitions (welcome email, meal plans, session cleanup, disk/DB usage check)

### Ops Infrastructure
- **Alembic** (`backend/alembic/`): Raw SQL database migrations. No SQLAlchemy ORM — uses `op.execute()` for DDL
- **Backup scripts** (`scripts/`): `backup-db.sh` (daily pg_dump + rotation) and `restore-db.sh` (interactive restore)
- **Log rotation**: All containers use `json-file` driver with 10 MB / 3 file rotation (compose.yml `x-logging` anchor)
- **Health endpoint** (`/health`): Reports DB connectivity + size, disk usage %. Returns `"degraded"` on failures
- **Account management** (`routers/account.py`): GDPR data export + self-service account deletion
- **Admin deletion** (`routers/admin.py`): Admin can delete any non-self user

### Onboarding / First-Run UX
- **GET /api/onboarding** (in `routers/dashboard.py`): lightweight endpoint returning `has_recipes`, `has_dietary_prefs`, `has_cooked`, `recipe_count`
- **OnboardingContext** (`web/src/context/OnboardingContext.jsx`): fetches onboarding status once on mount, exposes flags + `refresh()` + `dismiss()` (localStorage-persisted)
- Sidebar shows a "Getting Started" checklist widget (auto-hides when all items are done or user dismisses)
- Tonight page shows a welcome hero card when user has no recipes
- Recipes page shows inline URL import + starter recipe suggestions when empty
- Dashboard, ShoppingList, InstantChef all have actionable empty states with links to relevant pages

### Rate Limiting
- Configured via `slowapi` in `limiter.py`
- Applied to auth endpoints and AI features

---

## Existing Agent Rules

No existing `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files found. This file serves as the single source of truth for agent guidelines.

---

## Testing Infrastructure

**Status**: No test infrastructure currently exists.

When adding tests:
1. Create `backend/tests/` directory with `__init__.py`
2. Add `pytest.ini` or `[tool.pytest]` in `pyproject.toml`
3. Use `conftest.py` for fixtures (db session, test client)
4. Mock external services (LLM, email, Todoist) with pytest-mock
5. Run single test: `python -m pytest backend/tests/test_module.py::test_name -v`

---

## Environment Setup

- `.env` file required at project root (see `.env.example`)
- Gmail OAuth token directory mounted at `/app/google_auth/` in the backend container (read-only)
- Key env vars: TAVILY_API_KEY, GOOGLE_AUTH_PATH, SENDER_EMAIL, FERNET_KEY, SECRET_KEY
- Todoist tokens are per-user, stored Fernet-encrypted in the `user_integrations` table (no env var)

---

## Common Tasks

### Add new API endpoint
1. Create router in `routers/xxx.py` or add to existing
2. Define Pydantic models inline in the router (no separate schemas/ directory)
3. Register router in `main.py`
4. Update frontend API client in `web/src/api/client.js`
5. Add frontend page/component as needed

### Add new database table
1. Create an Alembic migration: `docker compose exec backend alembic revision -m "add foo table"`
2. Edit the generated file in `backend/alembic/versions/` — use `op.execute()` with raw SQL
3. Apply: `docker compose exec backend alembic upgrade head`
4. Add raw SQL queries in the relevant router or service (project uses psycopg2, not an ORM)
5. Update `dinnerflow_schema.sql` so fresh installs include the new table

### Debug container issues
```bash
# Exec into container
docker exec -it ironskillet_backend bash

# Check logs
docker compose logs backend

# Restart service
docker compose restart backend
```
