"""
Service navigation component with keyboard navigation support
"""

import logging
from typing import Any

import chainlit as cl

from src.services.data_service import DataService

# Configure logging
logger = logging.getLogger(__name__)


class ServiceNavigation:
    """Service navigation component with accessibility features"""

    def __init__(self):
        self.current_focus_index = 0
        self.navigation_elements = []

    async def create_navigation_menu(self, options: list[dict[str, Any]]) -> cl.Message:
        """Create accessible navigation menu with keyboard support"""
        if not options:
            return None

        # Create accessible action elements
        actions = []
        self.navigation_elements = []

        for i, option in enumerate(options):
            action = cl.Action(
                name=f"nav_option_{i}",
                value=option.get("label", ""),
                description=option.get("description", ""),
                label=option.get("label", "Unknown"),
                # Accessibility attributes
                metadata={
                    "aria-label": option.get("label", ""),
                    "aria-describedby": f"nav_desc_{i}",
                    "tabindex": "0" if i == 0 else "-1",  # First element gets focus
                    "role": "button",
                },
            )
            actions.append(action)
            self.navigation_elements.append(
                {"action": action, "index": i, "label": option.get("label", "")}
            )

        # Create navigation message with accessibility features
        navigation_message = cl.Message(
            content=self._get_navigation_instructions(),
            actions=actions,
            author="Navigation",
            metadata={
                "role": "navigation",
                "aria-label": "Service navigation menu",
                "data-keyboard-navigation": "enabled",
            },
        )

        return navigation_message

    def _get_navigation_instructions(self) -> str:
        """Get keyboard navigation instructions for screen readers"""
        return """Navigate using:
- **Tab**: Move between options
- **Enter**: Select option
- **Arrow keys**: Navigate options
- **Escape**: Close navigation

Available options:"""

    async def handle_keyboard_navigation(self, key: str) -> str | None:
        """Handle keyboard navigation events"""
        if not self.navigation_elements:
            return None

        if key == "Tab":
            # Move to next element
            self.current_focus_index = (self.current_focus_index + 1) % len(
                self.navigation_elements
            )
            return self._update_focus()

        elif key == "ArrowDown":
            # Move down
            self.current_focus_index = min(
                self.current_focus_index + 1, len(self.navigation_elements) - 1
            )
            return self._update_focus()

        elif key == "ArrowUp":
            # Move up
            self.current_focus_index = max(self.current_focus_index - 1, 0)
            return self._update_focus()

        elif key == "Home":
            # Move to first element
            self.current_focus_index = 0
            return self._update_focus()

        elif key == "End":
            # Move to last element
            self.current_focus_index = len(self.navigation_elements) - 1
            return self._update_focus()

        elif key == "Enter":
            # Select current element
            if self.navigation_elements:
                selected = self.navigation_elements[self.current_focus_index]
                return selected["label"]

        elif key == "Escape":
            # Close navigation
            return "close_navigation"

        return None

    def _update_focus(self) -> str:
        """Update focus state and return announcement for screen readers"""
        if not self.navigation_elements:
            return ""

        current_element = self.navigation_elements[self.current_focus_index]
        return f"Focused on: {current_element['label']}"

    def get_current_focus(self) -> dict[str, Any] | None:
        """Get currently focused navigation element"""
        if not self.navigation_elements or self.current_focus_index >= len(
            self.navigation_elements
        ):
            return None

        return self.navigation_elements[self.current_focus_index]

    def reset_focus(self):
        """Reset focus to first element"""
        self.current_focus_index = 0

    async def create_main_menu(self) -> cl.Message:
        """Create main menu with service categories"""
        try:
            # Get all service categories
            with DataService() as data_service:
                service_categories = data_service.get_all_service_categories()

            if not service_categories:
                return cl.Message(
                    content="No service categories available at the moment.",
                    author="System",
                )

            # Create navigation options from service categories
            navigation_options = []
            for category in service_categories:
                navigation_options.append(
                    {
                        "label": category.name,
                        "description": category.description,
                        "action_type": "select_service",
                        "service_category_id": str(category.id),
                        "priority": 1,
                    }
                )

            # Add general navigation options
            navigation_options.extend(
                [
                    {
                        "label": "Search Services",
                        "description": "Search for specific government services",
                        "action_type": "search",
                        "priority": 2,
                    },
                    {
                        "label": "Recent Queries",
                        "description": "View your recent service queries",
                        "action_type": "history",
                        "priority": 3,
                    },
                    {
                        "label": "Help & Support",
                        "description": "Get help using the assistant",
                        "action_type": "help",
                        "priority": 4,
                    },
                ]
            )

            # Create the navigation menu
            main_menu = await self.create_navigation_menu(navigation_options)

            # Update the content to be more descriptive for main menu
            main_menu.content = """# Main Menu

Welcome to the City Guide Smart Assistant! Choose from the following options:

## Service Categories
Select a service category to get started, or use the other options below.

**Navigation Instructions:**
- **Tab** or **Arrow keys**: Navigate between options
- **Enter**: Select option
- **Escape**: Close menu

Available options:"""

            return main_menu

        except Exception as e:
            logger.error(f"Failed to create main menu: {e}")
            return cl.Message(
                content="Unable to load main menu. Please try again later.",
                author="System",
            )


class KeyboardNavigationManager:
    """Manager for keyboard navigation across the application"""

    def __init__(self):
        self.active_component = None
        self.components = {}

    def register_component(self, component_id: str, component):
        """Register a component for keyboard navigation"""
        self.components[component_id] = component

    def set_active_component(self, component_id: str):
        """Set the active component for keyboard navigation"""
        if component_id in self.components:
            self.active_component = self.components[component_id]

    async def handle_key_event(self, key: str) -> str | None:
        """Handle keyboard event and route to active component"""
        if self.active_component and hasattr(
            self.active_component, "handle_keyboard_navigation"
        ):
            return await self.active_component.handle_keyboard_navigation(key)
        return None

    def get_navigation_state(self) -> dict[str, Any]:
        """Get current navigation state"""
        return {
            "active_component": self.active_component.__class__.__name__
            if self.active_component
            else None,
            "registered_components": list(self.components.keys()),
        }


# Global navigation manager instance
navigation_manager = KeyboardNavigationManager()


@cl.on_keyboard_event
def handle_keyboard_event(key: str):
    """Global keyboard event handler"""
    # This would be connected to Chainlit's keyboard event system
    # For now, we'll implement the logic in the components
    pass
