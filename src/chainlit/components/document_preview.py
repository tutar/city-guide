"""
Document preview component for Chainlit frontend.

This component provides rich document preview functionality with interactive
actions for document navigation and access.
"""

import logging
from typing import Any, Dict, List, Optional

import chainlit as cl

logger = logging.getLogger(__name__)


class DocumentPreviewComponent:
    """Component for displaying document previews with interactive actions."""

    def __init__(self):
        self.lucide_icons = {
            "open": "file-text",
            "download": "download",
            "preview": "eye",
            "info": "info",
            "external": "external-link",
            "metadata": "database",
            "access": "shield",
        }

    async def display_document_preview(
        self,
        document_data: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display a rich document preview with interactive actions.

        Args:
            document_data: Document information including metadata
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            # Extract document information
            document_id = document_data.get("document_id", "unknown")
            title = document_data.get("title", "Unknown Document")
            location = document_data.get("location", "Unknown location")
            access_state = document_data.get("access_state", "unknown")
            is_accessible = document_data.get("is_accessible", False)
            permission = document_data.get("permission", "unknown")
            attribution_metadata = document_data.get("attribution_metadata", {})

            # Create status indicator
            if is_accessible:
                status_emoji = "✅"
                status_text = "Available"
            else:
                status_emoji = "❌"
                status_text = "Unavailable"

            # Create message content
            message_content = f"""
## 📄 Document Preview: {title}

**Status:** {status_emoji} {status_text}
**Access State:** {access_state}
**Permission:** {permission}
**Location:** {location}

### Metadata
- **Document ID:** `{document_id}`
- **Created:** {document_data.get('created_at', 'Unknown')}
- **Updated:** {document_data.get('updated_at', 'Unknown')}

### Attribution Metadata
{self._format_attribution_metadata(attribution_metadata)}
"""

            # Create interactive actions
            actions = self._create_document_actions(
                document_id, is_accessible, message_id
            )

            # Send the preview message
            await cl.Message(
                content=message_content,
                actions=actions,
                author="Document Preview",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed document preview for {document_id} "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display document preview: {e}")
            # Fallback to simple message
            await cl.Message(
                content=f"Document preview for {document_data.get('document_id', 'unknown')}",
                author="Document Preview",
            ).send()

    def _format_attribution_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format attribution metadata for display."""
        if not metadata:
            return "*No attribution metadata available*"

        formatted_lines = []
        for key, value in metadata.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                formatted_lines.append(f"- **{key}:**")
                for sub_key, sub_value in value.items():
                    formatted_lines.append(f"  - {sub_key}: {sub_value}")
            elif isinstance(value, list):
                # Handle lists
                formatted_lines.append(f"- **{key}:** {', '.join(map(str, value))}")
            else:
                # Handle simple values
                formatted_lines.append(f"- **{key}:** {value}")

        return "\n".join(formatted_lines)

    def _create_document_actions(
        self, document_id: str, is_accessible: bool, message_id: Optional[str] = None
    ) -> List[cl.Action]:
        """Create interactive actions for document navigation."""
        actions = []

        # Preview action (always available)
        preview_action = cl.Action(
            name=f"doc_preview_{document_id}_{message_id or 'default'}",
            payload={"action_type": "preview", "document_id": document_id},
            icon=self.lucide_icons["preview"],
            label="Preview",
            tooltip="Show detailed document preview",
        )
        actions.append(preview_action)

        # Open action (only if accessible)
        if is_accessible:
            open_action = cl.Action(
                name=f"doc_open_{document_id}_{message_id or 'default'}",
                payload={"action_type": "open", "document_id": document_id},
                icon=self.lucide_icons["open"],
                label="Open",
                tooltip="Open the full document",
            )
            actions.append(open_action)

            # Download action (only if accessible)
            download_action = cl.Action(
                name=f"doc_download_{document_id}_{message_id or 'default'}",
                payload={"action_type": "download", "document_id": document_id},
                icon=self.lucide_icons["download"],
                label="Download",
                tooltip="Download document copy",
            )
            actions.append(download_action)

        # Metadata action (always available)
        metadata_action = cl.Action(
            name=f"doc_metadata_{document_id}_{message_id or 'default'}",
            payload={"action_type": "metadata", "document_id": document_id},
            icon=self.lucide_icons["metadata"],
            label="Metadata",
            tooltip="Show detailed metadata",
        )
        actions.append(metadata_action)

        # Access info action (always available)
        access_action = cl.Action(
            name=f"doc_access_{document_id}_{message_id or 'default'}",
            payload={"action_type": "access", "document_id": document_id},
            icon=self.lucide_icons["access"],
            label="Access Info",
            tooltip="Show access information",
        )
        actions.append(access_action)

        return actions

    async def display_multiple_document_previews(
        self,
        documents_data: List[Dict[str, Any]],
        user_session_id: str,
        title: str = "Document Sources",
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display multiple document previews in a consolidated view.

        Args:
            documents_data: List of document information
            user_session_id: User session identifier
            title: Title for the consolidated view
            message_id: Optional message ID for context
        """
        try:
            if not documents_data:
                await cl.Message(
                    content="No documents available for preview.",
                    author="Document Preview",
                ).send()
                return

            # Create summary message
            accessible_count = sum(
                1 for doc in documents_data if doc.get("is_accessible", False)
            )
            total_count = len(documents_data)

            message_content = f"""
## 📚 {title}

**Summary:** {accessible_count}/{total_count} documents accessible

### Available Documents
"""

            # Add each document summary
            for i, doc_data in enumerate(documents_data):
                doc_id = doc_data.get("document_id", f"doc_{i}")
                doc_title = doc_data.get("title", "Unknown Document")
                is_accessible = doc_data.get("is_accessible", False)

                status_emoji = "✅" if is_accessible else "❌"
                message_content += f"\n{status_emoji} **{doc_title}** (ID: `{doc_id}`)"

            # Create actions for each document
            actions = []
            for i, doc_data in enumerate(documents_data):
                doc_id = doc_data.get("document_id", f"doc_{i}")
                doc_title = doc_data.get("title", "Unknown Document")

                # Individual document preview action
                preview_action = cl.Action(
                    name=f"multi_doc_preview_{doc_id}_{message_id or 'default'}",
                    payload={"action_type": "preview", "document_id": doc_id},
                    icon=self.lucide_icons["preview"],
                    label=f"Preview: {doc_title[:20]}{'...' if len(doc_title) > 20 else ''}",
                    tooltip=f"Preview {doc_title}",
                )
                actions.append(preview_action)

            # Send the consolidated message
            await cl.Message(
                content=message_content,
                actions=actions,
                author="Document Preview",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed {len(documents_data)} document previews "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display multiple document previews: {e}")
            await cl.Message(
                content=f"Preview for {len(documents_data)} documents",
                author="Document Preview",
            ).send()

    async def display_document_access_summary(
        self,
        access_results: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display a summary of document access verification results.

        Args:
            access_results: Access verification results
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            results = access_results.get("results", {})
            statistics = access_results.get("statistics", {})

            accessible_count = statistics.get("accessible_documents", 0)
            total_count = statistics.get("total_documents", 0)
            accessibility_rate = statistics.get("accessibility_rate", 0.0)

            message_content = f"""
## 🔍 Document Access Summary

**Accessibility:** {accessible_count}/{total_count} documents accessible ({accessibility_rate:.1%})

### Access Status
"""

            # Add access status for each document
            for doc_id, result in results.items():
                title = result.get("title", "Unknown Document")
                is_accessible = result.get("accessible", False)
                access_state = result.get("access_state", "unknown")

                status_emoji = "✅" if is_accessible else "❌"
                message_content += f"\n{status_emoji} **{title}** - {access_state}"

                if not is_accessible:
                    reason = result.get("reason", "Unknown reason")
                    message_content += f" ({reason})"

            # Create actions for detailed previews
            actions = []
            for doc_id, result in results.items():
                title = result.get("title", "Unknown Document")

                preview_action = cl.Action(
                    name=f"access_preview_{doc_id}_{message_id or 'default'}",
                    payload={"action_type": "preview", "document_id": doc_id},
                    icon=self.lucide_icons["preview"],
                    label=f"Details: {title[:15]}{'...' if len(title) > 15 else ''}",
                    tooltip=f"Show details for {title}",
                )
                actions.append(preview_action)

            await cl.Message(
                content=message_content,
                actions=actions,
                author="Document Access",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed document access summary for {total_count} documents "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display document access summary: {e}")
            await cl.Message(
                content="Document access summary", author="Document Access"
            ).send()


# Global component instance
document_preview = DocumentPreviewComponent()
