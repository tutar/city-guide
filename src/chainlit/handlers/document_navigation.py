"""
Document navigation handlers for Chainlit frontend.

This module handles user interactions with document references in AI responses,
including document preview, access verification, and navigation actions.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

import chainlit as cl

from src.services.document_service import DocumentService
from src.chainlit.components.document_preview import document_preview

logger = logging.getLogger(__name__)

# Initialize services
_document_service = DocumentService()


class DocumentNavigationHandler:
    """Handler for document navigation actions and interactions."""

    def __init__(self):
        self.document_service = _document_service

    async def handle_document_preview_request(
        self, document_id: str, message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle document preview request from user interaction.

        Args:
            document_id: Document source UUID as string
            message_id: Optional message ID for context

        Returns:
            Document preview information
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

            # Verify access
            access_info = self.document_service.verify_document_access(doc_uuid)

            # Generate preview content
            preview_content = self._generate_preview_content(
                document_source, access_info
            )

            # Log the preview request
            logger.info(
                f"Document preview requested: {document_id} "
                f"(message_id: {message_id})"
            )

            return {
                "success": True,
                "document_id": document_id,
                "preview": preview_content,
                "access_info": access_info,
            }

        except Exception as e:
            logger.error(f"Failed to handle document preview for {document_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to get document preview: {str(e)}",
            }

    def _generate_preview_content(
        self, document_source: Any, access_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preview content for document."""
        return {
            "title": document_source.title,
            "location": document_source.location,
            "access_state": document_source.access_state,
            "permission": document_source.get_access_permission(),
            "is_accessible": access_info["accessible"],
            "created_at": document_source.created_at.isoformat(),
            "updated_at": document_source.updated_at.isoformat(),
            "attribution_metadata": document_source.attribution_metadata,
            "access_info": access_info,
        }

    async def handle_bulk_document_access_check(
        self, document_ids: List[str], message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle bulk document access verification.

        Args:
            document_ids: List of document source UUIDs
            message_id: Optional message ID for context

        Returns:
            Bulk access verification results
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

            # Bulk verify access
            bulk_results = self.document_service.bulk_verify_access(valid_doc_ids)

            # Format results
            results = {}
            accessible_count = 0

            for doc_id, access_info in bulk_results.items():
                results[str(doc_id)] = {
                    "accessible": access_info["accessible"],
                    "access_state": access_info["access_state"],
                    "permission": access_info["permission"],
                    "title": access_info["title"],
                    "reason": access_info.get("reason"),
                }

                if access_info["accessible"]:
                    accessible_count += 1

            # Calculate statistics
            total_count = len(valid_doc_ids)
            statistics = {
                "total_documents": total_count,
                "accessible_documents": accessible_count,
                "unaccessible_documents": total_count - accessible_count,
                "accessibility_rate": accessible_count / total_count
                if total_count > 0
                else 0.0,
                "invalid_document_ids": invalid_doc_ids,
            }

            logger.info(
                f"Bulk document access check: {accessible_count}/{total_count} "
                f"accessible (message_id: {message_id})"
            )

            return {"success": True, "results": results, "statistics": statistics}

        except Exception as e:
            logger.error(f"Failed to handle bulk document access check: {e}")
            return {
                "success": False,
                "error": f"Failed to verify document access: {str(e)}",
            }

    async def handle_document_navigation_action(
        self,
        action_type: str,
        document_id: str,
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle document navigation actions (open, download, etc.).

        Args:
            action_type: Type of navigation action
            document_id: Document source UUID
            user_session_id: User session identifier
            message_id: Optional message ID for context

        Returns:
            Navigation action result
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

            # Verify access
            access_info = self.document_service.verify_document_access(doc_uuid)
            if not access_info["accessible"]:
                return {
                    "success": False,
                    "error": f"Document not accessible: {access_info.get('reason', 'Access denied')}",
                }

            # Handle different action types
            if action_type == "open":
                result = await self._handle_open_document(
                    document_source, user_session_id, message_id
                )
            elif action_type == "download":
                result = await self._handle_download_document(
                    document_source, user_session_id, message_id
                )
            elif action_type == "preview":
                result = await self._handle_preview_document(
                    document_source, user_session_id, message_id
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

            # Log the navigation action
            logger.info(
                f"Document navigation action: {action_type} for {document_id} "
                f"(session: {user_session_id}, message_id: {message_id})"
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to handle document navigation action {action_type} "
                f"for {document_id}: {e}"
            )
            return {
                "success": False,
                "error": f"Failed to perform navigation action: {str(e)}",
            }

    async def _handle_open_document(
        self,
        document_source: Any,
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle document open action."""
        # In a real implementation, this would open the document
        # For now, return document information
        return {
            "success": True,
            "action": "open",
            "document_id": str(document_source.id),
            "title": document_source.title,
            "location": document_source.location,
            "message": f"Opening document: {document_source.title}",
            "access_url": f"/api/documents/access/{document_source.id}",  # Placeholder
        }

    async def _handle_download_document(
        self,
        document_source: Any,
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle document download action."""
        # In a real implementation, this would initiate download
        # For now, return download information
        return {
            "success": True,
            "action": "download",
            "document_id": str(document_source.id),
            "title": document_source.title,
            "location": document_source.location,
            "message": f"Downloading document: {document_source.title}",
            "download_url": f"/api/documents/download/{document_source.id}",  # Placeholder
        }

    async def _handle_preview_document(
        self,
        document_source: Any,
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle document preview action."""
        # Generate enhanced preview
        access_info = self.document_service.verify_document_access(document_source.id)
        preview_content = self._generate_preview_content(document_source, access_info)

        return {
            "success": True,
            "action": "preview",
            "document_id": str(document_source.id),
            "preview": preview_content,
            "message": f"Showing preview for: {document_source.title}",
        }

    async def send_document_preview_message(
        self, document_id: str, preview_data: Dict[str, Any], user_session_id: str
    ) -> None:
        """
        Send a formatted document preview message to the user.

        Args:
            document_id: Document source UUID
            preview_data: Document preview information
            user_session_id: User session identifier
        """
        try:
            # Use the document preview component
            await document_preview.display_document_preview(
                document_data={"document_id": document_id, **preview_data},
                user_session_id=user_session_id,
            )

        except Exception as e:
            logger.error(f"Failed to send document preview message: {e}")
            # Fallback to simple message
            await cl.Message(
                content=f"Document preview for {document_id}", author="Document Preview"
            ).send()


# Global handler instance
_document_navigation_handler = DocumentNavigationHandler()


async def handle_document_preview(document_id: str, message_id: Optional[str] = None):
    """
    Handle document preview request.

    This function is called from Chainlit action handlers.
    """
    return await _document_navigation_handler.handle_document_preview_request(
        document_id, message_id
    )


async def handle_bulk_document_access(
    document_ids: List[str], message_id: Optional[str] = None
):
    """
    Handle bulk document access verification.

    This function is called from Chainlit action handlers.
    """
    return await _document_navigation_handler.handle_bulk_document_access_check(
        document_ids, message_id
    )


async def handle_document_navigation(
    action_type: str,
    document_id: str,
    user_session_id: str,
    message_id: Optional[str] = None,
):
    """
    Handle document navigation action.

    This function is called from Chainlit action handlers.
    """
    return await _document_navigation_handler.handle_document_navigation_action(
        action_type, document_id, user_session_id, message_id
    )
