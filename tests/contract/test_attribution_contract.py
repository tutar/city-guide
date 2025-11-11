"""
Contract tests for enhanced response format with attribution.

These tests verify that the API response format conforms to the expected
contract, ensuring backward compatibility and consistent data structure.
"""

import pytest
from uuid import UUID
from typing import Dict, Any, List

from src.api.conversation import SendMessageResponse, AttributionData


class TestAttributionContract:
    """Contract tests for attribution-enhanced response format."""

    def test_send_message_response_contract(self):
        """Test SendMessageResponse contract with attribution."""
        # Valid response data
        response_data = {
            "response": "This is a test response with attribution.",
            "navigation_options": [{"label": "Next Step", "action_type": "general"}],
            "conversation_history": [
                {
                    "role": "user",
                    "content": "Test message",
                    "timestamp": "2024-01-01T00:00:00",
                }
            ],
            "attribution": {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_source_id": "12345678-1234-1234-1234-123456789012",
                        "confidence_score": 0.85,
                    }
                ],
                "citation_list": {
                    "document_sources": [
                        {
                            "id": "12345678-1234-1234-1234-123456789012",
                            "title": "Test Document",
                            "location": "/documents/test.pdf",
                            "access_info": {"permission": "public"},
                        }
                    ]
                },
                "fallback_mode": False,
            },
        }

        # Should validate without errors
        response = SendMessageResponse(**response_data)
        assert response.response == response_data["response"]
        assert response.attribution is not None

    def test_attribution_data_contract_minimal(self):
        """Test AttributionData contract with minimal data."""
        minimal_data = {
            "sentence_attributions": [],
            "citation_list": {},
            "fallback_mode": False,
        }

        attribution = AttributionData(**minimal_data)
        assert attribution.sentence_attributions == []
        assert attribution.citation_list == {}
        assert attribution.fallback_mode is False

    def test_attribution_data_contract_full(self):
        """Test AttributionData contract with full data."""
        full_data = {
            "sentence_attributions": [
                {
                    "sentence_index": 0,
                    "document_source_id": "12345678-1234-1234-1234-123456789012",
                    "confidence_score": 0.9,
                },
                {
                    "sentence_index": 1,
                    "document_source_id": "87654321-4321-4321-4321-210987654321",
                    "confidence_score": 0.7,
                },
            ],
            "citation_list": {
                "document_sources": [
                    {
                        "id": "12345678-1234-1234-1234-123456789012",
                        "title": "Document One",
                        "location": "/documents/doc1.pdf",
                        "access_info": {"permission": "public", "restricted": False},
                    },
                    {
                        "id": "87654321-4321-4321-4321-210987654321",
                        "title": "Document Two",
                        "location": "/documents/doc2.pdf",
                        "access_info": {
                            "permission": "restricted",
                            "reason": "confidential",
                        },
                    },
                ]
            },
            "fallback_mode": False,
        }

        attribution = AttributionData(**full_data)
        assert len(attribution.sentence_attributions) == 2
        assert len(attribution.citation_list["document_sources"]) == 2
        assert attribution.fallback_mode is False

    def test_send_message_response_backward_compatibility(self):
        """Test backward compatibility - response without attribution."""
        legacy_response_data = {
            "response": "This is a legacy response without attribution.",
            "navigation_options": [],
            "conversation_history": [],
            "usage": {"tokens": 100, "cost": 0.01}
            # No attribution field
        }

        # Should still validate (attribution is optional)
        response = SendMessageResponse(**legacy_response_data)
        assert response.response == legacy_response_data["response"]
        assert response.attribution is None

    def test_sentence_attribution_contract(self):
        """Test sentence attribution data contract."""
        valid_attribution = {
            "sentence_index": 0,
            "document_source_id": "12345678-1234-1234-1234-123456789012",
            "confidence_score": 0.85,
        }

        # Should be valid in AttributionData context
        attribution_data = AttributionData(
            sentence_attributions=[valid_attribution],
            citation_list={},
            fallback_mode=False,
        )

        assert len(attribution_data.sentence_attributions) == 1
        attribution = attribution_data.sentence_attributions[0]
        assert attribution["sentence_index"] == 0
        assert (
            attribution["document_source_id"] == "12345678-1234-1234-1234-123456789012"
        )
        assert attribution["confidence_score"] == 0.85

    def test_document_source_contract(self):
        """Test document source data contract."""
        valid_document_source = {
            "id": "12345678-1234-1234-1234-123456789012",
            "title": "Test Document",
            "location": "/documents/test.pdf",
            "access_info": {
                "permission": "public",
                "restricted": False,
                "notes": "Available to all users",
            },
        }

        # Should be valid in citation list context
        citation_list = {"document_sources": [valid_document_source]}

        attribution_data = AttributionData(
            sentence_attributions=[], citation_list=citation_list, fallback_mode=False
        )

        assert len(attribution_data.citation_list["document_sources"]) == 1
        doc_source = attribution_data.citation_list["document_sources"][0]
        assert doc_source["id"] == "12345678-1234-1234-1234-123456789012"
        assert doc_source["title"] == "Test Document"
        assert doc_source["location"] == "/documents/test.pdf"
        assert doc_source["access_info"]["permission"] == "public"

    def test_fallback_mode_contract(self):
        """Test fallback mode contract."""
        # Test with fallback mode enabled
        fallback_data = {
            "sentence_attributions": [],
            "citation_list": {"document_sources": []},
            "fallback_mode": True,
        }

        attribution = AttributionData(**fallback_data)
        assert attribution.fallback_mode is True
        assert attribution.sentence_attributions == []
        assert attribution.citation_list["document_sources"] == []

    def test_confidence_score_validation(self):
        """Test confidence score validation in sentence attributions."""
        # Valid confidence scores
        valid_scores = [0.0, 0.5, 0.99, 1.0]

        for score in valid_scores:
            attribution_data = {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_source_id": "12345678-1234-1234-1234-123456789012",
                        "confidence_score": score,
                    }
                ],
                "citation_list": {},
                "fallback_mode": False,
            }

            # Should validate without errors
            attribution = AttributionData(**attribution_data)
            assert attribution.sentence_attributions[0]["confidence_score"] == score

    def test_uuid_format_validation(self):
        """Test UUID format validation in document source IDs."""
        valid_uuids = [
            "12345678-1234-1234-1234-123456789012",
            "87654321-4321-4321-4321-210987654321",
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        ]

        for uuid_str in valid_uuids:
            attribution_data = {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_source_id": uuid_str,
                        "confidence_score": 0.8,
                    }
                ],
                "citation_list": {
                    "document_sources": [
                        {
                            "id": uuid_str,
                            "title": "Test Document",
                            "location": "/documents/test.pdf",
                            "access_info": {"permission": "public"},
                        }
                    ]
                },
                "fallback_mode": False,
            }

            # Should validate without errors
            attribution = AttributionData(**attribution_data)
            assert (
                attribution.sentence_attributions[0]["document_source_id"] == uuid_str
            )
            assert attribution.citation_list["document_sources"][0]["id"] == uuid_str

    def test_optional_fields_contract(self):
        """Test that optional fields are handled correctly."""
        # Response without optional fields
        minimal_response = {
            "response": "Minimal response",
            "navigation_options": [],
            "conversation_history": []
            # No usage, no attribution
        }

        response = SendMessageResponse(**minimal_response)
        assert response.response == "Minimal response"
        assert response.navigation_options == []
        assert response.conversation_history == []
        assert response.usage is None
        assert response.attribution is None

    def test_access_info_flexibility(self):
        """Test that access_info can contain flexible key-value pairs."""
        flexible_access_info = {
            "permission": "restricted",
            "reason": "confidential",
            "access_level": "internal",
            "expires": "2024-12-31",
            "custom_field": "custom_value",
        }

        attribution_data = {
            "sentence_attributions": [],
            "citation_list": {
                "document_sources": [
                    {
                        "id": "12345678-1234-1234-1234-123456789012",
                        "title": "Restricted Document",
                        "location": "/documents/restricted.pdf",
                        "access_info": flexible_access_info,
                    }
                ]
            },
            "fallback_mode": False,
        }

        attribution = AttributionData(**attribution_data)
        doc_source = attribution.citation_list["document_sources"][0]
        assert doc_source["access_info"]["permission"] == "restricted"
        assert doc_source["access_info"]["reason"] == "confidential"
        assert doc_source["access_info"]["custom_field"] == "custom_value"

    def test_response_with_mixed_data_types(self):
        """Test response with mixed data types in optional fields."""
        mixed_response = {
            "response": "Response with mixed data",
            "navigation_options": [
                {"label": "Action 1", "action_type": "general", "priority": 1},
                {
                    "label": "Action 2",
                    "action_type": "external",
                    "url": "https://example.com",
                },
            ],
            "conversation_history": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"source": "web"},
                },
                {
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": "2024-01-01T00:00:01",
                },
            ],
            "usage": {"tokens": 150, "cost": 0.015, "model": "gpt-4"},
            "attribution": {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_source_id": "12345678-1234-1234-1234-123456789012",
                        "confidence_score": 0.92,
                        "metadata": {"extracted_at": "2024-01-01T00:00:00"},
                    }
                ],
                "citation_list": {
                    "document_sources": [
                        {
                            "id": "12345678-1234-1234-1234-123456789012",
                            "title": "Mixed Data Document",
                            "location": "/documents/mixed.pdf",
                            "access_info": {
                                "permission": "public",
                                "tags": ["official", "guide"],
                            },
                            "metadata": {"created": "2024-01-01", "version": "1.0"},
                        }
                    ]
                },
                "fallback_mode": False,
                "performance_metrics": {"processing_time_ms": 150},
            },
        }

        # Should validate all mixed data types
        response = SendMessageResponse(**mixed_response)
        assert response.response == "Response with mixed data"
        assert len(response.navigation_options) == 2
        assert len(response.conversation_history) == 2
        assert response.usage["tokens"] == 150
        assert response.attribution is not None
        assert len(response.attribution.sentence_attributions) == 1
        assert len(response.attribution.citation_list["document_sources"]) == 1

    def test_error_scenarios(self):
        """Test error scenarios and edge cases."""
        # Test with invalid confidence score
        with pytest.raises(ValueError):
            # Confidence score outside valid range
            invalid_data = {
                "sentence_attributions": [
                    {
                        "sentence_index": 0,
                        "document_source_id": "12345678-1234-1234-1234-123456789012",
                        "confidence_score": 1.5,  # Invalid: > 1.0
                    }
                ],
                "citation_list": {},
                "fallback_mode": False,
            }
            AttributionData(**invalid_data)

        # Test with negative sentence index
        with pytest.raises(ValueError):
            invalid_data = {
                "sentence_attributions": [
                    {
                        "sentence_index": -1,  # Invalid: negative index
                        "document_source_id": "12345678-1234-1234-1234-123456789012",
                        "confidence_score": 0.8,
                    }
                ],
                "citation_list": {},
                "fallback_mode": False,
            }
            AttributionData(**invalid_data)
