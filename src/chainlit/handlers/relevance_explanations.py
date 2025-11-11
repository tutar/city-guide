"""
Relevance explanation handlers for Chainlit frontend.

This module handles relevance explanation requests and displays
source relevance information in AI responses.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import chainlit as cl

from src.services.relevance_service import get_relevance_service
from src.services.document_service import DocumentService
from src.chainlit.components.relevance_visualization import relevance_visualization

logger = logging.getLogger(__name__)

# Initialize services
_relevance_service = get_relevance_service()
_document_service = DocumentService()


class RelevanceExplanationHandler:
    """Handler for source relevance explanations and visualizations."""

    def __init__(self):
        self.relevance_service = _relevance_service
        self.document_service = _document_service

    async def handle_relevance_explanation_request(
        self,
        document_ids: List[str],
        user_query: str,
        ai_response: str,
        user_session_id: str,
        message_id: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle relevance explanation request for AI response.

        Args:
            document_ids: List of document source UUIDs
            user_query: Original user query
            ai_response: AI-generated response
            user_session_id: User session identifier
            message_id: Optional message ID for context
            context_metadata: Additional context metadata

        Returns:
            Relevance explanation results
        """
        try:
            # Parse document IDs
            valid_doc_ids = []
            invalid_doc_ids = []

            for doc_id_str in document_ids:
                try:
                    valid_doc_ids.append(UUID(doc_id_str))
                except ValueError:
                    invalid_doc_ids.append(doc_id_str)

            if not valid_doc_ids:
                return {"success": False, "error": "No valid document IDs provided"}

            # Get document sources
            document_sources = []
            for doc_id in valid_doc_ids:
                doc_source = self.document_service.get_document_source(doc_id)
                if doc_source:
                    document_sources.append(doc_source)

            if not document_sources:
                return {"success": False, "error": "No valid document sources found"}

            # Calculate relevance explanations
            explanations = self.relevance_service.explain_multiple_sources(
                document_sources=document_sources,
                user_query=user_query,
                ai_response=ai_response,
                context_metadata=context_metadata,
            )

            # Generate statistics
            statistics = self.relevance_service.get_relevance_statistics(explanations)

            # Send relevance visualization to user
            await self._send_relevance_visualization(
                explanations=explanations,
                statistics=statistics,
                user_session_id=user_session_id,
                message_id=message_id,
            )

            logger.info(
                f"Generated relevance explanations for {len(document_sources)} documents. "
                f"Average relevance: {statistics.get('average_relevance', 0):.3f} "
                f"(session: {user_session_id})"
            )

            return {
                "success": True,
                "explanations": explanations,
                "statistics": statistics,
                "invalid_document_ids": invalid_doc_ids,
            }

        except Exception as e:
            logger.error(f"Failed to handle relevance explanation request: {e}")
            return {
                "success": False,
                "error": f"Failed to generate relevance explanations: {str(e)}",
            }

    async def _send_relevance_visualization(
        self,
        explanations: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Send relevance visualization to the user.

        Args:
            explanations: List of relevance explanations
            statistics: Relevance statistics
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            await relevance_visualization.display_relevance_summary(
                explanations=explanations,
                statistics=statistics,
                user_session_id=user_session_id,
                message_id=message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send relevance visualization: {e}")
            # Fallback to simple message
            await self._send_fallback_relevance_message(explanations, user_session_id)

    async def _send_fallback_relevance_message(
        self, explanations: List[Dict[str, Any]], user_session_id: str
    ) -> None:
        """Send fallback relevance message when visualization fails."""
        try:
            if not explanations:
                await cl.Message(
                    content="No relevance information available.",
                    author="Source Relevance",
                ).send()
                return

            # Create simple summary
            top_sources = explanations[:3]  # Show top 3
            message_content = "## 🔍 Source Relevance Summary\n\n"

            for i, exp in enumerate(top_sources):
                score = exp["relevance_score"]
                confidence = exp["confidence_level"]
                title = exp["title"]

                # Add emoji based on score
                if score >= 0.8:
                    emoji = "⭐"
                elif score >= 0.6:
                    emoji = "✅"
                elif score >= 0.4:
                    emoji = "🔄"
                else:
                    emoji = "📄"

                message_content += (
                    f"{emoji} **{title}**\n"
                    f"   • Relevance: {score:.1%}\n"
                    f"   • Confidence: {confidence.replace('_', ' ').title()}\n\n"
                )

            if len(explanations) > 3:
                message_content += f"*... and {len(explanations) - 3} more sources*"

            await cl.Message(
                content=message_content,
                author="Source Relevance",
                parent_id=user_session_id,
            ).send()

        except Exception as e:
            logger.error(f"Failed to send fallback relevance message: {e}")
            await cl.Message(
                content="Source relevance information available.",
                author="Source Relevance",
            ).send()

    async def handle_single_document_relevance(
        self,
        document_id: str,
        user_query: str,
        ai_response: str,
        user_session_id: str,
        message_id: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle single document relevance explanation.

        Args:
            document_id: Document source UUID
            user_query: Original user query
            ai_response: AI-generated response
            user_session_id: User session identifier
            message_id: Optional message ID for context
            context_metadata: Additional context metadata

        Returns:
            Single document relevance explanation
        """
        try:
            # Parse document ID
            try:
                doc_uuid = UUID(document_id)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid document ID format: {document_id}",
                }

            # Get document source
            document_source = self.document_service.get_document_source(doc_uuid)
            if not document_source:
                return {"success": False, "error": f"Document not found: {document_id}"}

            # Calculate relevance explanation
            explanation = self.relevance_service.calculate_relevance_score(
                document_source=document_source,
                user_query=user_query,
                ai_response=ai_response,
                context_metadata=context_metadata,
            )

            # Send detailed relevance view
            await relevance_visualization.display_detailed_relevance(
                explanation=explanation,
                user_session_id=user_session_id,
                message_id=message_id,
            )

            logger.info(
                f"Generated single document relevance for {document_id}. "
                f"Score: {explanation['relevance_score']:.3f} "
                f"(session: {user_session_id})"
            )

            return {"success": True, "explanation": explanation}

        except Exception as e:
            logger.error(
                f"Failed to handle single document relevance for {document_id}: {e}"
            )
            return {
                "success": False,
                "error": f"Failed to generate relevance explanation: {str(e)}",
            }

    async def handle_relevance_comparison(
        self,
        document_ids: List[str],
        user_query: str,
        ai_response: str,
        user_session_id: str,
        message_id: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle relevance comparison between multiple documents.

        Args:
            document_ids: List of document source UUIDs
            user_query: Original user query
            ai_response: AI-generated response
            user_session_id: User session identifier
            message_id: Optional message ID for context
            context_metadata: Additional context metadata

        Returns:
            Relevance comparison results
        """
        try:
            # Get relevance explanations
            result = await self.handle_relevance_explanation_request(
                document_ids=document_ids,
                user_query=user_query,
                ai_response=ai_response,
                user_session_id=user_session_id,
                message_id=message_id,
                context_metadata=context_metadata,
            )

            if not result["success"]:
                return result

            # Send comparison visualization
            await relevance_visualization.display_relevance_comparison(
                explanations=result["explanations"],
                statistics=result["statistics"],
                user_session_id=user_session_id,
                message_id=message_id,
            )

            logger.info(
                f"Generated relevance comparison for {len(document_ids)} documents "
                f"(session: {user_session_id})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to handle relevance comparison: {e}")
            return {
                "success": False,
                "error": f"Failed to generate relevance comparison: {str(e)}",
            }


# Global handler instance
_relevance_explanation_handler = RelevanceExplanationHandler()


async def handle_relevance_explanation(
    document_ids: List[str],
    user_query: str,
    ai_response: str,
    user_session_id: str,
    message_id: Optional[str] = None,
    context_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Handle relevance explanation request.

    This function is called from Chainlit action handlers.
    """
    return await _relevance_explanation_handler.handle_relevance_explanation_request(
        document_ids=document_ids,
        user_query=user_query,
        ai_response=ai_response,
        user_session_id=user_session_id,
        message_id=message_id,
        context_metadata=context_metadata,
    )


async def handle_single_document_relevance(
    document_id: str,
    user_query: str,
    ai_response: str,
    user_session_id: str,
    message_id: Optional[str] = None,
    context_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Handle single document relevance explanation.

    This function is called from Chainlit action handlers.
    """
    return await _relevance_explanation_handler.handle_single_document_relevance(
        document_id=document_id,
        user_query=user_query,
        ai_response=ai_response,
        user_session_id=user_session_id,
        message_id=message_id,
        context_metadata=context_metadata,
    )


async def handle_relevance_comparison(
    document_ids: List[str],
    user_query: str,
    ai_response: str,
    user_session_id: str,
    message_id: Optional[str] = None,
    context_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Handle relevance comparison between documents.

    This function is called from Chainlit action handlers.
    """
    return await _relevance_explanation_handler.handle_relevance_comparison(
        document_ids=document_ids,
        user_query=user_query,
        ai_response=ai_response,
        user_session_id=user_session_id,
        message_id=message_id,
        context_metadata=context_metadata,
    )
