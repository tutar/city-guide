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
from src.chainlit.components.attribution_display import attribution_display
from src.chainlit.handlers.document_navigation import (
    handle_document_preview,
    handle_document_navigation,
    handle_bulk_document_access,
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


@cl.set_starters
async def set_starters():
    """suggestions to help user get started with this assistant."""
    return [
        cl.Starter(label="🏢办事指南", message="请提供本市最新的办事指南，包括户籍办理、社保转移等政务流程"),
        cl.Starter(label="🚦交通", message="查询本市实时交通状况，主要拥堵路段及绕行建议"),
        cl.Starter(label="🚇地铁", message="获取本市地铁线路图、运营时间表及换乘指南"),
        cl.Starter(label="🎓教育", message="推荐本市优质中小学及最新教育政策解读"),
        cl.Starter(label="👨‍👩‍👧亲子", message="寻找适合3-12岁儿童的周末活动场所和亲子项目"),
        cl.Starter(label="🌴旅游", message="推荐本市必游景点及隐藏打卡地，避开人流高峰时段"),
        cl.Starter(label="🗺️攻略", message="生成一份三日游详细攻略，包含住宿、美食、交通一体化方案"),
        cl.Starter(label="💼招聘", message="查找本市科技/金融行业最新招聘信息及薪资范围"),
        cl.Starter(label="💰特惠", message="汇总今日餐饮、购物、娱乐特惠活动，含独家折扣码"),
        cl.Starter(label="🏠生活指南", message="提供水电维修、社区服务、便民设施等生活实用信息"),
    ]


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

        # Store conversation context
        cl.user_session.set("conversation_id", response.get("conversation_id"))
        # Do not init navigation options because no content yet

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

        # Send assistant response with attribution
        attribution_data = response.get("attribution")
        if attribution_data:
            # Use attribution display component
            await attribution_display.display_response_with_attribution(
                response_text=response.get("response", ""),
                attribution_data=attribution_data,
            )
        else:
            # Fallback to basic message display
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
                content="**Recommended Next Steps:**",
                actions=high_priority_actions,
                author="Navigation",
            ).send()

    # Display medium priority options
    if medium_priority_options:
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
                content="**Related Actions:**",
                actions=medium_priority_actions,
                author="Navigation",
            ).send()

    # Display low priority options
    if low_priority_options:
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
                content="**Additional Options:**",
                actions=low_priority_actions,
                author="Navigation",
            ).send()


@cl.action_callback
async def on_action(action: cl.Action):
    """Handle navigation option selections and document actions"""
    # Check if this is a document navigation action
    action_type = action.payload.get("action_type", "") if action.payload else ""
    document_id = action.payload.get("document_id", "") if action.payload else ""

    if action_type and document_id:
        # Handle document navigation action
        await handle_document_navigation_action(action_type, document_id, action.name)
        return

    # Handle regular navigation option selections
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

        # Send assistant response with attribution
        attribution_data = response.get("attribution")
        if attribution_data:
            # Use attribution display component
            await attribution_display.display_response_with_attribution(
                response_text=response.get("response", ""),
                attribution_data=attribution_data,
            )
        else:
            # Fallback to basic message display
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


async def handle_document_navigation_action(
    action_type: str, document_id: str, action_name: str
):
    """Handle document navigation actions (preview, open, download)."""
    session_id = cl.user_session.get("session_id")
    if not session_id:
        await cl.Message(
            content="Session not found. Please refresh the page and try again.",
            author="Assistant",
        ).send()
        return

    try:
        # Handle the document navigation action
        result = await handle_document_navigation(
            action_type=action_type,
            document_id=document_id,
            user_session_id=session_id,
            message_id=action_name,
        )

        if result["success"]:
            # Show success message
            await cl.Message(
                content=result.get("message", "Document action completed"),
                author="Document Navigation",
            ).send()

            # If this was a preview action, show the preview
            if action_type == "preview" and "preview" in result:
                from src.chainlit.handlers.document_navigation import (
                    DocumentNavigationHandler,
                )

                handler = DocumentNavigationHandler()
                await handler.send_document_preview_message(
                    document_id=document_id,
                    preview_data=result["preview"],
                    user_session_id=session_id,
                )
        else:
            # Show error message
            await cl.Message(
                content=f"Failed to perform document action: {result.get('error', 'Unknown error')}",
                author="Document Navigation",
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"Error handling document action: {str(e)}",
            author="Document Navigation",
        ).send()


@cl.on_chat_end
def on_chat_end():
    """Clean up when chat ends"""
    # In Chainlit 2.x, user session data is automatically managed
    # No need to manually clear session data
    pass
