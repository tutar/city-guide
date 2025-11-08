"""
Chainlit application for City Guide Smart Assistant
"""

import uuid

import chainlit as cl

from src.api.conversation import (
    SendMessageRequest,
    StartConversationRequest,
    send_message,
    start_conversation,
)


@cl.on_chat_start
async def on_chat_start():
    """Initialize conversation when chat starts"""
    # Create a new conversation session
    session_id = str(uuid.uuid4())

    # Store session ID in user session
    cl.user_session.set("session_id", session_id)

    # Start conversation with API
    request = StartConversationRequest(
        user_session_id=session_id,
        user_preferences={"language": "zh-CN"},  # Default to Chinese
    )

    try:
        response = await start_conversation(request)

        # Send enhanced welcome message with context
        welcome_content = f"""{response.welcome_message}

**💡 How I can help you:**
- **Government Services**: Passport applications, business registration, visa services
- **Document Requirements**: Complete checklists and required materials
- **Application Process**: Step-by-step guidance for various services
- **Service Locations**: Find nearest government service centers
- **Status Tracking**: Check application progress and processing times

Feel free to ask me anything about government services!"""

        await cl.Message(content=welcome_content, author="Assistant").send()

        # Store conversation context
        cl.user_session.set("conversation_id", response.conversation_id)
        cl.user_session.set("navigation_options", response.navigation_options)

        # Display initial navigation options
        if response.navigation_options:
            await display_navigation_options(response.navigation_options)

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
        # Send message to API
        request = SendMessageRequest(session_id=session_id, message=message.content)

        response = await send_message(request)

        # Send assistant response
        await cl.Message(content=response.response, author="Assistant").send()

        # Update navigation options
        if response.navigation_options:
            await display_navigation_options(response.navigation_options)
            cl.user_session.set("navigation_options", response.navigation_options)

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

    # Define icons for different action types
    action_icons = {
        "requirements": "📋",
        "explain": "📖",
        "location": "📍",
        "appointment": "📅",
        "status": "📊",
        "contact": "📞",
        "download": "📥",
        "external": "🔗",
        "general": "💡",
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
        for option in high_priority_options:
            action_type = option.get("action_type", "general")
            icon = action_icons.get(action_type, "💡")
            action = cl.Action(
                name=option.get("label", "Unknown"),
                value=option.get("label", ""),
                description=option.get("description", ""),
                label=f"{icon} {option.get('label', 'Unknown')}",
            )
            high_priority_actions.append(action)

        if high_priority_actions:
            await cl.Message(actions=high_priority_actions, author="Navigation").send()

    # Display medium priority options
    if medium_priority_options:
        await cl.Message(content="**Related Actions:**", author="Navigation").send()

        medium_priority_actions = []
        for option in medium_priority_options:
            action_type = option.get("action_type", "general")
            icon = action_icons.get(action_type, "💡")
            action = cl.Action(
                name=option.get("label", "Unknown"),
                value=option.get("label", ""),
                description=option.get("description", ""),
                label=f"{icon} {option.get('label', 'Unknown')}",
            )
            medium_priority_actions.append(action)

        if medium_priority_actions:
            await cl.Message(
                actions=medium_priority_actions, author="Navigation"
            ).send()

    # Display low priority options
    if low_priority_options:
        await cl.Message(content="**Additional Options:**", author="Navigation").send()

        low_priority_actions = []
        for option in low_priority_options:
            action_type = option.get("action_type", "general")
            icon = action_icons.get(action_type, "💡")
            action = cl.Action(
                name=option.get("label", "Unknown"),
                value=option.get("label", ""),
                description=option.get("description", ""),
                label=f"{icon} {option.get('label', 'Unknown')}",
            )
            low_priority_actions.append(action)

        if low_priority_actions:
            await cl.Message(actions=low_priority_actions, author="Navigation").send()


@cl.action_callback
async def on_action(action: cl.Action):
    """Handle navigation option selections"""
    # Treat action selection as a user message
    await cl.Message(content=action.value, author="User").send()

    # Process the navigation option as a user message
    await on_message(cl.Message(content=action.value))


@cl.on_chat_end
def on_chat_end():
    """Clean up when chat ends"""
    # In Chainlit 2.x, user session data is automatically managed
    # No need to manually clear session data
    pass
