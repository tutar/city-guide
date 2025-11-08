"""
Chat interface component with screen reader compatibility
"""

from datetime import datetime
from typing import Any

import chainlit as cl

from .search_results import search_results


class AccessibleChatInterface:
    """Chat interface with accessibility features for screen readers"""

    def __init__(self):
        self.message_history = []
        self.last_announcement = ""
        self.aria_live_region = None

    async def send_accessible_message(
        self, content: str, author: str = "Assistant", message_type: str = "info"
    ) -> cl.Message:
        """Send message with accessibility features"""

        # Create message with accessibility metadata
        message_metadata = {
            "role": "message",
            "aria-live": "polite" if message_type == "info" else "assertive",
            "aria-label": f"Message from {author}",
            "timestamp": datetime.now().isoformat(),
            "message-type": message_type,
        }

        # Format content for better screen reader experience
        formatted_content = self._format_content_for_accessibility(content, author)

        # Create and send message
        message = cl.Message(
            content=formatted_content, author=author, metadata=message_metadata
        )

        await message.send()

        # Store message for history
        self.message_history.append(
            {
                "content": content,
                "author": author,
                "timestamp": message_metadata["timestamp"],
                "type": message_type,
            }
        )

        # Announce new message for screen readers
        await self._announce_new_message(author, message_type)

        return message

    def _format_content_for_accessibility(self, content: str, author: str) -> str:
        """Format content for better screen reader experience"""

        # Add semantic structure for complex content
        if "\n" in content or len(content) > 100:
            # For longer messages, add structure
            formatted = f"**{author}:**\n\n{content}"
        else:
            formatted = f"**{author}:** {content}"

        return formatted

    async def _announce_new_message(self, author: str, message_type: str):
        """Announce new message for screen readers"""
        announcement = f"New message from {author}"

        if message_type == "error":
            announcement = f"Error: {announcement}"
        elif message_type == "success":
            announcement = f"Success: {announcement}"

        self.last_announcement = announcement

        # In a real implementation, this would update an aria-live region
        # For Chainlit, we can use a dedicated announcement message
        await self._create_announcement_element(announcement, message_type)

    async def _create_announcement_element(
        self, announcement: str, announcement_type: str
    ):
        """Create announcement element for screen readers"""
        # Create a visually hidden element for screen reader announcements
        # This is a workaround since Chainlit doesn't have direct aria-live support

        # Note: Chainlit doesn't support custom HTML elements directly
        # In a production environment, this would be implemented with custom frontend components
        # For now, we'll log the announcement
        print(f"SCREEN READER ANNOUNCEMENT: {announcement}")

    async def create_input_field(
        self, placeholder: str = "Type your message..."
    ) -> dict[str, Any]:
        """Create accessible input field"""

        input_metadata = {
            "role": "textbox",
            "aria-label": "Message input",
            "aria-describedby": "input-instructions",
            "placeholder": placeholder,
            "tabindex": "0",
            "aria-required": "true",
        }

        # In Chainlit, the input field is provided by the framework
        # We can enhance it with additional instructions
        instructions = """
**Accessibility Instructions:**
- Type your message and press Enter to send
- Use Tab to navigate to other elements
- Use Escape to cancel
        """

        return {
            "metadata": input_metadata,
            "instructions": instructions,
            "placeholder": placeholder,
        }

    async def create_error_message(self, error_content: str) -> cl.Message:
        """Create accessible error message"""
        return await self.send_accessible_message(
            content=error_content, author="System", message_type="error"
        )

    async def create_success_message(self, success_content: str) -> cl.Message:
        """Create accessible success message"""
        return await self.send_accessible_message(
            content=success_content, author="System", message_type="success"
        )

    def get_message_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent message history"""
        return self.message_history[-limit:]

    async def create_skip_link(self) -> dict[str, Any]:
        """Create skip navigation link for keyboard users"""

        skip_link_metadata = {
            "role": "link",
            "aria-label": "Skip to main content",
            "href": "#main-content",
            "class": "skip-link",
        }

        return {"content": "Skip to main content", "metadata": skip_link_metadata}

    async def update_aria_live_region(self, content: str, priority: str = "polite"):
        """Update aria-live region with new content"""
        # This would update a dedicated aria-live region in the DOM
        # For Chainlit, we simulate this with a special message

        live_region_metadata = {
            "role": "status",
            "aria-live": priority,
            "aria-atomic": "true",
            "class": "aria-live-region",
        }

        # Create announcement message
        announcement = cl.Message(
            content=content, author="Screen Reader", metadata=live_region_metadata
        )

        await announcement.send()

    def get_accessibility_report(self) -> dict[str, Any]:
        """Generate accessibility report for the chat interface"""

        return {
            "total_messages": len(self.message_history),
            "last_announcement": self.last_announcement,
            "message_types": {
                "info": len([m for m in self.message_history if m["type"] == "info"]),
                "error": len([m for m in self.message_history if m["type"] == "error"]),
                "success": len(
                    [m for m in self.message_history if m["type"] == "success"]
                ),
            },
            "accessibility_features": [
                "Screen reader announcements",
                "Keyboard navigation support",
                "ARIA attributes",
                "Semantic HTML structure",
                "Error and success messaging",
                "Message history tracking",
            ],
        }

    async def display_step_by_step_guidance(
        self,
        steps: list[dict[str, Any]],
        service_name: str,
        include_source_attribution: bool = True,
    ) -> cl.Message:
        """Display step-by-step guidance with accessibility features"""

        # Use the search results component for step-by-step guidance
        return await search_results.display_step_by_step_guidance(steps, service_name)

    async def display_search_results(
        self,
        results: list[dict[str, Any]],
        query: str,
        show_source_attribution: bool = True,
    ) -> cl.Message:
        """Display search results with accessibility features"""

        # Use the search results component
        message = await search_results.display_search_results(
            results, query, show_source_attribution
        )

        # Announce new search results for screen readers
        announcement = f"Search results for {query}: {len(results)} results found"
        await self.update_aria_live_region(announcement, "polite")

        return message


# Global chat interface instance
chat_interface = AccessibleChatInterface()
