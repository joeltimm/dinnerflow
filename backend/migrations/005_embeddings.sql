-- Migration 005: Resize the recipe embedding column for the local embedding model.
-- Run against the dinnerflow database:
--   docker exec -i dinner-db psql -U dinneruser -d dinnerflow < backend/migrations/005_embeddings.sql
--
-- The column was vector(1536) (OpenAI dimension) but never populated. The local
-- embedding model (nomic-embed-text-v1.5) outputs 768 dimensions. Since no rows
-- carry an embedding yet, drop and re-add the column at the correct size, then add
-- an HNSW index for fast cosine-distance search. Idempotent.

ALTER TABLE recipes DROP COLUMN IF EXISTS embedding;
ALTER TABLE recipes ADD COLUMN embedding vector(768);

-- HNSW index for approximate nearest-neighbour search by cosine distance (<=>).
CREATE INDEX IF NOT EXISTS idx_recipes_embedding
  ON recipes USING hnsw (embedding vector_cosine_ops);
