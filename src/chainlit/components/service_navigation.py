"""
Service navigation component with keyboard navigation support
"""

import chainlit as cl
from typing import List, Dict, Any, Optional


class ServiceNavigation:
    """Service navigation component with accessibility features"""

    def __init__(self):
        self.current_focus_index = 0
        self.navigation_elements = []

    async def create_navigation_menu(self, options: List[Dict[str, Any]]) -> cl.Message:
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
                    "role": "button"
                }
            )
            actions.append(action)
            self.navigation_elements.append({
                "action": action,
                "index": i,
                "label": option.get("label", "")
            })

        # Create navigation message with accessibility features
        navigation_message = cl.Message(
            content=self._get_navigation_instructions(),
            actions=actions,
            author="Navigation",
            metadata={
                "role": "navigation",
                "aria-label": "Service navigation menu",
                "data-keyboard-navigation": "enabled"
            }
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

    async def handle_keyboard_navigation(self, key: str) -> Optional[str]:
        """Handle keyboard navigation events"""
        if not self.navigation_elements:
            return None

        if key == "Tab":
            # Move to next element
            self.current_focus_index = (self.current_focus_index + 1) % len(self.navigation_elements)
            return self._update_focus()

        elif key == "ArrowDown":
            # Move down
            self.current_focus_index = min(self.current_focus_index + 1, len(self.navigation_elements) - 1)
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

    def get_current_focus(self) -> Optional[Dict[str, Any]]:
        """Get currently focused navigation element"""
        if not self.navigation_elements or self.current_focus_index >= len(self.navigation_elements):
            return None

        return self.navigation_elements[self.current_focus_index]

    def reset_focus(self):
        """Reset focus to first element"""
        self.current_focus_index = 0


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

    async def handle_key_event(self, key: str) -> Optional[str]:
        """Handle keyboard event and route to active component"""
        if self.active_component and hasattr(self.active_component, 'handle_keyboard_navigation'):
            return await self.active_component.handle_keyboard_navigation(key)
        return None

    def get_navigation_state(self) -> Dict[str, Any]:
        """Get current navigation state"""
        return {
            "active_component": self.active_component.__class__.__name__ if self.active_component else None,
            "registered_components": list(self.components.keys())
        }


# Global navigation manager instance
navigation_manager = KeyboardNavigationManager()


@cl.on_keyboard_event
def handle_keyboard_event(key: str):
    """Global keyboard event handler"""
    # This would be connected to Chainlit's keyboard event system
    # For now, we'll implement the logic in the components
    pass