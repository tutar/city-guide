"""
Conversation API endpoints for City Guide Smart Assistant
"""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.models.conversation import ConversationContext
from src.services.ai_service import AIService
from src.services.data_service import DataService
from src.services.search_service import SearchService

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


class StartConversationRequest(BaseModel):
    """Request model for starting a conversation"""

    user_session_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Anonymous session identifier. Auto-generated if not provided",
    )
    initial_message: Optional[str] = Field(
        None, description="Optional initial message to start the conversation"
    )
    service_category_id: Optional[str] = Field(
        None, description="Optional service category ID to start with specific context"
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences for personalization"
    )


class StartConversationResponse(BaseModel):
    """Response model for starting a conversation"""

    session_id: str = Field(..., description="Session identifier for this conversation")
    conversation_id: str = Field(..., description="Unique conversation identifier")
    welcome_message: str = Field(..., description="Welcome message from the assistant")
    navigation_options: list = Field(..., description="Initial navigation options")
    service_context: Optional[dict[str, Any]] = Field(
        None, description="Service context if starting with specific service"
    )


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""

    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message content")


class SendMessageResponse(BaseModel):
    """Response model for sending a message"""

    response: str = Field(..., description="Assistant response")
    navigation_options: list = Field(..., description="Updated navigation options")
    conversation_history: list = Field(..., description="Updated conversation history")
    usage: Optional[dict[str, Any]] = Field(
        None, description="API usage information if available"
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
            search_service = SearchService()
            ai_service = AIService()

            # Check if session already exists
            existing_context = data_service.get_conversation_context(
                request.user_session_id
            )
            if existing_context:
                # Return existing session
                return StartConversationResponse(
                    session_id=existing_context.user_session_id,
                    conversation_id=str(existing_context.id),
                    welcome_message="Welcome back! How can I help you today?",
                    navigation_options=existing_context.navigation_options,
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

                        # Get navigation options for this service
                        nav_options = data_service.get_navigation_options_by_category(
                            service_category_id
                        )
                        conversation_context.navigation_options = [
                            {
                                "label": option.label,
                                "action_type": option.action_type,
                                "target_url": option.target_url,
                                "description": option.description,
                            }
                            for option in nav_options
                        ]

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

            # Generate welcome message based on context
            if service_context:
                welcome_message = f"Welcome! I can help you with {service_context['service_name']}. What would you like to know?"
            else:
                welcome_message = "Welcome to the City Guide Smart Assistant! I can help you navigate government services. What would you like to know about?"

            # Add welcome message to conversation
            conversation_context.add_message("assistant", welcome_message)

            # If initial message provided, process it
            if request.initial_message:
                conversation_context.add_message("user", request.initial_message)

                # Process the message with AI service
                response = ai_service.generate_government_guidance(
                    user_query=request.initial_message,
                    context_documents=[],  # Will be populated by search service
                    conversation_history=conversation_context.get_recent_messages(),
                )

                conversation_context.add_message("assistant", response["response"])

                # Update navigation options based on response
                if response.get("navigation_suggestions"):
                    conversation_context.navigation_options.extend(
                        response["navigation_suggestions"]
                    )

            # Save conversation context
            saved_context = data_service.create_conversation_context(
                conversation_context
            )

            return StartConversationResponse(
                session_id=saved_context.user_session_id,
                conversation_id=str(saved_context.id),
                welcome_message=welcome_message,
                navigation_options=saved_context.navigation_options,
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
    try:
        with DataService() as data_service:
            search_service = SearchService()
            ai_service = AIService()

            # Get existing conversation context
            conversation_context = data_service.get_conversation_context(
                request.session_id
            )
            if not conversation_context:
                raise HTTPException(status_code=404, detail="Conversation not found")

            # Add user message to conversation
            conversation_context.add_message("user", request.message)

            # Search for relevant documents
            search_results = search_service.search_documents(
                query=request.message,
                service_category_id=conversation_context.current_service_category_id,
            )

            # Generate AI response
            response = ai_service.generate_government_guidance(
                user_query=request.message,
                context_documents=search_results,
                conversation_history=conversation_context.get_recent_messages(),
            )

            # Add assistant response to conversation
            conversation_context.add_message("assistant", response["response"])

            # Update navigation options
            if response.get("navigation_suggestions"):
                conversation_context.navigation_options = response[
                    "navigation_suggestions"
                ]

            # Save updated conversation context
            updated_context = data_service.update_conversation_context(
                request.session_id, conversation_context
            )

            return SendMessageResponse(
                response=response["response"],
                navigation_options=updated_context.navigation_options,
                conversation_history=[
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in updated_context.conversation_history
                ],
                usage=response.get("usage"),
            )

    except HTTPException:
        raise
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
                "navigation_options": conversation_context.navigation_options,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversation history: {str(e)}"
        )
