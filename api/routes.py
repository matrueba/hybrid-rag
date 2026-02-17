"""FastAPI router with /api/alive, /api/run, and /api/config endpoints."""

import logging
from dataclasses import asdict
from fastapi import APIRouter, Request, HTTPException

from api.models import (
    RunRequest,
    RunResponse,
    ConfigRequest,
    ConfigResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ── Health check ──────────────────────────────────────────────────────

@router.get("/alive")
async def alive():
    """Health-check endpoint."""
    return {"status": "ok"}


# ── Run agent ─────────────────────────────────────────────────────────

@router.post(
    "/run",
    response_model=RunResponse,
    responses={500: {"model": ErrorResponse}},
)
async def run(body: RunRequest, request: Request):
    """Send a prompt to the RAG agent and return its response."""
    try:
        settings = request.app.state.settings
        rag_agent = request.app.state.rag_agent

        # If the caller requests a different session, rebuild the agent
        if body.session_id != rag_agent.session_id:
            from rag_agent.agent import RagAgent
            rag_agent = RagAgent(settings, session_id=body.session_id)
            await rag_agent.create_agent()
            request.app.state.rag_agent = rag_agent

        response = await rag_agent.run_agent(body.prompt)
        return RunResponse(response=response)

    except Exception as exc:
        logger.exception("Error running agent")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Configuration ────────────────────────────────────────────────────

@router.post(
    "/config",
    response_model=ConfigResponse,
    responses={500: {"model": ErrorResponse}},
)
async def config(body: ConfigRequest, request: Request):
    """Update runtime configuration and return the resulting settings."""
    try:
        settings = request.app.state.settings

        # Apply only the fields that were explicitly sent
        update_data = body.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No configuration fields provided.")

        for key, value in update_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown setting: {key}")

        # Rebuild the agent so it picks up new model / connection settings
        from rag_agent.agent import RagAgent
        rag_agent = RagAgent(settings, session_id=request.app.state.rag_agent.session_id)
        await rag_agent.create_agent()
        request.app.state.rag_agent = rag_agent

        logger.info("Configuration updated: %s", update_data)

        return ConfigResponse(
            llm_model=settings.llm_model,
            llm_local=settings.llm_local,
            llm_base_url=settings.llm_base_url,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
            embedding_base_url=settings.embedding_base_url,
            default_match_count=settings.default_match_count,
            max_match_count=settings.max_match_count,
            supabase_url=settings.supabase_url,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error updating configuration")
        raise HTTPException(status_code=500, detail=str(exc))
