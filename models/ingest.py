from dataclasses import dataclass
from typing import List


@dataclass
class IngestionConfig:
    """Configuration for document ingestion."""
    max_tokens: int = 512


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    document_id: str
    title: str
    chunks_created: int
    processing_time_ms: float
    errors: List[str]

