"""
Unit tests for the relevance service.
"""

import pytest
from uuid import uuid4

from src.services.relevance_service import RelevanceService
from src.models.document_source import DocumentSource, DocumentSourceCreate


class TestRelevanceService:
    """Test cases for the RelevanceService class."""

    @pytest.fixture
    def relevance_service(self):
        """Create a fresh relevance service for each test."""
        return RelevanceService()

    @pytest.fixture
    def sample_document_source(self):
        """Create a sample document source for testing."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Shenzhen Business Registration Guide",
            location="/documents/business-registration",
            access_info={"permission": "public"},
            attribution_metadata={
                "document_type": "guide",
                "category": "business",
                "region": "Shenzhen",
            },
        )
        return DocumentSource(
            document_embedding_id=create_data.document_embedding_id,
            title=create_data.title,
            location=create_data.location,
            access_info=create_data.access_info,
            attribution_metadata=create_data.attribution_metadata,
        )

    def test_calculate_relevance_score_basic(
        self, relevance_service, sample_document_source
    ):
        """Test basic relevance score calculation."""
        user_query = "How to register a business in Shenzhen?"
        ai_response = "You can register a business in Shenzhen using the business registration guide."

        result = relevance_service.calculate_relevance_score(
            document_source=sample_document_source,
            user_query=user_query,
            ai_response=ai_response,
        )

        assert "relevance_score" in result
        assert "confidence_level" in result
        assert "explanation" in result
        assert "relevance_factors" in result
        assert result["document_id"] == str(sample_document_source.id)
        assert result["title"] == sample_document_source.title
        assert 0.0 <= result["relevance_score"] <= 1.0
        assert result["confidence_level"] in ["high", "medium", "low", "very_low"]

    def test_calculate_relevance_score_with_context(
        self, relevance_service, sample_document_source
    ):
        """Test relevance score calculation with context metadata."""
        user_query = "Business registration"
        ai_response = "The business registration process is documented in our guides."
        context_metadata = {"document_type": "guide", "category": "business"}

        result = relevance_service.calculate_relevance_score(
            document_source=sample_document_source,
            user_query=user_query,
            ai_response=ai_response,
            context_metadata=context_metadata,
        )

        assert "relevance_score" in result
        assert "confidence_level" in result
        assert "relevance_factors" in result
        assert "metadata_relevance" in result["relevance_factors"]

    def test_explain_multiple_sources(self, relevance_service, sample_document_source):
        """Test relevance explanation for multiple sources."""
        # Create another document source
        create_data2 = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Shenzhen Tax Regulations",
            location="/documents/tax-regulations",
            access_info={"permission": "public"},
            attribution_metadata={
                "document_type": "regulation",
                "category": "tax",
                "region": "Shenzhen",
            },
        )
        doc_source2 = DocumentSource(
            document_embedding_id=create_data2.document_embedding_id,
            title=create_data2.title,
            location=create_data2.location,
            access_info=create_data2.access_info,
            attribution_metadata=create_data2.attribution_metadata,
        )

        user_query = "Business registration in Shenzhen"
        ai_response = "For business registration, refer to the business guide. Tax information is in tax regulations."

        explanations = relevance_service.explain_multiple_sources(
            document_sources=[sample_document_source, doc_source2],
            user_query=user_query,
            ai_response=ai_response,
        )

        assert len(explanations) == 2
        assert all("relevance_score" in exp for exp in explanations)
        assert all("confidence_level" in exp for exp in explanations)

        # Should be sorted by relevance score (descending)
        scores = [exp["relevance_score"] for exp in explanations]
        assert scores == sorted(scores, reverse=True)

    def test_get_relevance_statistics(self, relevance_service, sample_document_source):
        """Test relevance statistics generation."""
        # Create explanations
        explanations = [
            {
                "document_id": str(sample_document_source.id),
                "title": sample_document_source.title,
                "relevance_score": 0.8,
                "confidence_level": "high",
                "explanation": "Test explanation",
                "relevance_factors": {},
                "accessibility": True,
                "access_state": "available",
            },
            {
                "document_id": "test-id-2",
                "title": "Another Document",
                "relevance_score": 0.5,
                "confidence_level": "medium",
                "explanation": "Test explanation 2",
                "relevance_factors": {},
                "accessibility": True,
                "access_state": "available",
            },
        ]

        stats = relevance_service.get_relevance_statistics(explanations)

        assert stats["total_sources"] == 2
        assert stats["average_relevance"] == 0.65
        assert stats["max_relevance"] == 0.8
        assert stats["min_relevance"] == 0.5
        assert "confidence_distribution" in stats
        assert "score_distribution" in stats
        assert "top_source" in stats

    def test_get_relevance_statistics_empty(self, relevance_service):
        """Test relevance statistics with empty explanations."""
        stats = relevance_service.get_relevance_statistics([])

        assert stats["total_sources"] == 0
        assert stats["average_relevance"] == 0.0
        assert "confidence_distribution" in stats
        assert "score_distribution" in stats

    def test_clear_cache(self, relevance_service, sample_document_source):
        """Test cache clearing functionality."""
        # Add some data to cache
        user_query = "Test query"
        ai_response = "Test response"

        result = relevance_service.calculate_relevance_score(
            document_source=sample_document_source,
            user_query=user_query,
            ai_response=ai_response,
        )

        # Cache should have an entry
        cache_key = f"{sample_document_source.id}_{user_query[:50]}"
        assert cache_key in relevance_service._relevance_cache

        # Clear cache
        relevance_service.clear_cache()

        # Cache should be empty
        assert len(relevance_service._relevance_cache) == 0

    def test_fallback_relevance(self, relevance_service, sample_document_source):
        """Test fallback relevance when calculation fails."""
        # This test ensures that even if there's an error in calculation,
        # we get a fallback result

        # Mock a scenario that would cause calculation to fail
        # (e.g., by passing invalid data that would cause an exception)
        result = relevance_service._get_fallback_relevance(sample_document_source)

        assert result["relevance_score"] == 0.3
        assert result["confidence_level"] == "low"
        assert "explanation" in result
        assert "relevance_factors" in result
        assert result["document_id"] == str(sample_document_source.id)
        assert result["title"] == sample_document_source.title

    def test_relevance_factors_structure(
        self, relevance_service, sample_document_source
    ):
        """Test that relevance factors have the expected structure."""
        user_query = "Shenzhen business"
        ai_response = "Business registration in Shenzhen follows specific procedures."

        result = relevance_service.calculate_relevance_score(
            document_source=sample_document_source,
            user_query=user_query,
            ai_response=ai_response,
        )

        factors = result["relevance_factors"]

        assert "query_relevance" in factors
        assert "response_relevance" in factors
        assert "metadata_relevance" in factors

        for factor_name, factor_data in factors.items():
            assert "score" in factor_data
            assert "factors" in factor_data
            assert "explanation" in factor_data
            assert 0.0 <= factor_data["score"] <= 1.0
            assert isinstance(factor_data["factors"], list)
            assert isinstance(factor_data["explanation"], str)
