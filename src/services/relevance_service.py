"""
Source relevance explanation service for AI responses.

This service provides explanations for why specific document sources were cited
in AI responses, including relevance scoring and confidence metrics.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID

from src.models.document_source import DocumentSource

logger = logging.getLogger(__name__)


class RelevanceService:
    """Service for calculating and explaining source relevance."""

    def __init__(self):
        self._relevance_cache: Dict[str, Dict[str, Any]] = {}

    def calculate_relevance_score(
        self,
        document_source: DocumentSource,
        user_query: str,
        ai_response: str,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate relevance score for a document source.

        Args:
            document_source: The document source being evaluated
            user_query: Original user query
            ai_response: AI-generated response
            context_metadata: Additional context metadata

        Returns:
            Dictionary with relevance score and explanation
        """
        try:
            # Calculate base relevance factors
            query_relevance = self._calculate_query_relevance(
                document_source, user_query
            )
            response_relevance = self._calculate_response_relevance(
                document_source, ai_response
            )
            metadata_relevance = self._calculate_metadata_relevance(
                document_source, context_metadata
            )

            # Combine factors with weights
            combined_score = (
                query_relevance["score"] * 0.4
                + response_relevance["score"] * 0.4
                + metadata_relevance["score"] * 0.2
            )

            # Calculate confidence level
            confidence = self._calculate_confidence(
                query_relevance, response_relevance, metadata_relevance
            )

            # Generate explanation
            explanation = self._generate_relevance_explanation(
                document_source,
                query_relevance,
                response_relevance,
                metadata_relevance,
                combined_score,
                confidence,
            )

            result = {
                "document_id": str(document_source.id),
                "title": document_source.title,
                "relevance_score": round(combined_score, 3),
                "confidence_level": confidence,
                "explanation": explanation,
                "relevance_factors": {
                    "query_relevance": query_relevance,
                    "response_relevance": response_relevance,
                    "metadata_relevance": metadata_relevance,
                },
                "accessibility": document_source.is_accessible(),
                "access_state": document_source.access_state,
            }

            # Cache the result
            cache_key = f"{document_source.id}_{user_query[:50]}"
            self._relevance_cache[cache_key] = result

            logger.info(
                f"Calculated relevance for {document_source.title}: "
                f"score={combined_score:.3f}, confidence={confidence}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate relevance for {document_source.id}: {e}")
            return self._get_fallback_relevance(document_source)

    def _calculate_query_relevance(
        self, document_source: DocumentSource, user_query: str
    ) -> Dict[str, Any]:
        """Calculate relevance based on user query."""
        query_lower = user_query.lower()
        title_lower = document_source.title.lower()

        # Simple keyword matching for demonstration
        # In production, this would use semantic similarity
        score = 0.0
        factors = []

        # Title match
        if any(word in title_lower for word in query_lower.split()):
            score += 0.6
            factors.append("Title contains query keywords")

        # Metadata match
        for key, value in document_source.attribution_metadata.items():
            if isinstance(value, str) and any(
                word in value.lower() for word in query_lower.split()
            ):
                score += 0.2
                factors.append(f"Metadata '{key}' contains query keywords")
                break

        # Location/URL match
        if any(
            word in document_source.location.lower() for word in query_lower.split()
        ):
            score += 0.2
            factors.append("Document location contains query keywords")

        return {
            "score": min(score, 1.0),
            "factors": factors,
            "explanation": f"Query relevance based on {len(factors)} factors",
        }

    def _calculate_response_relevance(
        self, document_source: DocumentSource, ai_response: str
    ) -> Dict[str, Any]:
        """Calculate relevance based on AI response content."""
        response_lower = ai_response.lower()
        title_lower = document_source.title.lower()

        score = 0.0
        factors = []

        # Title mention in response
        if title_lower in response_lower:
            score += 0.5
            factors.append("Document title mentioned in response")

        # Metadata keywords in response
        metadata_keywords = set()
        for key, value in document_source.attribution_metadata.items():
            if isinstance(value, str):
                metadata_keywords.update(value.lower().split())

        matching_keywords = [
            keyword
            for keyword in metadata_keywords
            if keyword in response_lower and len(keyword) > 3
        ]

        if matching_keywords:
            score += min(len(matching_keywords) * 0.1, 0.3)
            factors.append(f"{len(matching_keywords)} metadata keywords in response")

        # Location mention
        if document_source.location.lower() in response_lower:
            score += 0.2
            factors.append("Document location mentioned in response")

        return {
            "score": min(score, 1.0),
            "factors": factors,
            "explanation": f"Response relevance based on {len(factors)} factors",
        }

    def _calculate_metadata_relevance(
        self,
        document_source: DocumentSource,
        context_metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate relevance based on metadata and context."""
        if not context_metadata:
            return {
                "score": 0.3,  # Default score for no context
                "factors": ["No specific context provided"],
                "explanation": "Default relevance based on document metadata",
            }

        score = 0.0
        factors = []

        # Check document type alignment
        doc_type = document_source.attribution_metadata.get("document_type", "")
        context_type = context_metadata.get("document_type", "")
        if doc_type and context_type and doc_type.lower() == context_type.lower():
            score += 0.4
            factors.append(f"Document type matches: {doc_type}")

        # Check temporal relevance
        if "created_at" in document_source.attribution_metadata:
            # Simple recency scoring
            score += 0.3
            factors.append("Document has creation timestamp")

        # Check access state
        if document_source.is_accessible():
            score += 0.3
            factors.append("Document is currently accessible")

        return {
            "score": min(score, 1.0),
            "factors": factors,
            "explanation": f"Context relevance based on {len(factors)} factors",
        }

    def _calculate_confidence(
        self,
        query_relevance: Dict[str, Any],
        response_relevance: Dict[str, Any],
        metadata_relevance: Dict[str, Any],
    ) -> str:
        """Calculate confidence level based on relevance factors."""
        scores = [
            query_relevance["score"],
            response_relevance["score"],
            metadata_relevance["score"],
        ]

        avg_score = sum(scores) / len(scores)
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)

        if avg_score >= 0.8 and score_variance < 0.05:
            return "high"
        elif avg_score >= 0.6:
            return "medium"
        elif avg_score >= 0.4:
            return "low"
        else:
            return "very_low"

    def _generate_relevance_explanation(
        self,
        document_source: DocumentSource,
        query_relevance: Dict[str, Any],
        response_relevance: Dict[str, Any],
        metadata_relevance: Dict[str, Any],
        combined_score: float,
        confidence: str,
    ) -> str:
        """Generate human-readable relevance explanation."""
        explanation_parts = []

        # Add strongest relevance factors
        all_factors = (
            query_relevance["factors"]
            + response_relevance["factors"]
            + metadata_relevance["factors"]
        )

        if all_factors:
            top_factors = all_factors[:3]  # Show top 3 factors
            explanation_parts.append(
                f"This document is relevant because: {', '.join(top_factors)}."
            )
        else:
            explanation_parts.append(
                "This document provides general background information."
            )

        # Add score context
        if combined_score >= 0.8:
            explanation_parts.append("It's highly relevant to your query.")
        elif combined_score >= 0.6:
            explanation_parts.append("It's quite relevant to your query.")
        elif combined_score >= 0.4:
            explanation_parts.append("It's somewhat relevant to your query.")
        else:
            explanation_parts.append("It provides supplementary information.")

        # Add confidence note
        if confidence == "high":
            explanation_parts.append("We're confident in this relevance assessment.")
        elif confidence == "medium":
            explanation_parts.append(
                "This relevance assessment is reasonably reliable."
            )
        else:
            explanation_parts.append(
                "This relevance assessment has lower confidence due to limited matching."
            )

        return " ".join(explanation_parts)

    def _get_fallback_relevance(
        self, document_source: DocumentSource
    ) -> Dict[str, Any]:
        """Get fallback relevance when calculation fails."""
        return {
            "document_id": str(document_source.id),
            "title": document_source.title,
            "relevance_score": 0.3,
            "confidence_level": "low",
            "explanation": "Unable to calculate specific relevance. "
            "This document may provide general background information.",
            "relevance_factors": {
                "query_relevance": {
                    "score": 0.3,
                    "factors": [],
                    "explanation": "Fallback",
                },
                "response_relevance": {
                    "score": 0.3,
                    "factors": [],
                    "explanation": "Fallback",
                },
                "metadata_relevance": {
                    "score": 0.3,
                    "factors": [],
                    "explanation": "Fallback",
                },
            },
            "accessibility": document_source.is_accessible(),
            "access_state": document_source.access_state,
        }

    def explain_multiple_sources(
        self,
        document_sources: List[DocumentSource],
        user_query: str,
        ai_response: str,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate relevance explanations for multiple document sources.

        Args:
            document_sources: List of document sources
            user_query: Original user query
            ai_response: AI-generated response
            context_metadata: Additional context metadata

        Returns:
            List of relevance explanations sorted by score
        """
        explanations = []

        for doc_source in document_sources:
            relevance = self.calculate_relevance_score(
                doc_source, user_query, ai_response, context_metadata
            )
            explanations.append(relevance)

        # Sort by relevance score (descending)
        explanations.sort(key=lambda x: x["relevance_score"], reverse=True)

        logger.info(
            f"Generated relevance explanations for {len(document_sources)} documents. "
            f"Top score: {explanations[0]['relevance_score'] if explanations else 'N/A'}"
        )

        return explanations

    def get_relevance_statistics(
        self, explanations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate statistics from relevance explanations.

        Args:
            explanations: List of relevance explanations

        Returns:
            Statistics about relevance distribution
        """
        if not explanations:
            return {
                "total_sources": 0,
                "average_relevance": 0.0,
                "confidence_distribution": {},
                "score_distribution": {},
            }

        scores = [exp["relevance_score"] for exp in explanations]
        confidence_levels = [exp["confidence_level"] for exp in explanations]

        # Calculate confidence distribution
        confidence_dist = {}
        for level in ["high", "medium", "low", "very_low"]:
            confidence_dist[level] = confidence_levels.count(level)

        # Calculate score distribution
        score_ranges = {
            "high": sum(1 for s in scores if s >= 0.8),
            "medium": sum(1 for s in scores if 0.6 <= s < 0.8),
            "low": sum(1 for s in scores if 0.4 <= s < 0.6),
            "very_low": sum(1 for s in scores if s < 0.4),
        }

        return {
            "total_sources": len(explanations),
            "average_relevance": sum(scores) / len(scores),
            "max_relevance": max(scores),
            "min_relevance": min(scores),
            "confidence_distribution": confidence_dist,
            "score_distribution": score_ranges,
            "top_source": explanations[0] if explanations else None,
        }

    def clear_cache(self) -> None:
        """Clear the relevance cache."""
        self._relevance_cache.clear()
        logger.info("Cleared relevance cache")


# Global service instance
_relevance_service = RelevanceService()


def get_relevance_service() -> RelevanceService:
    """Get the global relevance service instance."""
    return _relevance_service
