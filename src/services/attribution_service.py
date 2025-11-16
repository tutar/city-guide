"""
Attribution service for tracking document sources in AI responses.

This service handles sentence-level attribution tracking, citation list generation,
and attribution metadata management.
"""

import logging
from datetime import datetime
from typing import Any, List, Dict, Optional
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
        document: Dict[str, Any],
        confidence_score: float,
        metadata: AttributionMetadata,
    ) -> SentenceAttribution:
        """
        Add attribution for a specific sentence in the response.

        Args:
            response_id: UUID of the AI response
            sentence_index: Position of sentence in response
            document: Source document dictionary
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
            document_id=document.get("document_id"),
            title=document.get("document_title", "Unknown Title"),
            document=document,
            confidence_score=confidence_score,
        )

        metadata.total_sentences += 1
        metadata.attributed_sentences += 1
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
        document_ids = list(
            {attribution.document_id for attribution in sentence_attributions}
        )

        citation_list = CitationList(
            response_id=response_id, document_sources=document_ids
        )

        logger.info(
            f"Generated citation list for response {response_id} "
            f"with {len(document_ids)} unique documents"
        )

        return citation_list

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
            attribution.document_id
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
