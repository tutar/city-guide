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

        # Send welcome message
        await cl.Message(content=response.welcome_message, author="Assistant").send()

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
    """Display navigation options as interactive elements"""
    if not navigation_options:
        return

    # Create action elements for navigation options
    actions = []

    for option in navigation_options:
        action = cl.Action(
            name=option.get("label", "Unknown"),
            value=option.get("label", ""),
            description=option.get("description", ""),
            label=option.get("label", "Unknown"),
        )
        actions.append(action)

    # Send navigation options
    if actions:
        await cl.Message(
            content="You can also:", actions=actions, author="Navigation"
        ).send()


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
    # Clear user session data
    cl.user_session.clear()
