"""
Enhanced AI response service with document source attribution.

This service extends the existing AI service with attribution tracking
capabilities for document source attribution in AI-generated responses.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

from src.services.ai_service import AIService
from src.services.attribution_service import AttributionService
from src.services.document_service import DocumentService
from src.models.attribution import (
    SentenceAttribution,
    ResponseAttribution,
    AttributionMetadata,
)

logger = logging.getLogger(__name__)


class AIResponseService:
    """
    Enhanced AI response service with attribution tracking.

    This service wraps the existing AI service and adds attribution tracking
    capabilities for document source attribution.
    """

    def __init__(self):
        self.ai_service = AIService()
        self.attribution_service = AttributionService()
        self.document_service = DocumentService()

    def generate_response_with_attribution(
        self,
        user_query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI response with document source attribution.

        Args:
            user_query: User's query message
            context_documents: List of context documents with metadata
            conversation_history: Optional conversation history

        Returns:
            Enhanced response with attribution data
        """
        response_id = uuid4()
        logger.info(f"Generating response with attribution tracking: {response_id}")

        # Start attribution tracking
        attribution_metadata = self.attribution_service.start_attribution_tracking(
            response_id
        )

        try:
            # Generate AI response using existing service
            ai_response = self.ai_service.generate_government_guidance(
                user_query=user_query,
                context_documents=context_documents,
                conversation_history=conversation_history,
            )

            # Extract response text
            response_text = ai_response.get("response", "")

            # Track attribution for the generated response
            sentence_attributions = self._track_response_attribution(
                response_id=response_id,
                response_text=response_text,
                context_documents=context_documents,
                attribution_metadata=attribution_metadata,
            )

            # Complete attribution tracking
            response_attribution = (
                self.attribution_service.complete_attribution_tracking(
                    response_id=response_id,
                    sentence_attributions=sentence_attributions,
                    metadata=attribution_metadata,
                )
            )

            # Validate attribution consistency
            is_consistent = self.attribution_service.validate_attribution_consistency(
                response_attribution
            )

            if not is_consistent:
                logger.warning(
                    f"Attribution consistency check failed for response {response_id}"
                )

            # Enhance response with attribution data
            enhanced_response = self._enhance_response_with_attribution(
                ai_response=ai_response,
                response_attribution=response_attribution,
                context_documents=context_documents,
            )

            logger.info(
                f"Generated response with attribution: {response_id}, "
                f"{len(sentence_attributions)} sentences attributed"
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Failed to generate response with attribution: {e}")
            # Return basic response without attribution on error
            return self._get_fallback_response(user_query, context_documents)

    def _track_response_attribution(
        self,
        response_id: UUID,
        response_text: str,
        context_documents: List[Dict[str, Any]],
        attribution_metadata: AttributionMetadata,
    ) -> List[SentenceAttribution]:
        """
        Track attribution for each sentence in the response.

        Args:
            response_id: UUID of the response
            response_text: Generated response text
            context_documents: Context documents used
            attribution_metadata: Attribution metadata

        Returns:
            List of sentence attributions
        """
        sentence_attributions = []

        # Split response into sentences
        sentences = self._split_into_sentences(response_text)

        for sentence_index, sentence in enumerate(sentences):
            # Find the most relevant document for this sentence
            document_source_id, confidence_score = self._find_relevant_document(
                sentence=sentence, context_documents=context_documents
            )

            if document_source_id:
                # Add attribution for this sentence
                attribution = self.attribution_service.add_sentence_attribution(
                    response_id=response_id,
                    sentence_index=sentence_index,
                    document_source_id=document_source_id,
                    confidence_score=confidence_score,
                    metadata=attribution_metadata,
                )
                sentence_attributions.append(attribution)

        return sentence_attributions

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple regex.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting - can be enhanced with NLP libraries
        sentences = re.split(r"[.!?。！？]+", text)

        # Filter out empty sentences and strip whitespace
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

        return sentences

    def _find_relevant_document(
        self, sentence: str, context_documents: List[Dict[str, Any]]
    ) -> Tuple[Optional[UUID], float]:
        """
        Find the most relevant document for a sentence.

        Args:
            sentence: Sentence to find source for
            context_documents: Available context documents

        Returns:
            Tuple of (document_source_id, confidence_score)
        """
        if not context_documents:
            return None, 0.0

        # Simple keyword matching for demonstration
        # In production, this would use more sophisticated NLP techniques
        sentence_lower = sentence.lower()
        best_match = None
        best_score = 0.0

        for document in context_documents:
            score = self._calculate_relevance_score(sentence_lower, document)

            if score > best_score:
                best_score = score
                best_match = document

        if best_match and best_score > 0.1:  # Minimum confidence threshold
            # Extract or create document source ID
            document_source_id = self._get_document_source_id(best_match)
            return document_source_id, min(best_score, 1.0)

        return None, 0.0

    def _calculate_relevance_score(
        self, sentence: str, document: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score between sentence and document.

        Args:
            sentence: Lowercase sentence
            document: Document with metadata

        Returns:
            Relevance score (0.0-1.0)
        """
        score = 0.0

        # Check document title
        title = document.get("document_title", "").lower()
        if title and any(keyword in sentence for keyword in title.split()[:3]):
            score += 0.3

        # Check document content
        content: str = document.get("document_content", "").lower()
        if content:
            # Count overlapping words
            sentence_words = set(sentence.split())
            content_words = set(content.split())
            overlap = len(sentence_words.intersection(content_words))

            if overlap > 0:
                score += min(overlap * 0.1, 0.7)

        return score

    def _get_document_source_id(self, document: Dict[str, Any]) -> UUID:
        """
        Get or create document source ID for a document.

        Args:
            document: Document metadata

        Returns:
            Document source UUID
        """
        # In a real implementation, this would look up or create
        # a DocumentSource in the document service
        # For now, generate a deterministic UUID based on document content

        import hashlib

        # Create a unique identifier from document metadata
        doc_key = f"{document.get('title', '')}:{document.get('content', '')[:100]}"
        doc_hash = hashlib.md5(doc_key.encode()).hexdigest()

        # Convert hash to UUID
        return UUID(doc_hash[:32])

    def _enhance_response_with_attribution(
        self,
        ai_response: Dict[str, Any],
        response_attribution: ResponseAttribution,
        context_documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Enhance AI response with attribution data.

        Args:
            ai_response: Original AI response
            response_attribution: Attribution data
            context_documents: Context documents used

        Returns:
            Enhanced response with attribution
        """
        enhanced_response = ai_response.copy()

        # Embed document citations into the response text
        response_with_citations = self._embed_citations_into_response(
            ai_response.get("response", ""), response_attribution, context_documents
        )
        enhanced_response["response"] = response_with_citations

        # Add attribution data
        enhanced_response["attribution"] = {
            "sentence_attributions": [
                {
                    "sentence_index": attribution.sentence_index,
                    "document_source_id": str(attribution.document_source_id),
                    "confidence_score": attribution.confidence_score,
                }
                for attribution in response_attribution.sentence_attributions
            ],
            "citation_list": {
                "document_sources": [
                    {
                        "id": str(doc_id),
                        "title": self._get_document_title(doc_id, context_documents),
                        "location": f"/documents/{doc_id}",
                        "access_info": {"permission": "public"},
                    }
                    for doc_id in response_attribution.citation_list.document_sources
                ]
            },
        }

        # Add performance metrics
        performance_metrics = self.attribution_service.get_performance_metrics()
        enhanced_response["attribution_metrics"] = performance_metrics

        return enhanced_response

    def _embed_citations_into_response(
        self,
        response_text: str,
        response_attribution: ResponseAttribution,
        context_documents: List[Dict[str, Any]],
    ) -> str:
        """
        Embed document citations into the response text.

        Args:
            response_text: Original response text
            response_attribution: Attribution data
            context_documents: Context documents used

        Returns:
            Response text with embedded citations
        """
        if not response_attribution.sentence_attributions:
            return response_text

        # Split response into sentences
        sentences = self._split_into_sentences(response_text)

        # Create citation mapping
        citation_map = {}
        for attribution in response_attribution.sentence_attributions:
            if (
                attribution.confidence_score > 0.3
            ):  # Only include high-confidence attributions
                doc_id = attribution.document_source_id
                if doc_id not in citation_map:
                    citation_map[doc_id] = {
                        "title": self._get_document_title(doc_id, context_documents),
                        "citation_number": len(citation_map) + 1,
                    }

        # If no citations to add, return original text
        if not citation_map:
            return response_text

        # Add citations to sentences
        enhanced_sentences = []
        for i, sentence in enumerate(sentences):
            enhanced_sentence = sentence

            # Find attribution for this sentence
            for attribution in response_attribution.sentence_attributions:
                if (
                    attribution.sentence_index == i
                    and attribution.confidence_score > 0.3
                ):
                    doc_id = attribution.document_source_id
                    if doc_id in citation_map:
                        citation_number = citation_map[doc_id]["citation_number"]
                        # Add citation marker
                        enhanced_sentence = f"{sentence}[{citation_number}]"
                        break

            enhanced_sentences.append(enhanced_sentence)

        # Combine sentences back into text
        response_with_citations = ". ".join(enhanced_sentences)

        # Add citation references at the end
        if citation_map:
            citation_references = "\n\n**References:**\n"
            for doc_id, citation_info in citation_map.items():
                title = citation_info["title"]
                citation_number = citation_info["citation_number"]
                citation_references += f"[{citation_number}] {title}\n"

            response_with_citations += citation_references

        return response_with_citations

    def _get_document_title(
        self, doc_id: UUID, context_documents: List[Dict[str, Any]]
    ) -> str:
        """
        Get document title from context documents.

        Args:
            doc_id: Document source ID
            context_documents: Context documents

        Returns:
            Document title
        """
        # In a real implementation, this would query the document service
        # For now, try to find matching document in context
        for document in context_documents:
            # Check if this document matches our ID (simplified)
            potential_id = self._get_document_source_id(document)
            if potential_id == doc_id:
                return document.get("title", "Unknown Document")

        return "Unknown Document"

    def _get_fallback_response(
        self, user_query: str, context_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get fallback response when attribution tracking fails.

        Args:
            user_query: User query
            context_documents: Context documents

        Returns:
            Basic response without attribution
        """
        try:
            # Generate response without attribution tracking
            response = self.ai_service.generate_government_guidance(
                user_query=user_query, context_documents=context_documents
            )

            # Add minimal attribution info
            response["attribution"] = {
                "sentence_attributions": [],
                "citation_list": {"document_sources": []},
                "fallback_mode": True,
            }

            return response

        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return {
                "response": "I apologize, but I'm having trouble generating a response at the moment. Please try again later.",
                "attribution": {
                    "sentence_attributions": [],
                    "citation_list": {"document_sources": []},
                    "error": str(e),
                },
            }

    def get_attribution_for_response(
        self, response_id: UUID
    ) -> Optional[ResponseAttribution]:
        """
        Get attribution data for a specific response.

        Args:
            response_id: Response UUID

        Returns:
            ResponseAttribution if found
        """
        return self.attribution_service.get_attribution_for_response(response_id)

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get attribution performance metrics.

        Returns:
            Performance metrics
        """
        return self.attribution_service.get_performance_metrics()
