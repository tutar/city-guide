"""
Chainlit application for City Guide Smart Assistant
"""

import uuid

import chainlit as cl
import httpx

from src.api.conversation import (
    SendMessageRequest,
    StartConversationRequest,
)


# FastAPI base URL
FASTAPI_BASE_URL = "http://localhost:8000"


async def start_conversation_http(request: StartConversationRequest):
    """Start conversation via HTTP call to FastAPI"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FASTAPI_BASE_URL}/api/conversation/start",
            json=request.model_dump(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


async def send_message_http(request: SendMessageRequest):
    """Send message via HTTP call to FastAPI"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FASTAPI_BASE_URL}/api/conversation/message",
            json=request.model_dump(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


@cl.on_chat_start
async def on_chat_start():
    """Initialize conversation when chat starts"""
    # Create a new conversation session
    session_id = str(uuid.uuid4())

    # Store session ID in user session
    cl.user_session.set("session_id", session_id)

    # Start conversation with API via HTTP
    request = StartConversationRequest(
        user_session_id=session_id,
        user_preferences={"language": "zh-CN"},  # Default to Chinese
    )

    try:
        response = await start_conversation_http(request)

        # Send enhanced welcome message with context
        welcome_content = f"""{response.get("welcome_message")}

**💡 How I can help you:**
- **Government Services**: Passport applications, business registration, visa services
- **Document Requirements**: Complete checklists and required materials
- **Application Process**: Step-by-step guidance for various services
- **Service Locations**: Find nearest government service centers
- **Status Tracking**: Check application progress and processing times

Feel free to ask me anything about government services!"""

        await cl.Message(content=welcome_content, author="Assistant").send()

        # Store conversation context
        cl.user_session.set("conversation_id", response.get("conversation_id"))
        cl.user_session.set("navigation_options", response.get("navigation_options"))

        # Display initial navigation options
        navigation_options = response.get("navigation_options", [])
        if navigation_options:
            await display_navigation_options(navigation_options)

    except Exception:
        await cl.Message(
            content="Sorry, I encountered an error while starting our conversation. Please try again.",
            author="Assistant",
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages"""
    session_id = cl.user_session.get("session_id")

    if not session_id:
        await cl.Message(
            content="Session not found. Please refresh the page and try again.",
            author="Assistant",
        ).send()
        return

    try:
        # Send message to API via HTTP
        request = SendMessageRequest(session_id=session_id, message=message.content)

        response = await send_message_http(request)

        # Send assistant response
        await cl.Message(
            content=response.get("response", ""), author="Assistant"
        ).send()

        # Update navigation options
        navigation_options = response.get("navigation_options", [])
        if navigation_options:
            await display_navigation_options(navigation_options)
            cl.user_session.set("navigation_options", navigation_options)

    except Exception:
        await cl.Message(
            content="Sorry, I encountered an error while processing your message. Please try again.",
            author="Assistant",
        ).send()


async def display_navigation_options(navigation_options: list):
    """Display navigation options as interactive elements with enhanced UI"""
    if not navigation_options:
        return

    # Group navigation options by action type for better organization
    grouped_options = {}
    for option in navigation_options:
        action_type = option.get("action_type", "general")
        if action_type not in grouped_options:
            grouped_options[action_type] = []
        grouped_options[action_type].append(option)

    # Map action types to lucide icons (used in Action creation)
    lucide_icons = {
        "requirements": "file-text",
        "explain": "book-open",
        "location": "map-pin",
        "appointment": "calendar",
        "status": "bar-chart",
        "contact": "phone",
        "download": "download",
        "external": "external-link",
        "general": "lightbulb",
    }

    # Group by priority for better visual hierarchy
    high_priority_options = []
    medium_priority_options = []
    low_priority_options = []

    for option in navigation_options:
        priority = option.get("priority", 5)
        if priority <= 2:
            high_priority_options.append(option)
        elif priority <= 4:
            medium_priority_options.append(option)
        else:
            low_priority_options.append(option)

    # Display high priority options first
    if high_priority_options:
        await cl.Message(
            content="**Recommended Next Steps:**", author="Navigation"
        ).send()

        high_priority_actions = []
        for i, option in enumerate(high_priority_options):
            action_type = option.get("action_type", "general")
            label = option.get("label", "Unknown")
            description = option.get("description", "")

            # Ensure unique name and non-empty payload
            action_name = f"high_priority_{i}_{label.replace(' ', '_')}"
            action_payload = {"label": label, "description": description}

            # Use global lucide icons mapping
            icon = lucide_icons.get(action_type, "lightbulb")

            action = cl.Action(
                name=action_name,
                payload=action_payload,
                icon=icon,
                label=label,
                tooltip=description,
            )
            high_priority_actions.append(action)

        if high_priority_actions:
            await cl.Message(
                content="high_priority_actions",
                actions=high_priority_actions,
                author="Navigation",
            ).send()

    # Display medium priority options
    if medium_priority_options:
        await cl.Message(content="**Related Actions:**", author="Navigation").send()

        medium_priority_actions = []
        for i, option in enumerate(medium_priority_options):
            action_type = option.get("action_type", "general")
            label = option.get("label", "Unknown")
            description = option.get("description", "")

            # Ensure unique name and non-empty payload
            action_name = f"medium_priority_{i}_{label.replace(' ', '_')}"
            action_payload = {"label": label, "description": description}

            # Use global lucide icons mapping
            icon = lucide_icons.get(action_type, "lightbulb")

            action = cl.Action(
                name=action_name,
                payload=action_payload,
                icon=icon,
                label=label,
                tooltip=description,
            )
            medium_priority_actions.append(action)

        if medium_priority_actions:
            await cl.Message(
                content="medium_priority_actions",
                actions=medium_priority_actions,
                author="Navigation",
            ).send()

    # Display low priority options
    if low_priority_options:
        await cl.Message(content="**Additional Options:**", author="Navigation").send()

        low_priority_actions = []
        for i, option in enumerate(low_priority_options):
            action_type = option.get("action_type", "general")
            label = option.get("label", "Unknown")
            description = option.get("description", "")

            # Ensure unique name and non-empty payload
            action_name = f"low_priority_{i}_{label.replace(' ', '_')}"
            action_payload = {"label": label, "description": description}

            # Use global lucide icons mapping
            icon = lucide_icons.get(action_type, "lightbulb")

            action = cl.Action(
                name=action_name,
                payload=action_payload,
                icon=icon,
                label=label,
                tooltip=description,
            )
            low_priority_actions.append(action)

        if low_priority_actions:
            await cl.Message(
                content="low_priority_actions",
                actions=low_priority_actions,
                author="Navigation",
            ).send()


@cl.action_callback
async def on_action(action: cl.Action):
    """Handle navigation option selections"""
    # Extract label from payload
    action_label = action.payload.get("label", "") if action.payload else ""

    # Treat action selection as a user message
    await cl.Message(content=action_label, author="User").send()

    # Process the navigation option by directly calling the API
    # instead of creating a fake message object
    session_id = cl.user_session.get("session_id")
    if not session_id:
        await cl.Message(
            content="Session not found. Please refresh the page and try again.",
            author="Assistant",
        ).send()
        return

    try:
        # Send message to API via HTTP
        request = SendMessageRequest(session_id=session_id, message=action_label)
        response = await send_message_http(request)

        # Send assistant response
        await cl.Message(
            content=response.get("response", ""), author="Assistant"
        ).send()

        # Update navigation options
        navigation_options = response.get("navigation_options", [])
        if navigation_options:
            await display_navigation_options(navigation_options)
            cl.user_session.set("navigation_options", navigation_options)

    except Exception:
        await cl.Message(
            content="Sorry, I encountered an error while processing your message. Please try again.",
            author="Assistant",
        ).send()


@cl.on_chat_end
def on_chat_end():
    """Clean up when chat ends"""
    # In Chainlit 2.x, user session data is automatically managed
    # No need to manually clear session data
    pass
