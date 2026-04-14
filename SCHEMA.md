# Database Schema

PostgreSQL 15 with the [pgvector](https://github.com/pgvector/pgvector) extension.

---

## Tables

### users

Account records. One per registered user.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| email | text | | NOT NULL, UNIQUE |
| password_hash | text | | NOT NULL |
| full_name | text | | |
| created_at | timestamp | CURRENT_TIMESTAMP | |
| is_admin | boolean | false | |
| dietary_preferences | text | | |
| email_consent | boolean | false | NOT NULL |
| email_consent_date | timestamptz | | |

---

### recipes

User cookbook. Recipes can be scraped from a URL, added manually, or imported via email action links.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| title | text | | NOT NULL |
| source_url | text | | |
| entry_method | text | 'scraped' | |
| ingredients | jsonb | | |
| instructions | jsonb | | |
| full_text_content | text | | |
| local_image_path | text | | |
| embedding | vector(1536) | | |
| created_at | timestamp | CURRENT_TIMESTAMP | |
| rating | integer | | |
| last_cooked | timestamp | | |
| times_cooked | integer | 0 | |
| is_favorite | boolean | false | |
| user_id | integer | | FK -> users (CASCADE) |

---

### cooking_log

Per-cook history entries. A recipe can have many log entries.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| recipe_id | integer | | FK -> recipes |
| date_cooked | date | CURRENT_DATE | |
| rating | integer | | CHECK (1-5) |
| notes | text | | |
| created_at | timestamp | CURRENT_TIMESTAMP | |

---

### shopping_list_items

Per-user grocery list. Items can be checked off in the UI.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| user_id | integer | | FK -> users (CASCADE) |
| item_text | text | | NOT NULL |
| recipe_source | text | | |
| is_checked | boolean | false | |
| created_at | timestamp | CURRENT_TIMESTAMP | |

---

### search_terms

Meal idea pool used by the weekly email scheduler and Instant Chef.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| term | text | | NOT NULL, UNIQUE |
| category | text | | |
| last_used_at | timestamp | | |
| created_at | timestamp | CURRENT_TIMESTAMP | |
| user_id | integer | | FK -> users (CASCADE) |

---

### user_sessions

HTTP-only cookie sessions. Cleaned up daily by Celery Beat.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| token | text | | PK |
| user_id | integer | | NOT NULL, FK -> users (CASCADE) |
| expires_at | timestamptz | | NOT NULL |
| created_at | timestamptz | now() | |

---

### user_integrations

Third-party API tokens. Currently only Todoist. Tokens are Fernet-encrypted at rest.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| user_id | integer | | PK, FK -> users (CASCADE) |
| provider | text | | PK, CHECK ('todoist') |
| api_token | text | | NOT NULL |
| target_list_id | text | | |
| target_list_name | text | | |

---

### recipe_sync_logs

Audit log for Todoist ingredient syncs.

| Column | Type | Default | Constraints |
| :--- | :--- | :--- | :--- |
| id | integer | auto-increment | PK |
| user_id | integer | | FK -> users (CASCADE) |
| recipe_id | integer | | FK -> recipes (SET NULL) |
| ingredients_count | integer | 0 | |
| provider | varchar(50) | 'todoist' | |
| synced_at | timestamptz | now() | |

**Indexes:** `idx_sync_logs_time` (synced_at)
