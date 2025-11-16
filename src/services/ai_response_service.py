"""
Enhanced AI response service with document source attribution.

This service extends the existing AI service with attribution tracking
capabilities for document source attribution in AI-generated responses.
"""

import logging
import re
from annotated_types import doc
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from deprecated import deprecated

from services.sentence_splitter_service import SentenceSplitterService
from src.services.ai_service import AIService
from src.services.attribution_service import AttributionService
from src.services.vector_retrieval_service import get_vector_retrieval_service
from src.models.attribution import (
    SentenceAttribution,
    ResponseAttribution,
    AttributionMetadata,
)

from src.utils.config import settings

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
        self.vector_retrieval_service = get_vector_retrieval_service()
        self.sentence_splitter_service = SentenceSplitterService()

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
            (
                formatted_response_text,
                sentence_attributions,
            ) = self._track_response_attribution(
                response_id=response_id,
                response_text=response_text,
                context_documents=context_documents,
                attribution_metadata=attribution_metadata,
            )

            logger.info(
                f"Generated response with attribution: {response_id}, "
                f"{len(sentence_attributions)} sentences attributed"
            )
            enhanced_response = ai_response.copy()
            enhanced_response["formatted_response"] = formatted_response_text
            enhanced_response["sentence_attributions"] = sentence_attributions
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
    ) -> Tuple[str, List[SentenceAttribution]]:
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
        sentences = self.sentence_splitter_service.split_with_basic_processing(
            response_text
        )
        formatted_sentences = []
        sentence_index = 0

        for _, sentence in enumerate(sentences):
            if self.sentence_splitter_service.should_skip_citation(sentence):
                formatted_sentences.append(sentence + "\n\n")
                continue

            # Find the most relevant document for this sentence using vector retrieval
            document, confidence_score = self._find_relevant_document_with_vectors(
                sentence=sentence, context_documents=context_documents
            )

            if document:
                sentence_index = sentence_index + 1
                # Add attribution for this sentence
                attribution = self.attribution_service.add_sentence_attribution(
                    response_id=response_id,
                    sentence_index=sentence_index,
                    document=document,
                    confidence_score=confidence_score,
                    metadata=attribution_metadata,
                )
                sentence_attributions.append(attribution)

                formatted_sentence = f"{sentence} [^{sentence_index}]"

            else:
                formatted_sentence = sentence

            formatted_sentences.append(formatted_sentence + "\n\n")

        formatted_response_text = " ".join(formatted_sentences)
        return formatted_response_text, sentence_attributions

    def _find_relevant_document_with_vectors(
        self, sentence: str, context_documents: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Find the most relevant document for a sentence using vector retrieval.

        Args:
            sentence: Sentence to find source for
            context_documents: Available context documents

        Returns:
            Tuple of (document, confidence_score)
        """
        if not context_documents:
            return None, 0.0

        try:
            # Use vector retrieval to find most relevant documents
            relevant_docs = self.vector_retrieval_service.find_most_relevant_document(
                query_text=sentence,
                documents=context_documents,
                top_k=1,  # We only need the most relevant one
                similarity_threshold=settings.relevant_minimum_similarity_threshold,  # Minimum similarity threshold
            )

            if relevant_docs:
                best_doc = relevant_docs[0]
                confidence_score = best_doc["similarity_score"]
                document = best_doc["document"]

                logger.debug(
                    f"Found relevant document for sentence: '{sentence[:50]}...' "
                    f"with similarity score: {confidence_score:.3f}"
                )

                return document, confidence_score

            logger.debug(
                f"No relevant document found for sentence: '{sentence[:50]}...'"
            )
            return None, 0.0

        except Exception as e:
            logger.error(f"Vector retrieval failed for sentence '{sentence}': {e}")
            # Fallback to simple keyword matching if vector retrieval fails
            return self._fallback_keyword_matching(sentence, context_documents)

    def _fallback_keyword_matching(
        self, sentence: str, context_documents: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Fallback keyword matching when vector retrieval fails.

        Args:
            sentence: Sentence to find source for
            context_documents: Available context documents

        Returns:
            Tuple of (document, confidence_score)
        """
        sentence_lower = sentence.lower()
        best_match = None
        best_score = 0.0

        for document in context_documents:
            score = self._calculate_keyword_score(sentence_lower, document)

            if score > best_score:
                best_score = score
                best_match = document

        if best_match and best_score > 0.1:
            return best_match, min(best_score, 1.0)

        return None, 0.0

    def _calculate_keyword_score(
        self, sentence: str, document: Dict[str, Any]
    ) -> float:
        """
        Calculate keyword-based relevance score (fallback method).

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

    @deprecated
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
                    "document_id": str(attribution.document_id),
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
        sentences = self.sentence_splitter_service.split_with_basic_processing(
            response_text
        )

        # Create citation mapping
        citation_map = {}
        for attribution in response_attribution.sentence_attributions:
            if (
                attribution.confidence_score
                > settings.relevant_minimum_similarity_threshold
            ):  # Only include high-confidence attributions
                citation_map[attribution.document_id] = {
                    "title": attribution.title,
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
                    and attribution.confidence_score
                    > settings.relevant_minimum_similarity_threshold
                ):
                    doc_id = attribution.document_id
                    if doc_id in citation_map:
                        citation_number = citation_map[doc_id]["citation_number"]
                        # Add citation marker
                        enhanced_sentence = f"{sentence}[{citation_number}]"
                        break

            enhanced_sentences.append(enhanced_sentence)

        # Combine sentences back into text
        response_with_citations = ". ".join(enhanced_sentences)

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
            potential_id = document.get("document_id")
            if potential_id == doc_id:
                return document.get("document_title", "Unknown Document")

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
