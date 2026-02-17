"""Pydantic models for the FastAPI endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


# ── /api/run ──────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    """Request body for the /api/run endpoint."""
    prompt: str = Field(..., min_length=1, description="The user prompt to send to the agent.")
    session_id: str = Field(default="default", description="Session ID for conversation persistence.")


class RunResponse(BaseModel):
    """Successful response from the /api/run endpoint."""
    response: str


# ── /api/config ───────────────────────────────────────────────────────

class ConfigRequest(BaseModel):
    """Request body for the /api/config endpoint. All fields are optional; only supplied fields are updated."""
    # LLM
    llm_model: Optional[str] = None
    llm_local: Optional[bool] = None
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    # Embedding
    embedding_model: Optional[str] = None
    embedding_dimensions: Optional[int] = None
    embedding_api_key: Optional[str] = None
    embedding_base_url: Optional[str] = None
    # Search
    default_match_count: Optional[int] = None
    max_match_count: Optional[int] = None
    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None


class ConfigResponse(BaseModel):
    """Returns the current settings after an update."""
    # LLM
    llm_model: str
    llm_local: bool
    llm_base_url: str
    # Embedding
    embedding_model: str
    embedding_dimensions: int
    embedding_base_url: str
    # Search
    default_match_count: int
    max_match_count: int
    # Supabase
    supabase_url: str


# ── generic ───────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Generic error envelope."""
    detail: str
