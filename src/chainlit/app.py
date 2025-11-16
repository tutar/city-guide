"""
Chainlit application for City Guide Smart Assistant
"""

from typing import List
import uuid

import chainlit as cl
import httpx

from src.api.conversation import (
    SendMessageRequest,
    StartConversationRequest,
)
from src.chainlit.components.attribution_display import attribution_display

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


async def document_preview_http(document_ids: List[str]):
    """Get document preview via HTTP call to FastAPI"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FASTAPI_BASE_URL}/api/documents/citations",
            params={"document_ids": document_ids},
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


@cl.action_callback("display_reference_sidebar")
async def on_action(action: cl.Action):
    response_id = action.payload.get("response_id", "") if action.payload else ""

    elements = []
    # elements.append(cl.Text(content="1. title 1 \n\n contnet 1",name="^1"))
    # elements.append(cl.Text(content="2. title 2 \n\n contnet 2",name="^2"))
    if response_id:
        sentence_attributions = attribution_display.get_cached_sentence_attributions(
            response_id
        )
        for index, attr in enumerate(sentence_attributions):
            i = index + 1
            doc = attr.get("document", {})
            if doc:
                elements.append(
                    cl.Text(
                        content=f"""^{i}. {doc.get("document_title", "Unknown")} \n\n {doc.get("document_content", "")[:15] + "..."}""",
                        name=f"{i}",
                    )
                )

    # Setting elements will open the sidebar
    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("搜索结果")


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

    except Exception as e:
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
        attribution_data = response.get("sentence_attributions")

        if attribution_data:
            response_id = attribution_data[0].get("response_id")
            attribution_display.cache_sentence_attributions(
                response_id=response_id,
                attributions=attribution_data,
            )

            message_actions = []
            action_payload = {"response_id": response_id}
            display_reference_action = cl.Action(
                name="display_reference_sidebar",
                payload=action_payload,
                label="已阅读结果",
            )
            message_actions.append(display_reference_action)
            # Create new message
            return await cl.Message(
                content=response.get("formatted_response", ""),
                author="Assistant",
                actions=message_actions,
            ).send()

        # Create new message
        return await cl.Message(
            content=response.get("formatted_response", ""),
            author="Assistant",
        ).send()

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
