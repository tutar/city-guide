"""
Unit tests for attribution service.
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime

from src.services.attribution_service import AttributionService
from src.models.attribution import (
    SentenceAttribution,
    ResponseAttribution,
    AttributionMetadata,
)


class TestAttributionService:
    """Test cases for AttributionService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = AttributionService()
        self.response_id = uuid4()

    def test_start_attribution_tracking(self):
        """Test starting attribution tracking."""
        metadata = self.service.start_attribution_tracking(self.response_id)

        assert isinstance(metadata, AttributionMetadata)
        assert metadata.tracking_start_time is not None
        assert metadata.total_sentences == 0
        assert metadata.attributed_sentences == 0
        assert metadata.tracking_end_time is None

    def test_add_sentence_attribution(self):
        """Test adding sentence attribution."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        document_source_id = uuid4()

        attribution = self.service.add_sentence_attribution(
            response_id=self.response_id,
            sentence_index=0,
            document_source_id=document_source_id,
            confidence_score=0.9,
            metadata=metadata,
        )

        assert isinstance(attribution, SentenceAttribution)
        assert attribution.response_id == self.response_id
        assert attribution.sentence_index == 0
        assert attribution.document_source_id == document_source_id
        assert attribution.confidence_score == 0.9
        assert metadata.total_sentences == 1
        assert metadata.attributed_sentences == 1

    def test_add_sentence_attribution_invalid_confidence(self):
        """Test adding sentence attribution with invalid confidence score."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        document_source_id = uuid4()

        with pytest.raises(
            ValueError, match="Confidence score must be between 0.0 and 1.0"
        ):
            self.service.add_sentence_attribution(
                response_id=self.response_id,
                sentence_index=0,
                document_source_id=document_source_id,
                confidence_score=1.5,  # Invalid confidence score
                metadata=metadata,
            )

    def test_add_sentence_attribution_negative_index(self):
        """Test adding sentence attribution with negative index."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        document_source_id = uuid4()

        with pytest.raises(ValueError, match="Sentence index must be non-negative"):
            self.service.add_sentence_attribution(
                response_id=self.response_id,
                sentence_index=-1,  # Invalid index
                document_source_id=document_source_id,
                confidence_score=0.8,
                metadata=metadata,
            )

    def test_generate_citation_list(self):
        """Test generating citation list from sentence attributions."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        doc1, doc2 = uuid4(), uuid4()

        # Add multiple attributions with some duplicate documents
        attributions = [
            self.service.add_sentence_attribution(
                self.response_id, 0, doc1, 0.9, metadata
            ),
            self.service.add_sentence_attribution(
                self.response_id, 1, doc2, 0.8, metadata
            ),
            self.service.add_sentence_attribution(
                self.response_id, 2, doc1, 0.7, metadata  # Duplicate document
            ),
        ]

        citation_list = self.service.generate_citation_list(
            self.response_id, attributions
        )

        assert citation_list.response_id == self.response_id
        assert len(citation_list.document_sources) == 2  # Should deduplicate
        assert doc1 in citation_list.document_sources
        assert doc2 in citation_list.document_sources

    def test_complete_attribution_tracking(self):
        """Test completing attribution tracking."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        doc1, doc2 = uuid4(), uuid4()

        attributions = [
            self.service.add_sentence_attribution(
                self.response_id, 0, doc1, 0.9, metadata
            ),
            self.service.add_sentence_attribution(
                self.response_id, 1, doc2, 0.8, metadata
            ),
        ]

        response_attribution = self.service.complete_attribution_tracking(
            self.response_id, attributions, metadata
        )

        assert isinstance(response_attribution, ResponseAttribution)
        assert len(response_attribution.sentence_attributions) == 2
        assert len(response_attribution.citation_list.document_sources) == 2
        assert metadata.tracking_end_time is not None
        assert metadata.performance_impact_ms is not None

    def test_get_attribution_for_response(self):
        """Test retrieving attribution for a response."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        doc_id = uuid4()

        attributions = [
            self.service.add_sentence_attribution(
                self.response_id, 0, doc_id, 0.9, metadata
            )
        ]

        self.service.complete_attribution_tracking(
            self.response_id, attributions, metadata
        )

        # Retrieve from cache
        retrieved = self.service.get_attribution_for_response(self.response_id)

        assert retrieved is not None
        assert len(retrieved.sentence_attributions) == 1
        assert retrieved.sentence_attributions[0].document_source_id == doc_id

    def test_get_attribution_for_nonexistent_response(self):
        """Test retrieving attribution for non-existent response."""
        nonexistent_id = uuid4()
        result = self.service.get_attribution_for_response(nonexistent_id)

        assert result is None

    def test_validate_attribution_consistency(self):
        """Test attribution consistency validation."""
        doc1, doc2 = uuid4(), uuid4()

        # Create a consistent attribution
        citation_list = self.service.generate_citation_list(
            self.response_id,
            [
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=0,
                    document_source_id=doc1,
                    confidence_score=0.9,
                ),
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=1,
                    document_source_id=doc2,
                    confidence_score=0.8,
                ),
            ],
        )

        response_attribution = ResponseAttribution(
            sentence_attributions=[
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=0,
                    document_source_id=doc1,
                    confidence_score=0.9,
                ),
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=1,
                    document_source_id=doc2,
                    confidence_score=0.8,
                ),
            ],
            citation_list=citation_list,
        )

        is_consistent = self.service.validate_attribution_consistency(
            response_attribution
        )

        assert is_consistent is True

    def test_validate_attribution_inconsistency(self):
        """Test attribution inconsistency detection."""
        doc1, doc2, doc3 = uuid4(), uuid4(), uuid4()

        # Create an inconsistent attribution (citation list missing doc3)
        citation_list = self.service.generate_citation_list(
            self.response_id,
            [
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=0,
                    document_source_id=doc1,
                    confidence_score=0.9,
                ),
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=1,
                    document_source_id=doc2,
                    confidence_score=0.8,
                ),
            ],
        )

        response_attribution = ResponseAttribution(
            sentence_attributions=[
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=0,
                    document_source_id=doc1,
                    confidence_score=0.9,
                ),
                SentenceAttribution(
                    response_id=self.response_id,
                    sentence_index=1,
                    document_source_id=doc3,  # doc3 not in citation list
                    confidence_score=0.8,
                ),
            ],
            citation_list=citation_list,
        )

        is_consistent = self.service.validate_attribution_consistency(
            response_attribution
        )

        assert is_consistent is False

    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        doc_id = uuid4()

        attributions = [
            self.service.add_sentence_attribution(
                self.response_id, 0, doc_id, 0.9, metadata
            )
        ]

        self.service.complete_attribution_tracking(
            self.response_id, attributions, metadata
        )

        metrics = self.service.get_performance_metrics()

        assert isinstance(metrics, dict)
        assert "avg_performance_impact_ms" in metrics
        assert "tracking_count" in metrics
        assert "attribution_coverage_rate" in metrics

    def test_clear_cache(self):
        """Test clearing attribution cache."""
        metadata = self.service.start_attribution_tracking(self.response_id)
        doc_id = uuid4()

        attributions = [
            self.service.add_sentence_attribution(
                self.response_id, 0, doc_id, 0.9, metadata
            )
        ]

        self.service.complete_attribution_tracking(
            self.response_id, attributions, metadata
        )

        # Verify attribution is cached
        assert self.service.get_attribution_for_response(self.response_id) is not None

        # Clear cache
        self.service.clear_cache()

        # Verify attribution is no longer cached
        assert self.service.get_attribution_for_response(self.response_id) is None

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Add some attributions to cache
        for i in range(3):
            response_id = uuid4()
            metadata = self.service.start_attribution_tracking(response_id)
            doc_id = uuid4()

            attributions = [
                self.service.add_sentence_attribution(
                    response_id, 0, doc_id, 0.9, metadata
                )
            ]

            self.service.complete_attribution_tracking(
                response_id, attributions, metadata
            )

        stats = self.service.get_cache_stats()

        assert stats["cached_responses"] == 3
        assert stats["total_attributions"] == 3
