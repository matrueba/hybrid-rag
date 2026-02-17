"""
Reranker module — reorders search results using a cross-encoder model.
  - local   : sentence-transformers cross-encoder (offline, English-centric)
"""

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class Reranker(ABC):
    """Base interface for rerankers."""

    @abstractmethod
    async def rerank(self, query: str, results: list, top_k: int = 5) -> list:
        """Reorder *results* by relevance to *query* and return the top-k."""



# ---------------------------------------------------------------------------
# Local cross-encoder (optional)
# ---------------------------------------------------------------------------

class LocalReranker(Reranker):
    """Reranker using a local cross-encoder from sentence-transformers."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    async def rerank(self, query: str, results: list, top_k: int = 5) -> list:
        if not results:
            return results

        pairs = [(query, r.content) for r in results]
        scores = self.model.predict(pairs)

        # Attach scores and sort descending
        scored = list(zip(results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for result, score in scored[:top_k]:
            result.similarity = float(score)
            reranked.append(result)

        logger.info("local_rerank_done: returned %d results", len(reranked))
        return reranked


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_reranker(settings) -> Reranker:
    """
    Create the appropriate reranker based on settings.

    Args:
        settings: Application settings with rerank_provider, rerank_model,
                  and rerank_api_key.

    Returns:
        A Reranker instance.
    """
    provider = settings.rerank_provider.lower()
    if provider == "local":
        return LocalReranker(model_name=settings.rerank_model)
    else:
        raise ValueError(f"Unknown rerank provider: {provider}")
