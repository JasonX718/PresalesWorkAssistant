"""
Embedding generation using OpenAI API.
"""

import logging
from typing import Optional
from openai import OpenAI

from config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using OpenAI API."""

    def __init__(self):
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        Handles batching for large lists.
        """
        if not texts:
            return []

        all_embeddings = []
        batch_size = 100  # OpenAI batch limit

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Clean empty strings
            batch = [t if t.strip() else "empty" for t in batch]

            try:
                response = self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Embedding error for batch {i}: {e}")
                # Return zero vectors for failed batch
                dim = get_settings().embedding_dimension
                all_embeddings.extend([[0.0] * dim] * len(batch))

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query string."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * get_settings().embedding_dimension


# Singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
