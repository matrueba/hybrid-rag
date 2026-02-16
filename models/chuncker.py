from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional



@dataclass
class ChunkingConfig:
    """Configuration for DoclingHybridChunker."""
    max_tokens: int = 512  # Maximum tokens for embedding models
    tokenizer_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"  # Embedding model ID
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])  # Separators for fallback


@dataclass
class DocumentChunk:
    """Represents a document chunk with optional embedding."""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None
    embedding: Optional[List[float]] = None  # For embedder compatibility

    def __post_init__(self):
        """Calculate token count if not provided."""
        if self.token_count is None:
            # Rough estimation: ~4 characters per token
            self.token_count = len(self.content) // 4

