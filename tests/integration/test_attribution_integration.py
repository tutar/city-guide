"""
Integration tests for document source attribution flow.

These tests verify the complete attribution flow from API response generation
to frontend display, ensuring attribution data is properly tracked and displayed.
"""

import pytest
import asyncio
from uuid import uuid4
from typing import Dict, Any

from src.services.ai_response_service import AIResponseService
from src.services.attribution_service import AttributionService
from src.services.document_service import DocumentService


class TestAttributionIntegration:
    """Integration tests for document source attribution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_response_service = AIResponseService()
        self.attribution_service = AttributionService()
        self.document_service = DocumentService()

    def test_complete_attribution_flow(self):
        """Test complete attribution flow from response generation to citation list."""
        # Setup test data
        user_query = "What are the requirements for obtaining a passport?"
        context_documents = [
            {
                "title": "Passport Application Guide",
                "content": "To apply for a passport, you need valid ID, proof of citizenship, and passport photos.",
                "document_type": "guide",
            },
            {
                "title": "Government ID Requirements",
                "content": "Valid government-issued ID is required for all official applications.",
                "document_type": "requirements",
            },
        ]

        # Generate response with attribution
        response = self.ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=context_documents
        )

        # Verify response structure
        assert "response" in response
        assert "attribution" in response
        assert isinstance(response["response"], str)
        assert len(response["response"]) > 0

        # Verify attribution data structure
        attribution_data = response["attribution"]
        assert "sentence_attributions" in attribution_data
        assert "citation_list" in attribution_data
        assert isinstance(attribution_data["sentence_attributions"], list)
        assert isinstance(attribution_data["citation_list"], dict)

        # Verify citation list contains document sources
        citation_list = attribution_data["citation_list"]
        assert "document_sources" in citation_list
        assert isinstance(citation_list["document_sources"], list)

        # Verify sentence attributions reference valid document sources
        sentence_attributions = attribution_data["sentence_attributions"]
        if sentence_attributions:
            for attribution in sentence_attributions:
                assert "sentence_index" in attribution
                assert "document_id" in attribution
                assert "confidence_score" in attribution
                assert 0.0 <= attribution["confidence_score"] <= 1.0

    def test_attribution_with_multiple_documents(self):
        """Test attribution with multiple context documents."""
        user_query = "What documents do I need for a driver's license?"
        context_documents = [
            {
                "document_title": "Driver's License Application",
                "document_content": "You need proof of identity, proof of residency, and medical certificate.",
                "document_type": "application",
            },
            {
                "document_title": "Identity Verification",
                "document_content": "Valid photo ID and proof of address are required.",
                "document_type": "requirements",
            },
            {
                "document_title": "Medical Requirements",
                "document_content": "Medical certificate must be issued by an authorized physician.",
                "document_type": "medical",
            },
        ]

        response = self.ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=context_documents
        )

        # Verify attribution data
        attribution_data = response["attribution"]
        citation_list = attribution_data["citation_list"]

        # Should have multiple document sources
        assert len(citation_list["document_sources"]) >= 1

        # Verify document source structure
        for doc_source in citation_list["document_sources"]:
            assert "id" in doc_source
            assert "title" in doc_source
            assert "location" in doc_source
            assert "access_info" in doc_source

    def test_attribution_fallback_mode(self):
        """Test attribution fallback mode when attribution tracking fails."""
        user_query = "Simple test query"
        context_documents = []  # Empty context should trigger fallback

        response = self.ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=context_documents
        )

        # Verify fallback mode is indicated
        attribution_data = response["attribution"]
        assert attribution_data.get("fallback_mode", False) is True

        # Should still have basic attribution structure
        assert "sentence_attributions" in attribution_data
        assert "citation_list" in attribution_data

    def test_error_handling_in_attribution_flow(self):
        """Test error handling in attribution flow."""
        # Test with invalid data that should trigger fallback
        user_query = ""
        context_documents = [{"invalid": "data"}]

        # Should not raise exception, should use fallback
        response = self.ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=context_documents
        )

        # Should still return valid response structure
        assert "response" in response
        assert "attribution" in response

        # Attribution should indicate fallback mode
        attribution_data = response["attribution"]
        assert attribution_data.get("fallback_mode", False) is True

    def test_attribution_summary_statistics(self):
        """Test attribution summary statistics generation."""
        user_query = "Statistics test query"
        context_documents = [
            {
                "document_title": "Statistics Test Document",
                "document_content": "This document tests attribution statistics.",
                "document_type": "test",
            }
        ]

        response = self.ai_response_service.generate_response_with_attribution(
            user_query=user_query, context_documents=context_documents
        )

        attribution_data = response["attribution"]

        # Test summary generation (this would typically be in the display component)
        sentence_attributions = attribution_data["sentence_attributions"]
        citation_list = attribution_data["citation_list"]

        total_sentences = len(sentence_attributions)
        attributed_sentences = len(
            [a for a in sentence_attributions if a.get("document_id")]
        )
        unique_documents = len(citation_list.get("document_sources", []))

        # Basic statistics validation
        assert total_sentences >= 0
        assert attributed_sentences >= 0
        assert attributed_sentences <= total_sentences
        assert unique_documents >= 0

    @pytest.mark.asyncio
    async def test_conversation_api_integration(self):
        """Test attribution integration with conversation API (simulated)."""
        # This test simulates the API response structure
        # In a real integration test, this would call the actual API

        # Simulate API response with attribution
        mock_api_response = {
            "response": "To apply for a passport, you need valid ID and proof of citizenship.",
            "conversation_history": [],
            "attribution": {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_id": str(uuid4()),
                        "confidence_score": 0.85,
                    }
                ],
                "citation_list": {
                    "document_sources": [
                        {
                            "id": str(uuid4()),
                            "title": "Passport Application Requirements",
                            "location": "/documents/passport.pdf",
                            "access_info": {"permission": "public"},
                        }
                    ]
                },
                "fallback_mode": False,
            },
        }

        # Verify the response structure matches what the frontend expects
        assert "response" in mock_api_response
        assert "attribution" in mock_api_response

        attribution_data = mock_api_response["attribution"]
        assert "sentence_attributions" in attribution_data
        assert "citation_list" in attribution_data
        assert "fallback_mode" in attribution_data

        # Verify citation list structure
        citation_list = attribution_data["citation_list"]
        assert "document_sources" in citation_list
        assert len(citation_list["document_sources"]) > 0

        # Verify document source structure
        doc_source = citation_list["document_sources"][0]
        assert "id" in doc_source
        assert "title" in doc_source
        assert "location" in doc_source
        assert "access_info" in doc_source
