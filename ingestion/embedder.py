
import logging
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
import openai
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
from models.chuncker import DocumentChunk
from settings import load_settings

load_dotenv()

logger = logging.getLogger(__name__)

settings = load_settings()
EMBEDDING_MODEL = settings.embedding_model


class EmbeddingGenerator:
    """Generates embeddings for document chunks."""

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        batch_size: int = 100,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize embedding generator.

        Args:
            model: Embedding model to use
            batch_size: Number of texts to process in parallel
            api_key: OpenAI API key (optional)
            base_url: OpenAI base URL (optional)
        """
        self.model = model
        self.batch_size = batch_size

        settings = load_settings()
        self.client = openai.AsyncOpenAI(
            api_key=api_key or settings.embedding_api_key,
            base_url=base_url or settings.embedding_base_url
        )
        
        try:
            # Only for checking token count, with an aproximation using cl100k_base is enough
            self.tokenizer = tiktoken.get_encoding("cl100k_base") 
        except KeyError:
            raise ValueError(f"Model {model} not found")


    def _truncate_text(self, text: str) -> str:
        """
        Truncate text to max tokens allowed by the model.
        
        Args:
            text: Input text
            
        Returns:
            Truncated text
        """
        tokens = self.tokenizer.encode(text)
        if len(tokens) > settings.embedding_models[self.model]["max_tokens"]:
            # Perform truncation
            return self.tokenizer.decode(tokens[:settings.embedding_models[self.model]["max_tokens"]])
        return text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        text = self._truncate_text(text)

        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        processed_texts = [self._truncate_text(text) for text in texts]

        response = await self.client.embeddings.create(
            model=self.model,
            input=processed_texts
        )

        return [data.embedding for data in response.data]

    async def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        progress_callback: Optional[callable] = None
    ) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of document chunks
            progress_callback: Optional callback for progress updates

        Returns:
            Chunks with embeddings added
        """
        if not chunks:
            return chunks

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Process chunks in batches
        embedded_chunks = []
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i:i + self.batch_size]
            batch_texts = [chunk.content for chunk in batch_chunks]

            # Generate embeddings for this batch
            embeddings = await self.generate_embeddings_batch(batch_texts)

            # Add embeddings to chunks
            for chunk, embedding in zip(batch_chunks, embeddings):
                embedded_chunk = DocumentChunk(
                    content=chunk.content,
                    index=chunk.index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    metadata={
                        **chunk.metadata,
                        "embedding_model": self.model,
                        "embedding_generated_at": datetime.now().isoformat()
                    },
                    token_count=chunk.token_count
                )
                embedded_chunk.embedding = embedding
                embedded_chunks.append(embedded_chunk)

            # Progress update
            current_batch = (i // self.batch_size) + 1
            if progress_callback:
                progress_callback(current_batch, total_batches)

            logger.info(f"Processed batch {current_batch}/{total_batches}")

        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        return embedded_chunks

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query

        Returns:
            Query embedding
        """
        if len(query) == 0:
            return []
        if type(query) == list:
            return await self.generate_embeddings_batch(query)
        return await self.generate_embedding(query)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model."""
        return self.config["dimensions"]


def create_embedder(model: str = EMBEDDING_MODEL, **kwargs) -> EmbeddingGenerator:
    """
    Create embedding generator.

    Args:
        model: Embedding model to use
        **kwargs: Additional arguments for EmbeddingGenerator

    Returns:
        EmbeddingGenerator instance
    """
    return EmbeddingGenerator(model=model, **kwargs)