"""Pydantic models for the FastAPI endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class RunRequest(BaseModel):
    """Request body for the /api/run endpoint."""
    prompt: str = Field(..., min_length=1, description="The user prompt to send to the agent.")
    session_id: str = Field(default="default", description="Session ID for conversation persistence.")


class RunResponse(BaseModel):
    """Successful response from the /api/run endpoint."""
    response: str


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
    # Agent
    agent_session_id: Optional[str] = None
    # Reranker
    rerank_enabled: Optional[bool] = None
    rerank_model: Optional[str] = None
    rerank_top_k: Optional[int] = None


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
    # Reranker
    rerank_enabled: bool
    rerank_model: str
    rerank_top_k: int


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
