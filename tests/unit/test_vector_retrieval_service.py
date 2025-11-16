"""
Unit tests for the vector retrieval service.
"""

import pytest
import numpy as np
from uuid import UUID

from src.services.vector_retrieval_service import VectorRetrievalService
from src.services.text_embedding_service import TextEmbeddingService


class TestVectorRetrievalService:
    """Test cases for the VectorRetrievalService class."""

    @pytest.fixture
    def vector_retrieval_service(self):
        """Create a fresh vector retrieval service for each test."""
        return VectorRetrievalService()

    @pytest.fixture
    def text_embedding_service(self):
        """Create a text embedding service for testing."""
        return TextEmbeddingService()

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            {
                "title": "Business Registration Guide",
                "content": "This guide explains how to register a business in Shenzhen. It covers the required documents and procedures.",
                "document_type": "guide",
                "attribution_metadata": {"category": "business", "region": "Shenzhen"},
            },
            {
                "title": "Tax Regulations",
                "content": "This document contains tax regulations and requirements for businesses operating in Shenzhen.",
                "document_type": "regulation",
                "attribution_metadata": {"category": "tax", "region": "Shenzhen"},
            },
            {
                "title": "Employment Law",
                "content": "Labor laws and employment regulations for companies in Guangdong province.",
                "document_type": "law",
                "attribution_metadata": {
                    "category": "employment",
                    "region": "Guangdong",
                },
            },
        ]

    def test_find_most_relevant_document_basic(
        self, vector_retrieval_service, sample_documents
    ):
        """Test basic document retrieval functionality."""
        query = "How to register a business in Shenzhen?"

        results = vector_retrieval_service.find_most_relevant_document(
            query_text=query,
            documents=sample_documents,
            top_k=2,
            similarity_threshold=0.1,
        )

        assert len(results) > 0
        assert "document" in results[0]
        assert "similarity_score" in results[0]
        assert "document_id" in results[0]
        assert isinstance(results[0]["document_id"], UUID)
        assert 0.0 <= results[0]["similarity_score"] <= 1.0

    def test_find_most_relevant_document_empty_query(
        self, vector_retrieval_service, sample_documents
    ):
        """Test retrieval with empty query."""
        results = vector_retrieval_service.find_most_relevant_document(
            query_text="", documents=sample_documents
        )

        assert len(results) == 0

    def test_find_most_relevant_document_no_documents(self, vector_retrieval_service):
        """Test retrieval with no documents."""
        results = vector_retrieval_service.find_most_relevant_document(
            query_text="test query", documents=[]
        )

        assert len(results) == 0

    def test_find_most_relevant_document_high_threshold(
        self, vector_retrieval_service, sample_documents
    ):
        """Test retrieval with high similarity threshold."""
        query = "How to register a business in Shenzhen?"

        results = vector_retrieval_service.find_most_relevant_document(
            query_text=query,
            documents=sample_documents,
            top_k=3,
            similarity_threshold=0.9,  # Very high threshold
        )

        # With high threshold, we might get fewer results
        assert len(results) <= len(sample_documents)

        # All returned results should meet the threshold
        for result in results:
            assert result["similarity_score"] >= 0.9

    def test_calculate_document_similarity(
        self, vector_retrieval_service, sample_documents, text_embedding_service
    ):
        """Test document similarity calculation."""
        query = "business registration"
        query_embedding = text_embedding_service.get_embedding(query)
        document = sample_documents[0]

        similarity = vector_retrieval_service._calculate_document_similarity(
            query_embedding, document
        )

        assert 0.0 <= similarity <= 1.0

    def test_calculate_document_similarity_empty_document(
        self, vector_retrieval_service, text_embedding_service
    ):
        """Test similarity calculation with empty document."""
        query = "test query"
        query_embedding = text_embedding_service.get_embedding(query)
        empty_document = {"title": "", "content": ""}

        similarity = vector_retrieval_service._calculate_document_similarity(
            query_embedding, empty_document
        )

        assert similarity == 0.0

    def test_extract_document_content(self, vector_retrieval_service, sample_documents):
        """Test document content extraction."""
        document = sample_documents[0]
        content = vector_retrieval_service._extract_document_content(document)

        assert isinstance(content, str)
        assert len(content) > 0
        assert "Business Registration Guide" in content
        assert "register a business" in content

    def test_extract_document_content_minimal(self, vector_retrieval_service):
        """Test content extraction with minimal document."""
        minimal_doc = {"title": "Test Title"}
        content = vector_retrieval_service._extract_document_content(minimal_doc)

        assert content == "Test Title"

    def test_cosine_similarity_identical_vectors(self, vector_retrieval_service):
        """Test cosine similarity with identical vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = vector_retrieval_service._cosine_similarity(vec1, vec2)

        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self, vector_retrieval_service):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        similarity = vector_retrieval_service._cosine_similarity(vec1, vec2)

        assert abs(similarity - 0.0) < 1e-6

    def test_cosine_similarity_opposite_vectors(self, vector_retrieval_service):
        """Test cosine similarity with opposite vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])

        similarity = vector_retrieval_service._cosine_similarity(vec1, vec2)

        assert similarity == 0.0  # Should be clipped to 0

    def test_clear_cache(self, vector_retrieval_service, sample_documents):
        """Test cache clearing functionality."""
        # Perform some operations to populate cache
        query = "test query"
        vector_retrieval_service.find_most_relevant_document(
            query_text=query, documents=sample_documents
        )

        # Clear cache
        vector_retrieval_service.clear_cache()

        # Cache should be empty
        stats = vector_retrieval_service.get_cache_stats()
        assert stats["cached_similarities"] == 0

    def test_get_cache_stats(self, vector_retrieval_service):
        """Test cache statistics retrieval."""
        stats = vector_retrieval_service.get_cache_stats()

        assert "cached_similarities" in stats
        assert "cache_hit_rate" in stats
        assert isinstance(stats["cached_similarities"], int)
        assert isinstance(stats["cache_hit_rate"], float)

    def test_fallback_results(self, vector_retrieval_service, sample_documents):
        """Test fallback results generation."""
        results = vector_retrieval_service._get_fallback_results(sample_documents)

        assert len(results) == 1
        assert results[0]["document"] == sample_documents[0]
        assert results[0]["similarity_score"] == 0.1
        assert isinstance(results[0]["document_id"], UUID)
