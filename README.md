# 🍳 Dinnerflow

**The Self-Hosted, AI-Powered Meal Planning Engine.**

![Dinnerflow Logo](static/images/cooking-ogre.png)

Dinnerflow is a robust, self-hosted application designed to streamline meal planning, recipe management, and grocery automation. Built on a containerized architecture, it combines a **Streamlit** frontend for interaction, a **PostgreSQL** database for storage, and **n8n** for AI-driven automation and "Auto-Chef" capabilities.

---

## ✨ Features

### 📖 The Cookbook (CMS)
* **Recipe Management:** Manually add recipes or ingest them via URL.
* **Detailed Views:** View ingredients, instructions, and chef's notes.
* **Interactivity:**
    * ⭐ **Rate Meals:** 5-star rating system.
    * ❤️ **Favorites:** Toggle favorite meals for quick access.
    * 🔥 **Cook Counter:** Track how many times a meal has been cooked.
    * 📅 **History:** Logs the last cooked date.
* **CRUD Actions:** Edit notes instantly or delete recipes (which auto-cleans image files from disk).

### 📊 Kitchen Analytics
A real-time dashboard visualizing your cooking habits:
* **Total Stats:** Recipe count, total meals cooked, average rating.
* **Charts:** "Most Cooked" bar charts and "Hall of Fame" (Highest Rated).

### 🤖 Auto-Chef (n8n Integration)
A sidebar trigger that wakes up your n8n automation workflow to:
1.  **Scrape & Search:** Query the web (via Tavily) for new meal ideas.
2.  **Hybrid Selection:** Generates a weekly plan using **4 random new ideas** + **1 proven favorite** from your existing library.
3.  **Delivery:** Emails a formatted HTML meal plan to your inbox.

---

## 🏗️ Architecture

Dinnerflow runs entirely in Docker.

| Service | Technology | Description |
| :--- | :--- | :--- |
| **App** | Streamlit (Python) | The user interface and application logic. |
| **Database** | PostgreSQL | Persists recipes, history, and search terms. |
| **Automation** | n8n | Workflow engine for web scraping, AI parsing, and email. |
| **AI/Search** | Tavily / Local LLM | Used by n8n to find and parse recipes. |

---

## 🛠️ Setup & Installation

### Prerequisites
* Docker & Docker Compose
* (Optional) An n8n instance if running automation externally.

### 1. File Structure
Ensure your project directory looks like this:
```text
dinnerflow/
├── app.py                  # Main Streamlit application
├── docker-compose.yml      # Container orchestration
├── Dockerfile              # App build instructions
└── static/
    └── images/
        ├── cooking-ogre.png          # Sidebar Logo
        └── cooking-ogre-favicon.png  # Browser Tab Icon

###2. Environment Variables
Create a .env file (or set in docker-compose.yml) for your database credentials:

POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=postgres

### 3. Run the Stack
docker compose up -d --build

Access the application at http://localhost:8501.

💾 Database Schema
Dinnerflow uses two primary tables.

1. recipes (The Cookbook)
Stores your curated collection.

SQL

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title TEXT,
    source_url TEXT,
    local_image_path TEXT,
    full_text_content TEXT,  -- Notes/Instructions
    entry_method TEXT,       -- 'manual', 'experimental', etc.
    rating INTEGER,          -- 0-5 Stars
    last_cooked TIMESTAMP,
    times_cooked INTEGER DEFAULT 0,
    is_favorite BOOLEAN DEFAULT FALSE,
    ingredients JSONB,       -- (Planned feature)
    instructions JSONB       -- (Planned feature)
);
2. search_terms (The Idea Pool)
Used by n8n to pick random meal ideas.

SQL

CREATE TABLE search_terms (
    id SERIAL PRIMARY KEY,
    term TEXT NOT NULL,
    last_used_at TIMESTAMP
);
⚙️ The "Auto-Chef" Workflow
The "Generate Email Plan" button in the app sidebar triggers a Webhook in n8n (GET /webhook/get-more-dinner).

Logic Flow:

Query: n8n selects 4 random terms from search_terms (that haven't been used in 30 days) AND 1 random recipe from the recipes table.

Search: Uses Tavily API to find the best current recipe for the search terms.

Format: Aggregates the results into an HTML email.

Send: Delivers the "Mix Tape" meal plan to the user.
