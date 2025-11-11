"""
Attribution service for tracking document sources in AI responses.

This service handles sentence-level attribution tracking, citation list generation,
and attribution metadata management.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID

from src.models.attribution import (
    SentenceAttribution,
    CitationList,
    ResponseAttribution,
    AttributionMetadata,
)

logger = logging.getLogger(__name__)


class AttributionService:
    """Service for managing document source attribution in AI responses."""

    def __init__(self):
        self._attribution_cache: Dict[UUID, ResponseAttribution] = {}
        self._performance_metrics: Dict[str, float] = {}

    def start_attribution_tracking(self, response_id: UUID) -> AttributionMetadata:
        """
        Start tracking attribution for a new AI response.

        Args:
            response_id: UUID of the AI response

        Returns:
            AttributionMetadata with tracking start time
        """
        logger.info(f"Starting attribution tracking for response: {response_id}")
        metadata = AttributionMetadata(
            tracking_start_time=datetime.now(),
            total_sentences=0,
            attributed_sentences=0,
        )
        return metadata

    def add_sentence_attribution(
        self,
        response_id: UUID,
        sentence_index: int,
        document_source_id: UUID,
        confidence_score: float,
        metadata: AttributionMetadata,
    ) -> SentenceAttribution:
        """
        Add attribution for a specific sentence in the response.

        Args:
            response_id: UUID of the AI response
            sentence_index: Position of sentence in response
            document_source_id: UUID of the source document
            confidence_score: AI confidence in attribution (0.0-1.0)
            metadata: Current attribution metadata

        Returns:
            SentenceAttribution object
        """
        if not 0.0 <= confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        if sentence_index < 0:
            raise ValueError("Sentence index must be non-negative")

        attribution = SentenceAttribution(
            response_id=response_id,
            sentence_index=sentence_index,
            document_source_id=document_source_id,
            confidence_score=confidence_score,
        )

        metadata.total_sentences += 1
        metadata.attributed_sentences += 1

        logger.debug(
            f"Added attribution for sentence {sentence_index} in response {response_id} "
            f"to document {document_source_id} with confidence {confidence_score}"
        )

        return attribution

    def generate_citation_list(
        self, response_id: UUID, sentence_attributions: List[SentenceAttribution]
    ) -> CitationList:
        """
        Generate a citation list from sentence attributions.

        Args:
            response_id: UUID of the AI response
            sentence_attributions: List of sentence attributions

        Returns:
            CitationList with deduplicated document sources
        """
        # Extract unique document source IDs
        document_source_ids = list(
            {attribution.document_source_id for attribution in sentence_attributions}
        )

        citation_list = CitationList(
            response_id=response_id, document_sources=document_source_ids
        )

        logger.info(
            f"Generated citation list for response {response_id} "
            f"with {len(document_source_ids)} unique documents"
        )

        return citation_list

    def complete_attribution_tracking(
        self,
        response_id: UUID,
        sentence_attributions: List[SentenceAttribution],
        metadata: AttributionMetadata,
    ) -> ResponseAttribution:
        """
        Complete attribution tracking and generate final response attribution.

        Args:
            response_id: UUID of the AI response
            sentence_attributions: List of sentence attributions
            metadata: Attribution metadata

        Returns:
            Complete ResponseAttribution object
        """
        metadata.tracking_end_time = datetime.now()

        # Calculate performance impact
        if metadata.tracking_start_time and metadata.tracking_end_time:
            tracking_duration = (
                metadata.tracking_end_time - metadata.tracking_start_time
            ).total_seconds() * 1000  # Convert to milliseconds
            metadata.performance_impact_ms = tracking_duration

        # Generate citation list
        citation_list = self.generate_citation_list(response_id, sentence_attributions)

        # Create final response attribution
        response_attribution = ResponseAttribution(
            sentence_attributions=sentence_attributions, citation_list=citation_list
        )

        # Cache the attribution
        self._attribution_cache[response_id] = response_attribution

        # Update performance metrics
        self._update_performance_metrics(metadata)

        logger.info(
            f"Completed attribution tracking for response {response_id}: "
            f"{len(sentence_attributions)} sentences attributed, "
            f"{len(citation_list.document_sources)} unique documents, "
            f"performance impact: {metadata.performance_impact_ms:.2f}ms"
        )

        return response_attribution

    def get_attribution_for_response(
        self, response_id: UUID
    ) -> Optional[ResponseAttribution]:
        """
        Get attribution data for a specific response.

        Args:
            response_id: UUID of the AI response

        Returns:
            ResponseAttribution if found, None otherwise
        """
        return self._attribution_cache.get(response_id)

    def validate_attribution_consistency(
        self, response_attribution: ResponseAttribution
    ) -> bool:
        """
        Validate that citation list contains all referenced documents.

        Args:
            response_attribution: Response attribution to validate

        Returns:
            True if consistent, False otherwise
        """
        # Extract all document source IDs from sentence attributions
        attribution_doc_ids = {
            attribution.document_source_id
            for attribution in response_attribution.sentence_attributions
        }

        # Get document source IDs from citation list
        citation_doc_ids = set(response_attribution.citation_list.document_sources)

        # Check if citation list contains all referenced documents
        is_consistent = attribution_doc_ids.issubset(citation_doc_ids)

        if not is_consistent:
            logger.warning(
                f"Attribution consistency check failed: "
                f"citation list missing {attribution_doc_ids - citation_doc_ids}"
            )

        return is_consistent

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get current performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        return self._performance_metrics.copy()

    def _update_performance_metrics(self, metadata: AttributionMetadata) -> None:
        """Update performance metrics with new tracking data."""
        if metadata.performance_impact_ms:
            # Track average performance impact
            current_avg = self._performance_metrics.get(
                "avg_performance_impact_ms", 0.0
            )
            count = self._performance_metrics.get("tracking_count", 0)

            new_avg = ((current_avg * count) + metadata.performance_impact_ms) / (
                count + 1
            )

            self._performance_metrics["avg_performance_impact_ms"] = new_avg
            self._performance_metrics["tracking_count"] = count + 1
            self._performance_metrics[
                "last_performance_impact_ms"
            ] = metadata.performance_impact_ms

        # Track attribution coverage
        if metadata.total_sentences > 0:
            coverage_rate = metadata.attributed_sentences / metadata.total_sentences
            self._performance_metrics["attribution_coverage_rate"] = coverage_rate

    def clear_cache(self) -> None:
        """Clear the attribution cache."""
        self._attribution_cache.clear()
        logger.info("Cleared attribution cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_responses": len(self._attribution_cache),
            "total_attributions": sum(
                len(attribution.sentence_attributions)
                for attribution in self._attribution_cache.values()
            ),
        }
