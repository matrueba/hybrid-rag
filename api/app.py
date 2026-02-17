"""FastAPI application factory with lifespan-managed RagAgent."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from settings import load_settings
from rag_agent.agent import RagAgent
from api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise Settings and RagAgent on startup; clean up on shutdown."""
    logger.info("🚀 Starting API — initialising agent…")

    settings = load_settings()
    rag_agent = RagAgent(settings, session_id="default")
    await rag_agent.create_agent()

    app.state.settings = settings
    app.state.rag_agent = rag_agent

    logger.info("✅ Agent ready")
    yield
    logger.info("👋 Shutting down API")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="Hubryd RAG API",
        description="REST API for the Hubryd RAG agent.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app
