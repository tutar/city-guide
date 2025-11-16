"""
Text embedding service for generating embeddings from text.

This service provides a simplified interface for generating text embeddings
that can be used with the vector retrieval service.
"""

import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)


class TextEmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._embedding_dim = 1024  # Qwen3-Embedding-0.6B embedding dimension

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector
        """
        if not text.strip():
            return self._get_zero_embedding()

        cache_key = self._get_cache_key(text)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            # In production, this would call the actual embedding model
            # For now, generate a simulated embedding
            embedding = self._generate_simulated_embedding(text)

            # Cache the result
            self._embedding_cache[cache_key] = embedding

            logger.debug(f"Generated embedding for text: '{text[:50]}...'")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return self._get_zero_embedding()

    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)

        return embeddings

    def _generate_simulated_embedding(self, text: str) -> np.ndarray:
        """
        Generate a simulated embedding vector.

        In production, this would be replaced with actual model inference.
        This simulation creates embeddings that capture some semantic properties.
        """
        # Convert text to lowercase and split into words
        words = text.lower().split()

        # Create a simple hash-based embedding
        embedding = np.zeros(self._embedding_dim)

        for word in words:
            # Create a deterministic hash for the word
            word_hash = hash(word) % self._embedding_dim
            # Add contribution from this word
            embedding[word_hash] += 1.0 / (len(words) + 1)

        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Add some random noise to simulate real embeddings
        noise = np.random.normal(0, 0.01, self._embedding_dim)
        embedding = embedding + noise

        # Re-normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _get_zero_embedding(self) -> np.ndarray:
        """Get a zero embedding vector."""
        return np.zeros(self._embedding_dim)

    def _get_cache_key(self, text: str) -> str:
        """Create cache key for text."""
        # Use first 100 characters as key to avoid too long keys
        return text[:100].lower().strip()

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_embeddings": len(self._embedding_cache),
            "embedding_dimension": self._embedding_dim,
        }


# Global service instance
_text_embedding_service = TextEmbeddingService()


def get_text_embedding_service() -> TextEmbeddingService:
    """Get the global text embedding service instance."""
    return _text_embedding_service
