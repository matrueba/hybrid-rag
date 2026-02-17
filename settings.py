import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    # Vector store settings
    vector_store_table: str = os.getenv("VECTOR_STORE_TABLE", "documents")
    documents_table: str = "documents"
    chunks_table: str = "document_chunks"
    # Search settings
    default_match_count: int = int(os.getenv("DEFAULT_MATCH_COUNT", "10"))
    max_match_count: int = int(os.getenv("MAX_MATCH_COUNT", "50"))
    # Embedding settings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "snowflake-arctic-embed2")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434/v1")
    # LLM settings
    llm_local: bool = os.getenv("LLM_LOCAL", "False")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    # Tracing settings
    tracing_api_key: str = os.getenv("TRACING_API_KEY", "")
    embedding_models: dict = field(default_factory=lambda: {
        "snowflake-arctic-embed2": {
            "model": "snowflake-arctic-embed2",
            "dimensions": 1024,
            "max_tokens": 8191
        },
        "nomic-embed-text-v2-moe": {
            "model": "nomic-embed-text-v2-moe",
            "dimensions": 768,
            "max_tokens": 512
        }
    })
    # Google Drive settings
    gdrive_credentials_file: str = os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json")
    gdrive_folder_id: str = os.getenv("GDRIVE_FOLDER_ID", "")
    # Reranking settings
    rerank_enabled: bool = os.getenv("RERANK_ENABLED", "False")
    rerank_provider: str = os.getenv("RERANK_PROVIDER", "local")
    rerank_model: str = os.getenv("RERANK_MODEL", "rerank-v3.5")
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "5"))


def load_settings() -> Settings:
    return Settings()

