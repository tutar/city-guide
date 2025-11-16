"""
Attribution display component for document source attribution.

This component displays document source attribution markers in AI responses
and provides access to citation lists and original documents.
"""

import chainlit as cl
from typing import Dict, Any, List, Optional


class AttributionDisplay:
    """Component for displaying document source attribution in AI responses."""

    def __init__(self):
        self._response_sentence_attributions_cache: Dict[str, float] = {}

    def get_cached_sentence_attributions(self, response_id: str) -> Optional[float]:
        """Get cached sentence attributions for a response ID."""
        return self._response_sentence_attributions_cache.get(response_id)

    def cache_sentence_attributions(
        self, response_id: str, attributions: float
    ) -> None:
        """Cache sentence attributions for a response ID."""
        self._response_sentence_attributions_cache[response_id] = attributions

    async def display_response_with_attribution(
        self,
        formatted_response: str,
        sentence_attributions: List[Dict[str, Any]],
        message_id: Optional[str] = None,
    ) -> cl.Message:
        """
        Display AI response with document source attribution markers.

        Args:
            formatted_response: The AI-generated response text
            attribution_data: Attribution data from the API response
            message_id: Optional message ID for updating existing message

        Returns:
            Chainlit Message object with attribution display
        """
        try:
            # Create the main response message
            if message_id:
                # Update existing message
                message = cl.Message(
                    content=formatted_response,
                    author="Assistant",
                    id=message_id,
                )
            else:
                # Create new message
                message = cl.Message(
                    content=formatted_response,
                    author="Assistant",
                )

            await message.send()

            return message

        except Exception as e:
            # Fallback to basic response display
            cl.error(f"Failed to display attribution: {e}")
            return await cl.Message(
                content=response_text,
                author="Assistant",
                metadata={"attribution_error": str(e)},
            ).send()

    def _format_response_with_markers(
        self, response_text: str, sentence_attributions: List[Dict[str, Any]]
    ) -> str:
        """
        Format response text with attribution markers.

        Args:
            response_text: Original response text
            sentence_attributions: List of sentence attributions

        Returns:
            Formatted response with attribution markers
        """
        if not sentence_attributions:
            return response_text

        # Split response into sentences (simplified approach)
        sentences = self._split_into_sentences(response_text)
        formatted_sentences = []

        for i, sentence in enumerate(sentences):
            # Find attribution for this sentence
            attribution = next(
                (a for a in sentence_attributions if a.get("sentence_index") == i), None
            )

            if attribution:
                # Add attribution marker
                doc_id = attribution.get("sentence_index", "")
                confidence = attribution.get("confidence_score", 0.0)
                marker_text = f"[^{doc_id}]"

                formatted_sentence = f"{sentence} {marker_text}"
            else:
                formatted_sentence = sentence

            formatted_sentences.append(formatted_sentence)

        return " ".join(formatted_sentences)

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple approach.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting - can be enhanced with NLP
        import re

        sentences = re.split(r"[.!?。！？]+", text)
        # sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    async def _display_citation_list(
        self, citation_list: Dict[str, Any], message: cl.Message
    ) -> None:
        """
        Display citation list with document sources.

        Args:
            citation_list: Citation list data
            message: The message object
        """
        document_sources = citation_list.get("document_sources", [])

        if not document_sources:
            return

        # Create citation list content
        message_actions = []
        citations = []

        for i, doc_source in enumerate(document_sources, 1):
            # payload with doc ids and (todo)display with favicon.ico of doc urls
            citations.append({"doc_id": doc_source.get("id", ""), "citation_id": i})

        action_payload = {"citations": citations}
        display_reference_action = cl.Action(
            name="display_reference_sidebar",
            payload=action_payload,
            label="已阅读结果",
        )
        message_actions.append(display_reference_action)

        message.actions = message_actions
        # Send citation list as a follow-up message
        await message.update()

    async def _display_fallback_indicator(self, parent_message_id: str) -> None:
        """
        Display fallback mode indicator.

        Args:
            parent_message_id: ID of the parent message
        """
        fallback_content = """
> ⚠️ **Note**: Document source attribution is currently limited.
> Some references may not be displayed due to technical limitations.
        """.strip()

        await cl.Message(
            content=fallback_content,
            author="System",
            parent_id=parent_message_id,
            metadata={"role": "fallback_indicator"},
        ).send()

    async def display_attribution_details(
        self, document_id: str, attribution_data: Dict[str, Any]
    ) -> None:
        """
        Display detailed attribution information for a specific document.

        Args:
            document_id: Document source ID
            attribution_data: Full attribution data
        """
        try:
            # Find the document source
            citation_list = attribution_data.get("citation_list", {})
            document_sources = citation_list.get("document_sources", [])

            document_source = next(
                (doc for doc in document_sources if doc.get("id") == document_id),
                None,
            )

            if not document_source:
                await cl.Message(
                    content=f"Document source {document_id} not found in citations.",
                    author="System",
                ).send()
                return

            # Create detailed view
            title = document_source.get("title", "Unknown Document")
            location = document_source.get("location", "")
            access_info = document_source.get("access_info", {})

            content = f"## 📄 Document Details: {title}\n\n"
            content += f"**ID:** `{document_id}`\n\n"

            if location:
                content += f"**Location:** {location}\n\n"

            if access_info:
                content += "**Access Information:**\n"
                for key, value in access_info.items():
                    content += f"- {key}: {value}\n"
                content += "\n"

            # Find sentences that reference this document
            sentence_attributions = attribution_data.get("sentence_attributions", [])
            relevant_sentences = [
                attr
                for attr in sentence_attributions
                if attr.get("document_id") == document_id
            ]

            if relevant_sentences:
                content += f"**Referenced in {len(relevant_sentences)} sentence(s)**\n"
                for attr in relevant_sentences:
                    confidence = attr.get("confidence_score", 0.0)
                    content += f"- Sentence {attr.get('sentence_index') + 1} (confidence: {confidence:.1%})\n"

            await cl.Message(
                content=content,
                author="System",
                metadata={
                    "role": "document_details",
                    "document_id": document_id,
                },
            ).send()

        except Exception as e:
            await cl.Message(
                content=f"Error displaying document details: {str(e)}", author="System"
            ).send()

    def get_attribution_summary(
        self, attribution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate attribution summary statistics.

        Args:
            attribution_data: Attribution data

        Returns:
            Summary statistics
        """
        sentence_attributions = attribution_data.get("sentence_attributions", [])
        citation_list = attribution_data.get("citation_list", {})

        total_sentences = len(sentence_attributions)
        attributed_sentences = len(
            [a for a in sentence_attributions if a.get("document_id")]
        )
        unique_documents = len(citation_list.get("document_sources", []))

        avg_confidence = 0.0
        if attributed_sentences > 0:
            avg_confidence = (
                sum(
                    a.get("confidence_score", 0.0)
                    for a in sentence_attributions
                    if a.get("document_id")
                )
                / attributed_sentences
            )

        return {
            "total_sentences": total_sentences,
            "attributed_sentences": attributed_sentences,
            "attribution_rate": attributed_sentences / total_sentences
            if total_sentences > 0
            else 0.0,
            "unique_documents": unique_documents,
            "average_confidence": avg_confidence,
            "fallback_mode": attribution_data.get("fallback_mode", False),
        }


# Global attribution display instance
attribution_display = AttributionDisplay()
