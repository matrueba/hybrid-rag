from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import Optional
from pydantic_ai.ag_ui import StateDeps
from tools import SearchDeps, hybrid_search
from system_prompt import MAIN_SYSTEM_PROMPT


class RAGState(BaseModel):
    """Minimal shared state for the RAG agent."""
    pass


rag_agent = Agent(
    'gemini-3-flash-preview',
    deps_type=StateDeps[RAGState],
    system_prompt=MAIN_SYSTEM_PROMPT
)


@rag_agent.tool
async def search_knowledge_base(
    ctx: RunContext[StateDeps[RAGState]],
    query: str,
    match_count: Optional[int] = 5,
    full_text_weight: Optional[float] = 1.0,
    semantic_weight: Optional[float] = 1.0,
) -> str:
    """
    Search the knowledge base for relevant information.

    Uses hybrid search combining semantic (vector) and full-text (keyword)
    matching with Reciprocal Rank Fusion. Adjust weights to control the
    search strategy:
        - Both 1.0 → hybrid search (default, recommended)
        - full_text_weight=0 → semantic only
        - semantic_weight=0  → full-text only

    Args:
        ctx: Agent runtime context with state dependencies
        query: Search query text
        match_count: Number of results to return (default: 5)
        full_text_weight: Weight for keyword matching (0 to disable)
        semantic_weight: Weight for semantic matching (0 to disable)

    Returns:
        String containing the retrieved information formatted for the LLM
    """
    try:
        deps = SearchDeps()

        results = await hybrid_search(
            deps,
            query,
            match_count=match_count,
            full_text_weight=full_text_weight or 1.0,
            semantic_weight=semantic_weight or 1.0,
        )

        if not results:
            return "No relevant information found in the knowledge base."

        response_parts = [f"Found {len(results)} relevant documents:\n"]

        for i, result in enumerate(results, 1):
            response_parts.append(
                f"\n--- Document {i}: {result.document_title} "
                f"(relevance: {result.similarity:.4f}) ---"
            )
            response_parts.append(result.content)

        return "\n".join(response_parts)

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"