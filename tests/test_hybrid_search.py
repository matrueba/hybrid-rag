"""Quick test for hybrid_search via Supabase RPC."""

import asyncio
from tools import SearchDeps, hybrid_search


async def main():
    deps = SearchDeps()

    # Default hybrid search (both weights = 1.0)
    results = await hybrid_search(deps, "Seguimiento de KPIs y Cierre Provisional Enero", match_count=5)
    print(f"Hybrid results: {len(results)}")
    for r in results:
        print(f"  [{r.similarity:.4f}] {r.document_title}: {r.content[:80]}...")

    # Semantic-only (full_text_weight=0)
    results = await hybrid_search(deps, "test query", match_count=5, full_text_weight=0.0)
    print(f"\nSemantic-only results: {len(results)}")

    # Text-only (semantic_weight=0)
    results = await hybrid_search(deps, "test query", match_count=5, semantic_weight=0.0)
    print(f"\nText-only results: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())