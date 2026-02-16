
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from supabase import create_client, Client
from settings import load_settings, Settings
from ingestion.embedder import EmbeddingGenerator, create_embedder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared dependencies for search tools
# ---------------------------------------------------------------------------

class SearchDeps:
    """Encapsulates Supabase client, settings, and embedder for search tools."""

    def __init__(
        self,
        supabase: Optional[Client] = None,
        settings: Optional[Settings] = None,
        embedder: Optional[EmbeddingGenerator] = None,
    ):
        self.settings = settings or load_settings()
        self.supabase = supabase or create_client(
            self.settings.supabase_url,
            self.settings.supabase_key,
        )
        self.embedder = embedder or create_embedder()


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    """Model for search results."""

    chunk_id: str = Field(..., description="Chunk row ID as string")
    document_id: str = Field(..., description="Parent document UUID as string")
    content: str = Field(..., description="Chunk text content")
    similarity: float = Field(..., description="RRF relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    document_title: str = Field("", description="Title from parent document")
    document_source: str = Field("", description="Source from parent document")


# ---------------------------------------------------------------------------
# Hybrid search  (single RPC — semantic + full-text + RRF all in SQL)
# ---------------------------------------------------------------------------

async def hybrid_search(
    deps: SearchDeps,
    query: str,
    match_count: Optional[int] = None,
    full_text_weight: float = 1.0,
    semantic_weight: float = 1.0,
    rrf_k: int = 60,
) -> List[SearchResult]:
    """
    Perform hybrid search combining semantic and keyword matching.

    Calls a single Supabase RPC that runs both vector search and full-text
    search, then merges results using Reciprocal Rank Fusion — all in SQL.

    Weight configuration:
        - full_text_weight=1, semantic_weight=1 → hybrid (default)
        - full_text_weight=0, semantic_weight=1 → semantic only
        - full_text_weight=1, semantic_weight=0 → full-text only

    Args:
        deps: Search dependencies (Supabase client, embedder, settings).
        query: Search query text.
        match_count: Number of results to return (default from settings).
        full_text_weight: Weight for full-text results (0 to disable).
        semantic_weight: Weight for semantic results (0 to disable).
        rrf_k: RRF smoothing constant (default 60, per Cormack et al. 2009).

    Returns:
        List of search results sorted by combined RRF score.
    """
    try:
        if match_count is None:
            match_count = deps.settings.default_match_count
        match_count = min(match_count, deps.settings.max_match_count)

        logger.info(
            "hybrid_search starting: query='%s', match_count=%d, "
            "ft_weight=%.1f, sem_weight=%.1f",
            query, match_count, full_text_weight, semantic_weight,
        )

        # Generate query embedding
        query_embedding = await deps.embedder.embed_query(query)

        # Single RPC call — everything happens in PostgreSQL
        response = deps.supabase.rpc(
            "hybrid_search",
            {
                "query_text": query,
                "query_embedding": query_embedding,
                "match_count": match_count,
                "full_text_weight": full_text_weight,
                "semantic_weight": semantic_weight,
                "rrf_k": rrf_k,
            },
        ).execute()

        results = _rows_to_search_results(response.data or [])

        logger.info(
            "hybrid_search_completed: query='%s', returned=%d",
            query, len(results),
        )
        return results

    except Exception as e:
        logger.exception("hybrid_search_error: query=%s, error=%s", query, e)
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows_to_search_results(rows: List[Dict[str, Any]]) -> List[SearchResult]:
    """Convert raw Supabase RPC rows to ``SearchResult`` objects."""
    return [
        SearchResult(
            chunk_id=str(row["chunk_id"]),
            document_id=str(row["document_id"]),
            content=row["content"],
            similarity=float(row.get("similarity", 0.0)),
            metadata=row.get("metadata") or {},
            document_title=row.get("document_title", ""),
            document_source=row.get("document_source", ""),
        )
        for row in rows
    ]