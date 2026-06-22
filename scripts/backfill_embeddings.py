#!/usr/bin/env python3
"""
Backfill embeddings for recipes that don't have one yet (semantic search + dedup).

Run inside the backend container so it has DB access + the embedding endpoint:

    docker exec -w /app ironskillet_backend python scripts/backfill_embeddings.py

Safe to re-run: only rows with a NULL embedding are processed.
"""
import logging

import psycopg2.extras

from database import get_connection, init_pool
from services import llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backfill_embeddings")


def main() -> None:
    init_pool()
    with get_connection() as conn:
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, ingredients, instructions "
                "FROM recipes WHERE embedding IS NULL ORDER BY id"
            )
            rows = cur.fetchall()

    log.info("%d recipe(s) need an embedding", len(rows))
    embedded = failed = 0
    for r in rows:
        try:
            text = llm.recipe_embedding_text(
                r["title"], r["ingredients"] or [], r["instructions"] or []
            )
            vector = llm.to_pgvector(llm.generate_embedding(text))
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE recipes SET embedding = %s::vector WHERE id = %s",
                        (vector, r["id"]),
                    )
            embedded += 1
            log.info("embedded recipe %d (%s)", r["id"], r["title"])
        except Exception as exc:
            failed += 1
            log.error("recipe %d failed: %s", r["id"], exc)

    log.info("Done: %d embedded, %d failed", embedded, failed)


if __name__ == "__main__":
    main()
