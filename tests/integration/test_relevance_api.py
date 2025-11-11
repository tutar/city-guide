"""
Integration tests for the relevance API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from src.models.document_source import DocumentSourceCreate
from src.services.document_service import DocumentService


class TestRelevanceAPI:
    """Test cases for the relevance API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_document_ids(self):
        """Create sample documents and return their IDs."""
        document_service = DocumentService()

        # Create sample documents
        doc1_data = DocumentSourceCreate(
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

        doc2_data = DocumentSourceCreate(
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

        doc1 = document_service.create_document_source(doc1_data)
        doc2 = document_service.create_document_source(doc2_data)

        return [str(doc1.id), str(doc2.id)]

    def test_explain_source_relevance_success(self, client, sample_document_ids):
        """Test successful relevance explanation."""
        request_data = {
            "document_ids": sample_document_ids,
            "user_query": "How to register a business in Shenzhen?",
            "ai_response": "You can register a business in Shenzhen using the business registration guide. Tax regulations may also be relevant.",
        }

        response = client.post("/api/relevance/explain", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "explanations" in data
        assert "statistics" in data
        assert len(data["explanations"]) == 2

        # Check structure of explanations
        for explanation in data["explanations"]:
            assert "document_id" in explanation
            assert "title" in explanation
            assert "relevance_score" in explanation
            assert "confidence_level" in explanation
            assert "explanation" in explanation
            assert "relevance_factors" in explanation
            assert "accessibility" in explanation
            assert "access_state" in explanation

            # Check relevance factors structure
            factors = explanation["relevance_factors"]
            assert "query_relevance" in factors
            assert "response_relevance" in factors
            assert "metadata_relevance" in factors

        # Check statistics
        stats = data["statistics"]
        assert "total_sources" in stats
        assert "average_relevance" in stats
        assert "max_relevance" in stats
        assert "min_relevance" in stats

    def test_explain_source_relevance_with_context(self, client, sample_document_ids):
        """Test relevance explanation with context metadata."""
        request_data = {
            "document_ids": sample_document_ids,
            "user_query": "Business registration",
            "ai_response": "Business registration process is documented.",
            "context_metadata": {"document_type": "guide", "category": "business"},
        }

        response = client.post("/api/relevance/explain", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert len(data["explanations"]) == 2
        assert data["statistics"]["total_sources"] == 2

    def test_explain_source_relevance_no_valid_documents(self, client):
        """Test relevance explanation with no valid documents."""
        request_data = {
            "document_ids": ["invalid-uuid-1", "invalid-uuid-2"],
            "user_query": "Test query",
            "ai_response": "Test response",
        }

        response = client.post("/api/relevance/explain", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "No valid document IDs provided" in data["detail"]

    def test_explain_source_relevance_no_documents_found(self, client):
        """Test relevance explanation with valid UUIDs but no documents."""
        valid_but_nonexistent_uuids = [str(uuid4()), str(uuid4())]

        request_data = {
            "document_ids": valid_but_nonexistent_uuids,
            "user_query": "Test query",
            "ai_response": "Test response",
        }

        response = client.post("/api/relevance/explain", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "No valid document sources found" in data["detail"]

    def test_explain_single_document_relevance_success(
        self, client, sample_document_ids
    ):
        """Test successful single document relevance explanation."""
        document_id = sample_document_ids[0]

        request_data = {
            "document_id": document_id,
            "user_query": "How to register a business?",
            "ai_response": "Business registration guide provides the necessary information.",
        }

        response = client.post("/api/relevance/explain/single", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["document_id"] == document_id
        assert "title" in data
        assert "relevance_score" in data
        assert "confidence_level" in data
        assert "explanation" in data
        assert "relevance_factors" in data

    def test_explain_single_document_relevance_invalid_id(self, client):
        """Test single document relevance with invalid document ID."""
        request_data = {
            "document_id": "invalid-uuid",
            "user_query": "Test query",
            "ai_response": "Test response",
        }

        response = client.post("/api/relevance/explain/single", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "Invalid document ID format" in data["detail"]

    def test_explain_single_document_relevance_not_found(self, client):
        """Test single document relevance with non-existent document."""
        non_existent_uuid = str(uuid4())

        request_data = {
            "document_id": non_existent_uuid,
            "user_query": "Test query",
            "ai_response": "Test response",
        }

        response = client.post("/api/relevance/explain/single", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Document not found" in data["detail"]

    def test_get_relevance_statistics(self, client):
        """Test getting relevance service statistics."""
        response = client.get("/api/relevance/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "cache_size" in data
        assert "service_ready" in data
        assert "calculation_method" in data
        assert "factors_considered" in data

    def test_clear_relevance_cache(self, client):
        """Test clearing the relevance cache."""
        response = client.post("/api/relevance/cache/clear")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "Relevance cache cleared successfully" in data["message"]
