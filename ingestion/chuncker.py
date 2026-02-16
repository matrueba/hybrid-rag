
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional

import concurrent.futures
from dotenv import load_dotenv
from transformers import AutoTokenizer
from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument
from models.chuncker import DocumentChunk, ChunkingConfig

load_dotenv()

logger = logging.getLogger(__name__)



class DoclingHybridChunker:
    """
    Docling HybridChunker wrapper for intelligent document splitting.

    This chunker uses Docling's built-in HybridChunker which:
    - Respects document structure (sections, paragraphs, tables)
    - Is token-aware (fits embedding model limits)
    - Preserves semantic coherence
    - Includes heading context in chunks
    """

    def __init__(self, config: ChunkingConfig):
        """
        Initialize chunker.

        Args:
            config: Chunking configuration
        """
        self.config = config
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        logger.info(f"Initializing tokenizer: {config.tokenizer_model_id}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_model_id)
        except Exception as e:
            logger.error(f"Failed to load tokenizer {config.tokenizer_model_id}: {e}")
            self.tokenizer = None

        if self.tokenizer:
            self.chunker = HybridChunker(
                tokenizer=self.tokenizer,
                max_tokens=config.max_tokens,
                merge_peers=True
            )
            logger.info(f"HybridChunker initialized (max_tokens={config.max_tokens})")
        else:
            self.chunker = None
            logger.warning("HybridChunker disabled due to tokenizer failure")

    async def chunk_document(
        self,
        content: str,
        title: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        docling_doc: Optional[DoclingDocument] = None
    ) -> List[DocumentChunk]:
        """
        Chunk a document asynchronously using Docling's HybridChunker or fallback.

        Args:
            content: Document content (markdown format)
            title: Document title
            source: Document source
            metadata: Additional metadata
            docling_doc: Optional pre-converted DoclingDocument (for efficiency)

        Returns:
            List of document chunks with contextualized content
        """
        if not content.strip():
            return []

        base_metadata = {
            "title": title,
            "source": source,
            "chunk_method": "hybrid",
            **(metadata or {})
        }

        if docling_doc is None or self.chunker is None:
            if self.chunker is None:
                raise ValueError("Chunker not initialized")
            raise ValueError("No DoclingDocument provided")

        try:
            loop = asyncio.get_running_loop()
            
            def _process_docling_chunks():
                chunk_iter = self.chunker.chunk(dl_doc=docling_doc)
                chunks = list(chunk_iter)

                result_chunks = []
                current_pos = 0
                for i, chunk in enumerate(chunks):
                    contextualized_text = self.chunker.contextualize(chunk=chunk)
                    
                    if self.tokenizer:
                        token_count = len(self.tokenizer.encode(contextualized_text))
                    else:
                        token_count = len(contextualized_text) // 4

                    provenance = {}
                    if hasattr(chunk, 'prov') and chunk.prov:
                        try:
                            provenance = [p.dict() for p in chunk.prov] 
                        except:
                            provenance = str(chunk.prov)

                    # Create chunk metadata
                    chunk_metadata = {
                        **base_metadata,
                        "total_chunks": len(chunks),
                        "token_count": token_count,
                        "has_context": True,  # Flag indicating contextualized chunk
                        "provenance": provenance
                    }

                    start_char = current_pos
                    end_char = start_char + len(contextualized_text)

                    result_chunks.append(DocumentChunk(
                        content=contextualized_text.strip(),
                        index=i,
                        start_char=start_char,
                        end_char=end_char,
                        metadata=chunk_metadata,
                        token_count=token_count
                    ))

                    current_pos = end_char
                
                return result_chunks

            document_chunks = await loop.run_in_executor(self._executor, _process_docling_chunks)
            
            logger.info(f"Created {len(document_chunks)} chunks using HybridChunker")
            return document_chunks

        except Exception as e:
            logger.error(f"HybridChunker failed: {e}")
            raise ValueError(f"HybridChunker failed: {e}")


def create_chunker(config: ChunkingConfig):
    """
    Create DoclingHybridChunker for intelligent document splitting.

    Args:
        config: Chunking configuration

    Returns:
        DoclingHybridChunker instance
    """
    return DoclingHybridChunker(config)