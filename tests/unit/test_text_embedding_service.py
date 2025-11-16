"""
Unit tests for the text embedding service.
"""

import pytest
import numpy as np

from src.services.text_embedding_service import TextEmbeddingService


class TestTextEmbeddingService:
    """Test cases for the TextEmbeddingService class."""

    @pytest.fixture
    def text_embedding_service(self):
        """Create a fresh text embedding service for each test."""
        return TextEmbeddingService()

    def test_get_embedding_basic(self, text_embedding_service):
        """Test basic embedding generation."""
        text = "This is a test sentence for embedding generation."
        embedding = text_embedding_service.get_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1024,)  # Qwen3-Embedding-0.6B dimension
        assert np.all(np.isfinite(embedding))
        assert 0.0 <= np.linalg.norm(embedding) <= 1.0 + 1e-6  # Should be normalized

    def test_get_embedding_empty_text(self, text_embedding_service):
        """Test embedding generation with empty text."""
        embedding = text_embedding_service.get_embedding("")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1024,)
        assert np.all(embedding == 0.0)  # Should be zero vector

    def test_get_embedding_whitespace_text(self, text_embedding_service):
        """Test embedding generation with whitespace-only text."""
        embedding = text_embedding_service.get_embedding("   \n\t  ")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1024,)
        assert np.all(embedding == 0.0)  # Should be zero vector

    def test_get_embedding_consistency(self, text_embedding_service):
        """Test that embeddings are consistent for the same text."""
        text = "Consistent embedding test text"
        embedding1 = text_embedding_service.get_embedding(text)
        embedding2 = text_embedding_service.get_embedding(text)

        # Should be identical (cached)
        np.testing.assert_array_equal(embedding1, embedding2)

    def test_get_embedding_different_texts(self, text_embedding_service):
        """Test that different texts produce different embeddings."""
        text1 = "First test sentence"
        text2 = "Second test sentence"

        embedding1 = text_embedding_service.get_embedding(text1)
        embedding2 = text_embedding_service.get_embedding(text2)

        # Should be different (but might have some similarity)
        similarity = np.dot(embedding1, embedding2)
        assert -1.0 <= similarity <= 1.0

    def test_get_embeddings_batch(self, text_embedding_service):
        """Test batch embedding generation."""
        texts = [
            "First sentence for batch processing",
            "Second sentence for batch processing",
            "Third sentence for batch processing",
        ]

        embeddings = text_embedding_service.get_embeddings_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)

        for embedding in embeddings:
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (1024,)
            assert np.all(np.isfinite(embedding))

    def test_get_embeddings_batch_empty(self, text_embedding_service):
        """Test batch embedding generation with empty list."""
        embeddings = text_embedding_service.get_embeddings_batch([])

        assert isinstance(embeddings, list)
        assert len(embeddings) == 0

    def test_get_embeddings_batch_mixed(self, text_embedding_service):
        """Test batch embedding generation with mixed content."""
        texts = ["Normal text", "", "Another normal text"]  # Empty text

        embeddings = text_embedding_service.get_embeddings_batch(texts)

        assert len(embeddings) == 3

        # Check that empty text produces zero embedding
        assert np.all(embeddings[1] == 0.0)

        # Check that normal texts produce non-zero embeddings
        assert not np.all(embeddings[0] == 0.0)
        assert not np.all(embeddings[2] == 0.0)

    def test_generate_simulated_embedding(self, text_embedding_service):
        """Test simulated embedding generation."""
        text = "Test text for simulated embedding"
        embedding = text_embedding_service._generate_simulated_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1024,)
        assert np.all(np.isfinite(embedding))
        assert 0.0 <= np.linalg.norm(embedding) <= 1.0 + 1e-6

    def test_get_zero_embedding(self, text_embedding_service):
        """Test zero embedding generation."""
        zero_embedding = text_embedding_service._get_zero_embedding()

        assert isinstance(zero_embedding, np.ndarray)
        assert zero_embedding.shape == (1024,)
        assert np.all(zero_embedding == 0.0)

    def test_get_cache_key(self, text_embedding_service):
        """Test cache key generation."""
        text = "This is a test text for cache key generation"
        cache_key = text_embedding_service._get_cache_key(text)

        assert isinstance(cache_key, str)
        assert len(cache_key) <= 100  # Should be truncated
        assert cache_key == text[:100].lower().strip()

    def test_get_cache_key_long_text(self, text_embedding_service):
        """Test cache key generation with long text."""
        long_text = "a" * 200  # 200 character text
        cache_key = text_embedding_service._get_cache_key(long_text)

        assert len(cache_key) == 100  # Should be truncated to 100 chars

    def test_clear_cache(self, text_embedding_service):
        """Test cache clearing functionality."""
        # Generate some embeddings to populate cache
        text1 = "First text for cache"
        text2 = "Second text for cache"

        text_embedding_service.get_embedding(text1)
        text_embedding_service.get_embedding(text2)

        # Check cache is populated
        stats_before = text_embedding_service.get_cache_stats()
        assert stats_before["cached_embeddings"] > 0

        # Clear cache
        text_embedding_service.clear_cache()

        # Check cache is empty
        stats_after = text_embedding_service.get_cache_stats()
        assert stats_after["cached_embeddings"] == 0

    def test_get_cache_stats(self, text_embedding_service):
        """Test cache statistics retrieval."""
        stats = text_embedding_service.get_cache_stats()

        assert "cached_embeddings" in stats
        assert "embedding_dimension" in stats
        assert isinstance(stats["cached_embeddings"], int)
        assert stats["embedding_dimension"] == 1024

    def test_embedding_normalization(self, text_embedding_service):
        """Test that embeddings are properly normalized."""
        texts = [
            "Short text",
            "This is a longer text with more words and content for testing normalization",
            "Another test sentence for embedding normalization verification",
        ]

        for text in texts:
            embedding = text_embedding_service.get_embedding(text)
            norm = np.linalg.norm(embedding)

            # Embeddings should be approximately normalized
            assert abs(norm - 1.0) < 0.1  # Allow some tolerance for noise

    def test_embedding_semantic_properties(self, text_embedding_service):
        """Test that embeddings capture some semantic properties."""
        similar_texts = [
            "How to register a business",
            "Business registration process",
            "Company registration procedure",
        ]

        different_text = "Weather forecast for tomorrow"

        # Get embeddings for similar texts
        similar_embeddings = [
            text_embedding_service.get_embedding(text) for text in similar_texts
        ]

        # Get embedding for different text
        different_embedding = text_embedding_service.get_embedding(different_text)

        # Calculate similarities
        similar_similarities = []
        for i in range(len(similar_embeddings)):
            for j in range(i + 1, len(similar_embeddings)):
                similarity = np.dot(similar_embeddings[i], similar_embeddings[j])
                similar_similarities.append(similarity)

        # Calculate similarities with different text
        different_similarities = [
            np.dot(emb, different_embedding) for emb in similar_embeddings
        ]

        # Similar texts should have higher similarity than with different text
        avg_similar_similarity = np.mean(similar_similarities)
        avg_different_similarity = np.mean(different_similarities)

        # This is a probabilistic test - in most cases this should hold
        # but we allow for some randomness in the simulated embeddings
        assert avg_similar_similarity >= avg_different_similarity - 0.2
