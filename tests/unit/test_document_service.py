"""
Unit tests for document service.
"""

import pytest
from uuid import UUID, uuid4

from src.services.document_service import DocumentService
from src.models.document_source import (
    DocumentSource,
    DocumentSourceCreate,
    DocumentSourceUpdate,
    DocumentSourceSearchResult,
)


class TestDocumentService:
    """Test cases for DocumentService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DocumentService()

    def test_create_document_source(self):
        """Test creating a document source."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Test Document",
            location="/documents/test.pdf",
            access_info={"permission": "public"},
            attribution_metadata={"source": "test"},
        )

        document_source = self.service.create_document_source(create_data)

        assert isinstance(document_source, DocumentSource)
        assert document_source.title == "Test Document"
        assert document_source.location == "/documents/test.pdf"
        assert document_source.access_info["permission"] == "public"
        assert document_source.attribution_metadata["source"] == "test"
        assert document_source.access_state == "available"

    def test_get_document_source(self):
        """Test retrieving a document source."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Test Document",
            location="/documents/test.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)
        retrieved = self.service.get_document_source(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Document"

    def test_get_nonexistent_document_source(self):
        """Test retrieving a non-existent document source."""
        nonexistent_id = uuid4()
        result = self.service.get_document_source(nonexistent_id)

        assert result is None

    def test_update_document_source(self):
        """Test updating a document source."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Original Title",
            location="/documents/original.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)

        update_data = DocumentSourceUpdate(
            title="Updated Title",
            location="/documents/updated.pdf",
            access_info={"permission": "restricted"},
            attribution_metadata={"updated": True},
        )

        updated = self.service.update_document_source(created.id, update_data)

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.location == "/documents/updated.pdf"
        assert updated.access_info["permission"] == "restricted"
        assert updated.attribution_metadata["updated"] is True

    def test_update_nonexistent_document_source(self):
        """Test updating a non-existent document source."""
        nonexistent_id = uuid4()
        update_data = DocumentSourceUpdate(title="New Title")

        result = self.service.update_document_source(nonexistent_id, update_data)

        assert result is None

    def test_verify_document_access_available(self):
        """Test verifying access for an available document."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Available Document",
            location="/documents/available.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)
        access_info = self.service.verify_document_access(created.id)

        assert access_info["accessible"] is True
        assert access_info["access_state"] == "available"
        assert access_info["permission"] == "public"
        assert access_info["title"] == "Available Document"

    def test_verify_document_access_unavailable(self):
        """Test verifying access for an unavailable document."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Unavailable Document",
            location="/documents/unavailable.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)

        # Update to unavailable state
        update_data = DocumentSourceUpdate(access_state="unavailable")
        self.service.update_document_source(created.id, update_data)

        access_info = self.service.verify_document_access(created.id)

        assert access_info["accessible"] is False
        assert access_info["access_state"] == "unavailable"

    def test_verify_nonexistent_document_access(self):
        """Test verifying access for a non-existent document."""
        nonexistent_id = uuid4()
        access_info = self.service.verify_document_access(nonexistent_id)

        assert access_info["accessible"] is False
        assert access_info["reason"] == "Document not found"
        assert access_info["access_state"] == "unavailable"

    def test_handle_document_access_failure(self):
        """Test handling document access failure."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Problematic Document",
            location="/documents/problem.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)

        failure_info = self.service.handle_document_access_failure(
            created.id, "Network timeout"
        )

        assert failure_info["document_id"] == str(created.id)
        assert failure_info["accessible"] is False
        assert failure_info["failure_reason"] == "Network timeout"
        assert failure_info["graceful_degradation"] is True
        assert failure_info["preserved_metadata"]["title"] == "Problematic Document"

    def test_handle_nonexistent_document_access_failure(self):
        """Test handling access failure for non-existent document."""
        nonexistent_id = uuid4()

        failure_info = self.service.handle_document_access_failure(
            nonexistent_id, "Document not found"
        )

        assert failure_info["document_id"] == str(nonexistent_id)
        assert failure_info["accessible"] is False
        assert failure_info["failure_reason"] == "Document not found"
        assert failure_info["graceful_degradation"] is True
        assert failure_info["preserved_metadata"]["title"] == "Unknown"

    def test_search_document_sources(self):
        """Test searching document sources."""
        # Create test documents
        documents = [
            DocumentSourceCreate(
                document_embedding_id=uuid4(),
                title="Python Programming Guide",
                location="/documents/python.pdf",
                access_info={"permission": "public"},
                attribution_metadata={"category": "programming"},
            ),
            DocumentSourceCreate(
                document_embedding_id=uuid4(),
                title="JavaScript Tutorial",
                location="/documents/javascript.pdf",
                access_info={"permission": "public"},
                attribution_metadata={"category": "programming"},
            ),
            DocumentSourceCreate(
                document_embedding_id=uuid4(),
                title="Data Science Handbook",
                location="/documents/datascience.pdf",
                access_info={"permission": "public"},
                attribution_metadata={"category": "data"},
            ),
        ]

        for doc in documents:
            self.service.create_document_source(doc)

        # Search for programming documents
        results = self.service.search_document_sources("programming")

        assert len(results) == 2
        assert all(isinstance(result, DocumentSourceSearchResult) for result in results)
        assert all(
            "programming" in result.document_source.title.lower()
            or result.document_source.attribution_metadata.get("category")
            == "programming"
            for result in results
        )

    def test_search_document_sources_empty_query(self):
        """Test searching with empty query."""
        results = self.service.search_document_sources("")

        assert len(results) == 0

    def test_get_document_access_logs(self):
        """Test getting document access logs."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Logged Document",
            location="/documents/logged.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)

        # Generate some access logs
        self.service.get_document_source(created.id)
        self.service.verify_document_access(created.id)

        logs = self.service.get_document_access_logs(document_id=created.id)

        assert len(logs) >= 2
        assert all(log["document_id"] == created.id for log in logs)
        assert any(log["action"] == "read" for log in logs)
        assert any(log["action"] == "verify" for log in logs)

    def test_get_service_stats(self):
        """Test getting service statistics."""
        # Create some documents
        for i in range(3):
            create_data = DocumentSourceCreate(
                document_embedding_id=uuid4(),
                title=f"Document {i}",
                location=f"/documents/doc{i}.pdf",
                access_info={"permission": "public"},
            )
            self.service.create_document_source(create_data)

        stats = self.service.get_service_stats()

        assert stats["total_documents"] == 3
        assert stats["accessible_documents"] == 3
        assert stats["unavailable_documents"] == 0
        assert (
            stats["access_log_entries"] >= 0
        )  # May be 0 if no access logging during creation
        assert "cache_hit_rate" in stats

    def test_clear_cache(self):
        """Test clearing document cache."""
        create_data = DocumentSourceCreate(
            document_embedding_id=uuid4(),
            title="Cached Document",
            location="/documents/cached.pdf",
            access_info={"permission": "public"},
        )

        created = self.service.create_document_source(create_data)

        # Verify document is cached
        assert self.service.get_document_source(created.id) is not None

        # Clear cache
        self.service.clear_cache()

        # Verify document is no longer cached
        assert self.service.get_document_source(created.id) is None

    def test_cleanup_old_logs(self):
        """Test cleaning up old access logs."""
        # Create some access logs
        for i in range(5):
            create_data = DocumentSourceCreate(
                document_embedding_id=uuid4(),
                title=f"Log Document {i}",
                location=f"/documents/log{i}.pdf",
                access_info={"permission": "public"},
            )
            created = self.service.create_document_source(create_data)
            self.service.get_document_source(created.id)

        initial_log_count = len(self.service.get_document_access_logs())

        # Clean up logs (simulate very old logs)
        removed_count = self.service.cleanup_old_logs(max_age_hours=0)

        final_log_count = len(self.service.get_document_access_logs())

        assert removed_count >= 0
        assert final_log_count <= initial_log_count
