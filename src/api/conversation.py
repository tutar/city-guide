"""
Conversation API endpoints for City Guide Smart Assistant
"""

import asyncio
import time
import uuid
from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.attribution import SentenceAttribution
from src.models.conversation_model import ConversationContext
from src.services.data_service import DataService
from src.services.search_service import SearchService
from src.services.ai_response_service import AIResponseService
from src.utils.config import settings

from src.services.ai_service import AIService

router = APIRouter(prefix="/api/conversation", tags=["conversation"])

# Initialize services once to avoid repeated initialization
_ai_service = AIService()
_search_service = SearchService(ai_service=_ai_service)
_ai_response_service = AIResponseService()


class StartConversationRequest(BaseModel):
    """Request model for starting a conversation"""

    user_session_id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Anonymous session identifier. Auto-generated if not provided",
    )
    initial_message: str | None = Field(
        None, description="Optional initial message to start the conversation"
    )
    service_category_id: str | None = Field(
        None, description="Optional service category ID to start with specific context"
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences for personalization"
    )


class StartConversationResponse(BaseModel):
    """Response model for starting a conversation"""

    session_id: str = Field(..., description="Session identifier for this conversation")
    conversation_id: str = Field(..., description="Unique conversation identifier")
    service_context: dict[str, Any] | None = Field(
        None, description="Service context if starting with specific service"
    )


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""

    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message content")


class AttributionData(BaseModel):
    """Attribution data for document sources"""

    sentence_attributions: list[dict[str, Any]] = Field(
        default_factory=list, description="Sentence-level document attributions"
    )
    citation_list: dict[str, Any] = Field(
        default_factory=dict, description="Complete citation list"
    )
    fallback_mode: bool = Field(
        False, description="Whether attribution is in fallback mode"
    )


class SendMessageResponse(BaseModel):
    """Response model for sending a message"""

    response: str = Field(..., description="Assistant response")
    formatted_response: str = Field(..., description="Formatted assistant response")
    conversation_history: list = Field(..., description="Updated conversation history")
    usage: dict[str, Any] | None = Field(
        None, description="API usage information if available"
    )
    sentence_attributions: list = Field(
        ..., description="Sentence-level document attributions"
    )


@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """
    Start a new conversation with optional service context

    Creates a new conversation session with welcome message and initial
    navigation options based on service context if provided.
    """
    try:
        # Initialize services
        with DataService() as data_service:
            ai_service = _ai_service

            # Check if session already exists
            existing_context = data_service.get_conversation_context(
                request.user_session_id
            )
            if existing_context:
                # Return existing session
                return StartConversationResponse(
                    session_id=existing_context.user_session_id,
                    conversation_id=str(existing_context.id),
                    service_context={
                        "service_category_id": str(
                            existing_context.current_service_category_id
                        )
                    }
                    if existing_context.current_service_category_id
                    else None,
                )

            # Create new conversation context
            conversation_context = ConversationContext(
                user_session_id=request.user_session_id,
                user_preferences=request.user_preferences,
            )

            # Set service context if provided
            if request.service_category_id:
                try:
                    service_category_id = uuid.UUID(request.service_category_id)
                    service_category = data_service.get_service_category(
                        service_category_id
                    )
                    if service_category:
                        conversation_context.current_service_category_id = (
                            service_category_id
                        )

                        service_context = {
                            "service_category_id": str(service_category_id),
                            "service_name": service_category.name,
                            "service_description": service_category.description,
                        }
                    else:
                        service_context = None
                except ValueError:
                    service_context = None
            else:
                service_context = None

            # Save conversation context
            saved_context = data_service.create_conversation_context(
                conversation_context
            )

            return StartConversationResponse(
                session_id=saved_context.user_session_id,
                conversation_id=str(saved_context.id),
                service_context=service_context,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start conversation: {str(e)}"
        )


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send a message in an existing conversation

    Processes user message and returns assistant response with updated
    navigation options and conversation history.
    """
    # Performance monitoring
    timings = {}

    try:
        # Start total timing
        total_start = time.time()

        with DataService() as data_service:
            # Use pre-initialized services to avoid repeated initialization
            search_service = _search_service
            ai_service = _ai_service
            timings["service_init"] = 0.0  # Service initialization is now zero-cost

            # Get existing conversation context
            context_start = time.time()
            conversation_context = data_service.get_conversation_context(
                request.session_id
            )
            if not conversation_context:
                raise HTTPException(status_code=404, detail="Conversation not found")
            timings["get_context"] = time.time() - context_start

            # Add user message to conversation
            add_message_start = time.time()
            conversation_context.add_message("user", request.message)
            timings["add_user_message"] = time.time() - add_message_start

            # Parallel execution: search documents and get navigation options concurrently
            parallel_start = time.time()

            # Create tasks for parallel execution
            search_task = asyncio.create_task(
                search_service.search_documents(
                    query=request.message,
                    service_category_id=conversation_context.current_service_category_id,
                )
            )

            # Get conversation history as dictionaries (optimized)
            convert_start = time.time()
            conversation_history_dicts = conversation_context.get_recent_messages_dict()
            timings["convert_history"] = time.time() - convert_start

            # Wait for both tasks to complete
            search_results = await search_task
            timings["parallel_operations"] = time.time() - parallel_start

            # Generate AI response with attribution
            ai_start = time.time()
            response = _ai_response_service.generate_response_with_attribution(
                user_query=request.message,
                context_documents=search_results,
                conversation_history=conversation_history_dicts,
            )
            timings["ai_generation"] = time.time() - ai_start

            # Add assistant response to conversation
            add_assistant_start = time.time()
            conversation_context.add_message("assistant", response["response"])
            timings["add_assistant_message"] = time.time() - add_assistant_start

            # Save updated conversation context
            save_start = time.time()
            updated_context = data_service.update_conversation_context(
                request.session_id, conversation_context
            )
            timings["save_context"] = time.time() - save_start

            # Calculate total time
            timings["total"] = time.time() - total_start

            # Log performance metrics
            print(f"Performance metrics for send_message:")
            for step, duration in timings.items():
                print(f"  {step}: {duration:.3f}s")

            return SendMessageResponse(
                response=response["response"],
                formatted_response=response["formatted_response"],
                conversation_history=[
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in updated_context.conversation_history
                ],
                sentence_attributions=response.get("sentence_attributions"),
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


@router.get("/{session_id}/history")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session

    Returns the complete conversation history for the given session.
    """
    try:
        with DataService() as data_service:
            conversation_context = data_service.get_conversation_context(session_id)
            if not conversation_context:
                raise HTTPException(status_code=404, detail="Conversation not found")

            return {
                "session_id": conversation_context.user_session_id,
                "conversation_id": str(conversation_context.id),
                "history": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata,
                    }
                    for msg in conversation_context.conversation_history
                ],
                "current_service_category_id": str(
                    conversation_context.current_service_category_id
                )
                if conversation_context.current_service_category_id
                else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversation history: {str(e)}"
        )
