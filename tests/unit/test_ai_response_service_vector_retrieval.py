"""
Unit tests for AI response service with vector retrieval integration.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import UUID

from src.services.ai_response_service import AIResponseService
from src.services.vector_retrieval_service import VectorRetrievalService


class TestAIResponseServiceVectorRetrieval:
    """Test cases for AIResponseService with vector retrieval."""

    @pytest.fixture
    def ai_response_service(self):
        """Create a fresh AI response service for each test."""
        return AIResponseService()

    @pytest.fixture
    def sample_context_documents(self):
        """Create sample context documents for testing."""
        return [
            {
                "title": "Business Registration Guide",
                "document_title": "Business Registration Guide",
                "document_content": "This guide explains how to register a business in Shenzhen. It covers the required documents and procedures.",
                "document_type": "guide",
                "attribution_metadata": {"category": "business", "region": "Shenzhen"},
            },
            {
                "title": "Tax Regulations",
                "document_title": "Tax Regulations",
                "document_content": "This document contains tax regulations and requirements for businesses operating in Shenzhen.",
                "document_type": "regulation",
                "attribution_metadata": {"category": "tax", "region": "Shenzhen"},
            },
        ]

    @pytest.fixture
    def sample_ai_response(self):
        """Create sample AI response for testing."""
        return {
            "response": "You can register a business in Shenzhen by following the business registration guide. Tax information is available in the tax regulations document."
        }

    def test_find_relevant_document_with_vectors_success(
        self, ai_response_service, sample_context_documents
    ):
        """Test successful vector retrieval for document relevance."""
        sentence = "How to register a business in Shenzhen"

        # Mock the vector retrieval service
        mock_vector_service = Mock(spec=VectorRetrievalService)
        mock_vector_service.find_most_relevant_document.return_value = [
            {
                "document": sample_context_documents[0],
                "similarity_score": 0.85,
                "document_id": UUID("12345678-1234-5678-1234-567812345678"),
            }
        ]

        ai_response_service.vector_retrieval_service = mock_vector_service

        (
            document_id,
            confidence,
        ) = ai_response_service._find_relevant_document_with_vectors(
            sentence, sample_context_documents
        )

        assert document_id is not None
        assert confidence == 0.85
        mock_vector_service.find_most_relevant_document.assert_called_once_with(
            query_text=sentence,
            documents=sample_context_documents,
            top_k=1,
            similarity_threshold=0.3,
        )

    def test_find_relevant_document_with_vectors_no_results(
        self, ai_response_service, sample_context_documents
    ):
        """Test vector retrieval with no relevant documents."""
        sentence = "Unrelated topic that won't match any documents"

        # Mock the vector retrieval service to return no results
        mock_vector_service = Mock(spec=VectorRetrievalService)
        mock_vector_service.find_most_relevant_document.return_value = []

        ai_response_service.vector_retrieval_service = mock_vector_service

        (
            document_id,
            confidence,
        ) = ai_response_service._find_relevant_document_with_vectors(
            sentence, sample_context_documents
        )

        assert document_id is None
        assert confidence == 0.0

    def test_find_relevant_document_with_vectors_fallback(
        self, ai_response_service, sample_context_documents
    ):
        """Test fallback to keyword matching when vector retrieval fails."""
        sentence = "Business registration"

        # Mock the vector retrieval service to raise an exception
        mock_vector_service = Mock(spec=VectorRetrievalService)
        mock_vector_service.find_most_relevant_document.side_effect = Exception(
            "Vector service error"
        )

        ai_response_service.vector_retrieval_service = mock_vector_service

        # Mock the fallback method
        with patch.object(
            ai_response_service, "_fallback_keyword_matching"
        ) as mock_fallback:
            mock_fallback.return_value = (
                UUID("12345678-1234-5678-1234-567812345678"),
                0.5,
            )

            (
                document_id,
                confidence,
            ) = ai_response_service._find_relevant_document_with_vectors(
                sentence, sample_context_documents
            )

            mock_fallback.assert_called_once_with(sentence, sample_context_documents)
            assert document_id is not None
            assert confidence == 0.5

    def test_fallback_keyword_matching(
        self, ai_response_service, sample_context_documents
    ):
        """Test fallback keyword matching functionality."""
        sentence = "business registration"

        document_id, confidence = ai_response_service._fallback_keyword_matching(
            sentence, sample_context_documents
        )

        # Should find the business registration guide
        assert document_id is not None
        assert 0.0 <= confidence <= 1.0

    def test_fallback_keyword_matching_no_match(
        self, ai_response_service, sample_context_documents
    ):
        """Test fallback keyword matching with no matches."""
        sentence = "completely unrelated topic"

        document_id, confidence = ai_response_service._fallback_keyword_matching(
            sentence, sample_context_documents
        )

        assert document_id is None
        assert confidence == 0.0

    def test_calculate_keyword_score(
        self, ai_response_service, sample_context_documents
    ):
        """Test keyword score calculation."""
        sentence = "business registration"
        document = sample_context_documents[0]  # Business registration guide

        score = ai_response_service._calculate_keyword_score(sentence, document)

        assert 0.0 <= score <= 1.0
        # Should have some score since "business" and "registration" are in the document
        assert score > 0.0

    def test_calculate_keyword_score_no_match(
        self, ai_response_service, sample_context_documents
    ):
        """Test keyword score calculation with no matches."""
        sentence = "weather forecast"
        document = sample_context_documents[0]  # Business registration guide

        score = ai_response_service._calculate_keyword_score(sentence, document)

        assert score == 0.0

    def test_track_response_attribution_with_vectors(
        self, ai_response_service, sample_context_documents
    ):
        """Test response attribution tracking with vector retrieval."""
        response_id = UUID("12345678-1234-5678-1234-567812345678")
        response_text = (
            "You can register a business in Shenzhen. Tax regulations apply."
        )

        # Mock the vector retrieval service
        mock_vector_service = Mock(spec=VectorRetrievalService)

        # Mock different results for different sentences
        def mock_find_documents(query_text, documents, top_k, similarity_threshold):
            if "register a business" in query_text.lower():
                return [
                    {
                        "document": sample_context_documents[0],
                        "similarity_score": 0.85,
                        "document_id": UUID("11111111-1111-1111-1111-111111111111"),
                    }
                ]
            elif "tax regulations" in query_text.lower():
                return [
                    {
                        "document": sample_context_documents[1],
                        "similarity_score": 0.75,
                        "document_id": UUID("22222222-2222-2222-2222-222222222222"),
                    }
                ]
            else:
                return []

        mock_vector_service.find_most_relevant_document.side_effect = (
            mock_find_documents
        )

        ai_response_service.vector_retrieval_service = mock_vector_service

        # Mock attribution service
        mock_attribution_service = Mock()
        mock_attribution_service.add_sentence_attribution.return_value = Mock()
        ai_response_service.attribution_service = mock_attribution_service

        attributions = ai_response_service._track_response_attribution(
            response_id=response_id,
            response_text=response_text,
            context_documents=sample_context_documents,
            attribution_metadata=Mock(),
        )

        # Should have attributions for both sentences
        assert len(attributions) == 2
        assert mock_attribution_service.add_sentence_attribution.call_count == 2

    def test_track_response_attribution_no_documents(self, ai_response_service):
        """Test response attribution tracking with no context documents."""
        response_id = UUID("12345678-1234-5678-1234-567812345678")
        response_text = "Test response without documents"

        attributions = ai_response_service._track_response_attribution(
            response_id=response_id,
            response_text=response_text,
            context_documents=[],
            attribution_metadata=Mock(),
        )

        assert len(attributions) == 0

    def test_track_response_attribution_empty_response(
        self, ai_response_service, sample_context_documents
    ):
        """Test response attribution tracking with empty response."""
        response_id = UUID("12345678-1234-5678-1234-567812345678")
        response_text = ""

        attributions = ai_response_service._track_response_attribution(
            response_id=response_id,
            response_text=response_text,
            context_documents=sample_context_documents,
            attribution_metadata=Mock(),
        )

        assert len(attributions) == 0

    @patch("src.services.ai_response_service.AIService")
    @patch("src.services.ai_response_service.AttributionService")
    @patch("src.services.ai_response_service.get_vector_retrieval_service")
    def test_generate_response_with_attribution_integration(
        self,
        mock_vector_service,
        mock_attribution_service,
        mock_ai_service,
        ai_response_service,
        sample_context_documents,
    ):
        """Test full response generation with attribution integration."""
        user_query = "How to register a business in Shenzhen?"

        # Mock AI service response
        mock_ai_service.return_value.generate_government_guidance.return_value = {
            "response": "You can register a business in Shenzhen by following the business registration guide."
        }

        # Mock attribution service
        mock_attribution = Mock()
        mock_attribution.sentence_attributions = [Mock(), Mock()]
        mock_attribution.citation_list = Mock(document_sources=[])

        mock_attribution_service.return_value.start_attribution_tracking.return_value = (
            Mock()
        )
        mock_attribution_service.return_value.complete_attribution_tracking.return_value = (
            mock_attribution
        )
        mock_attribution_service.return_value.validate_attribution_consistency.return_value = (
            True
        )
        mock_attribution_service.return_value.get_performance_metrics.return_value = {}

        # Mock vector retrieval service
        mock_vector_instance = Mock()
        mock_vector_instance.find_most_relevant_document.return_value = []
        mock_vector_service.return_value = mock_vector_instance

        result = ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=sample_context_documents
        )

        assert "response" in result
        assert "attribution" in result
        assert "attribution_metrics" in result
        assert result["attribution"]["sentence_attributions"] is not None
        assert result["attribution"]["citation_list"] is not None

    def test_split_into_sentences_basic(self, ai_response_service):
        """Test basic sentence splitting."""
        text = "This is the first sentence. This is the second sentence! And this is the third?"
        sentences = ai_response_service._split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "This is the first sentence"
        assert sentences[1] == "This is the second sentence"
        assert sentences[2] == "And this is the third"

    def test_split_into_sentences_chinese(self, ai_response_service):
        """Test sentence splitting with Chinese punctuation."""
        text = "这是第一句话。这是第二句话！这是第三句话？"
        sentences = ai_response_service._split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "这是第一句话"
        assert sentences[1] == "这是第二句话"
        assert sentences[2] == "这是第三句话"

    def test_split_into_sentences_mixed(self, ai_response_service):
        """Test sentence splitting with mixed punctuation."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence。"
        sentences = ai_response_service._split_into_sentences(text)

        assert len(sentences) == 4
        assert sentences[0] == "First sentence"
        assert sentences[1] == "Second sentence"
        assert sentences[2] == "Third sentence"
        assert sentences[3] == "Fourth sentence"

    def test_split_into_sentences_empty(self, ai_response_service):
        """Test sentence splitting with empty text."""
        sentences = ai_response_service._split_into_sentences("")

        assert len(sentences) == 0

    def test_split_into_sentences_whitespace(self, ai_response_service):
        """Test sentence splitting with whitespace-only text."""
        sentences = ai_response_service._split_into_sentences("   \n\t  ")

        assert len(sentences) == 0
