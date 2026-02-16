
import asyncio
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add root to path so we can import ingestion.embedder
sys.path.append(os.getcwd())

from ingestion.embedder import EmbeddingGenerator

class TestEmbeddingGenerator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock settings to avoid loading .env or actual settings
        self.settings_patcher = patch('ingestion.embedder.load_settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.return_value.embedding_api_key = "fake_key"
        self.mock_settings.return_value.embedding_base_url = "https://api.openai.com/v1"
        self.mock_settings.return_value.embedding_model = "text-embedding-3-small"

        self.embedder = EmbeddingGenerator()
        
        # Mock the client within the embedder
        self.embedder.client = MagicMock()
        self.embedder.client.embeddings.create = MagicMock()

    async def asyncTearDown(self):
        self.settings_patcher.stop()

    async def test_truncation(self):
        print("\nTesting text truncation...")
        # Create a text longer than 8191 tokens
        # 'a ' is 2 chars, likely 1 token. 8200 * 'a ' = 16400 chars, ~8200 tokens
        long_text = "word " * 9000
        truncated = self.embedder._truncate_text(long_text)
        
        tokens = self.embedder.tokenizer.encode(truncated)
        self.assertLessEqual(len(tokens), 8191)
        print(f"Original length: {len(long_text)}, Truncated length: {len(truncated)}")
        print(f"Token count after truncation: {len(tokens)}")

    async def test_generate_embedding(self):
        print("\nTesting embedding generation...")
        
        # Mock response
        mock_response = MagicMock()
        mock_data = MagicMock()
        mock_data.embedding = [0.1, 0.2, 0.3]
        mock_response.data = [mock_data]
        
        # Async mock for create
        f = asyncio.Future()
        f.set_result(mock_response)
        self.embedder.client.embeddings.create.return_value = f

        embedding = await self.embedder.generate_embedding("test text")
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        print("Embedding generated successfully")

    async def test_batch_embedding(self):
        print("\nTesting batch embedding...")
         # Mock response
        mock_response = MagicMock()
        mock_data1 = MagicMock()
        mock_data1.embedding = [0.1, 0.2]
        mock_data2 = MagicMock()
        mock_data2.embedding = [0.3, 0.4]
        mock_response.data = [mock_data1, mock_data2]
        
        f = asyncio.Future()
        f.set_result(mock_response)
        self.embedder.client.embeddings.create.return_value = f

        embeddings = await self.embedder.generate_embeddings_batch(["text1", "text2"])
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(embeddings[0], [0.1, 0.2])
        self.assertEqual(embeddings[1], [0.3, 0.4])
        print("Batch embeddings generated successfully")

if __name__ == '__main__':
    unittest.main()
