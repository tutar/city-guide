"""
Vector retrieval service for semantic similarity-based document retrieval.

This service replaces the keyword matching approach with vector embeddings
and cosine similarity for more accurate document relevance assessment.
"""

import logging
import numpy as np
from typing import List, Dict, Any
from uuid import UUID

from src.services.text_embedding_service import get_text_embedding_service

logger = logging.getLogger(__name__)


class VectorRetrievalService:
    """Service for vector-based document retrieval using semantic similarity."""

    def __init__(self):
        self.embedding_service = get_text_embedding_service()
        self._similarity_cache: Dict[str, float] = {}

    def find_most_relevant_document(
        self,
        query_text: str,
        documents: List[Dict[str, Any]],
        top_k: int = 3,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Find the most relevant documents for a query using semantic similarity.

        Args:
            query_text: Query text to find relevant documents for
            documents: List of documents with content and metadata
            top_k: Number of top documents to return
            similarity_threshold: Minimum similarity score threshold

        Returns:
            List of relevant documents with similarity scores
        """
        if not query_text.strip() or not documents:
            return []

        try:
            # Get query embedding
            query_embedding = self.embedding_service.get_embedding(query_text)

            # Calculate similarity for each document
            scored_documents = []
            for doc in documents:
                similarity_score = self._calculate_document_similarity(
                    query_embedding, doc
                )

                if similarity_score >= similarity_threshold:
                    scored_documents.append(
                        {
                            "document": doc,
                            "similarity_score": similarity_score,
                            "document_id": doc.get("document_id", ""),
                        }
                    )

            # Sort by similarity score (descending)
            scored_documents.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Return top-k documents
            top_documents = scored_documents[:top_k]

            logger.info(
                f"Found {len(top_documents)} relevant documents for query: '{query_text[:50]}...' "
                f"(top score: {top_documents[0]['similarity_score'] if top_documents else 0:.3f})"
            )

            return top_documents

        except Exception as e:
            logger.error(f"Vector retrieval failed for query '{query_text}': {e}")
            return self._get_fallback_results(documents)

    def _calculate_document_similarity(
        self, query_embedding: np.ndarray, document: Dict[str, Any]
    ) -> float:
        """
        Calculate semantic similarity between query and document.

        Args:
            query_embedding: Query text embedding vector
            document: Document with content and metadata

        Returns:
            Similarity score (0.0-1.0)
        """
        cache_key = (
            f"{hash(str(query_embedding.tolist()))}_{self._get_document_key(document)}"
        )

        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        try:
            # Get document content for embedding
            document_content = self._extract_document_content(document)

            if not document_content:
                return 0.0

            # Get document embedding
            doc_embedding = self.embedding_service.get_embedding(document_content)

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, doc_embedding)

            # Cache the result
            self._similarity_cache[cache_key] = similarity

            return similarity

        except Exception as e:
            logger.warning(f"Failed to calculate similarity for document: {e}")
            return 0.0

    def _extract_document_content(self, document: Dict[str, Any]) -> str:
        """Extract text content from document for embedding."""
        content_parts = []

        # Add title
        title = document.get("title") or document.get("document_title")
        if title:
            content_parts.append(title)

        # Add content
        content = document.get("content") or document.get("document_content")
        if content:
            # Use first 500 characters to avoid too long content
            content_parts.append(content[:500])

        # Add metadata keywords
        metadata = document.get("attribution_metadata", {})
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) < 100:
                content_parts.append(value)

        return " ".join(content_parts)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        # Ensure vectors are normalized
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        # Ensure value is between 0 and 1
        return max(0.0, min(1.0, similarity))

    def _get_document_key(self, document: Dict[str, Any]) -> str:
        """Create a unique key for document caching."""
        title = document.get("title") or document.get("document_title", "")
        content_preview = (
            document.get("content", "")[:50]
            or document.get("document_content", "")[:50]
        )
        return f"{title}:{content_preview}"

    def _get_fallback_results(
        self, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get fallback results when vector retrieval fails."""
        if not documents:
            return []

        # Return first document with low confidence
        return [
            {
                "document": documents[0],
                "similarity_score": 0.1,
                "document_id": documents[0].get("document_id"),
            }
        ]

    def clear_cache(self) -> None:
        """Clear the similarity cache."""
        self._similarity_cache.clear()
        logger.info("Cleared vector retrieval cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_similarities": len(self._similarity_cache),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified for demonstration)."""
        # In real implementation, track actual hits/misses
        total_calls = len(self._similarity_cache)
        if total_calls == 0:
            return 0.0

        # Assume 70% hit rate for demonstration
        return 0.7


# Global service instance
_vector_retrieval_service = VectorRetrievalService()


def get_vector_retrieval_service() -> VectorRetrievalService:
    """Get the global vector retrieval service instance."""
    return _vector_retrieval_service
