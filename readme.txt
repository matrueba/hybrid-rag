
https://supabase.com/docs/guides/ai/hybrid-search

EN supabase ir a database, Extensions y habilitar pgvector or run 
create extension if not exists vector
with
  schema extensions;


Crear tablas

-- Tabla de documentos
CREATE TABLE IF NOT EXISTS documents (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title       text NOT NULL,
  source      text,
  content     text,
  metadata    jsonb DEFAULT '{}'::jsonb,
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id            bigserial PRIMARY KEY,
  document_id   uuid REFERENCES documents(id) ON DELETE CASCADE,
  content       text NOT NULL,
  embedding     vector(1024),
  chunk_index   int,
  metadata      jsonb DEFAULT '{}'::jsonb,
  token_count   int,
  created_at    timestamptz DEFAULT now(),
  fts           tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED
);

-- * En fts puedes usar diferentes configuraciones, por ejemplo:
--   - 'simple': para inglés
--   - 'spanish': para español
--   - 'english': para inglés

-- Índice vectorial para búsqueda semántica (cosine distance)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
  ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);


-- * m => número de vecinos por nodo (default 16)
-- * ef_construction => número de vecinos a visitar durante la construcción del índice (default 64)


-- 4. Hybrid search RPC (semantic + full-text + RRF in a single query)
--    Use full_text_weight=0 for semantic-only, semantic_weight=0 for text-only.
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text text,
  query_embedding vector(1024),
  match_count int DEFAULT 10,
  full_text_weight float DEFAULT 1.0,
  semantic_weight float DEFAULT 1.0,
  rrf_k int DEFAULT 60
)
RETURNS TABLE (
  chunk_id bigint,
  document_id uuid,
  content text,
  similarity float,
  metadata jsonb,
  document_title text,
  document_source text
)
LANGUAGE sql STABLE
AS $$
WITH full_text AS (
  SELECT
    dc.id,
    row_number() OVER (
      ORDER BY ts_rank(dc.fts, websearch_to_tsquery(query_text)) DESC
    ) AS rank_ix
  FROM document_chunks dc
  WHERE dc.fts @@ websearch_to_tsquery(query_text)
  ORDER BY rank_ix
  LIMIT least(match_count, 30) * 2
),
semantic AS (
  SELECT
    dc.id,
    row_number() OVER (
      ORDER BY dc.embedding <=> query_embedding
    ) AS rank_ix
  FROM document_chunks dc
  ORDER BY rank_ix
  LIMIT least(match_count, 30) * 2
)
SELECT
  dc.id AS chunk_id,
  dc.document_id,
  dc.content,
  (
    coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
    coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight
  ) AS similarity,
  dc.metadata,
  d.title AS document_title,
  d.source AS document_source
FROM
  full_text
  FULL OUTER JOIN semantic ON full_text.id = semantic.id
  JOIN document_chunks dc ON coalesce(full_text.id, semantic.id) = dc.id
  JOIN documents d ON dc.document_id = d.id
ORDER BY similarity DESC
LIMIT least(match_count, 30);
$$;
"""

--- query_embedding vector(1024) Define la cantidad de dimensiones del embedding ---
Depende del modelo usdo será diferente. En este caso usaremos snowflake-arctic-embed2 
que tiene dimension 1024 por defecto.

















Enseñanzas durante el desarrollo

Importancia de entender el contexto y background técnico de lo que se está haciendo 
y no delegar todo a la IA.
Usando OPUS 4.6 me recomendaba usar ivfflat en lugar de hnsw, imagino por que es 
el estándar que los modelos manejan en su set de entrenamiento.
Sin embargo, hnsw es notablemente mejor para búsqueda semántica.
En la query de busqueda recomendaba usar to_tsvector('spanish', content) y 
plainto_tsquery('spanish', query_text), pero lo recomendable es usar fts, que es 
una columna generada que almacena el resultado de to_tsvector.

No quedarte con la primera respuesta de la IA, siempre validar, cuestionar e investigar.

Usar siempre archivos de contexto en el proyecto para guiar a a la IA (Agents.md, Claude.md, o lo que sea)