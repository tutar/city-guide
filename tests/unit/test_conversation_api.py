"""
Unit tests for conversation API endpoints
"""

import uuid
from datetime import UTC
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.conversation import router
from src.models.conversation_model import ConversationContext, Message


@pytest.fixture
def test_client():
    """Create test client for conversation API"""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestConversationAPI:
    """Test suite for conversation API endpoints"""

    def test_start_conversation_success(self, test_client):
        """Test successful conversation start"""
        # Mock dependencies
        mock_conversation_context = Mock(spec=ConversationContext)
        mock_conversation_context.user_session_id = "test-session-123"
        mock_conversation_context.id = uuid.uuid4()
        mock_conversation_context.navigation_options = []
        mock_conversation_context.current_service_category_id = None

        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = None
                    mock_data_instance.create_conversation_context.return_value = (
                        mock_conversation_context
                    )

                    mock_search_instance = mock_search_service.return_value
                    mock_search_instance.search_documents.return_value = []

                    mock_ai_instance = mock_ai_service.return_value
                    mock_ai_instance.generate_government_guidance.return_value = {
                        "response": "Test response",
                        "usage": {"total_tokens": 100},
                        "model": "deepseek-chat",
                        "context_documents_used": 0,
                    }

                    # When starting conversation
                    response = test_client.post(
                        "/api/conversation/start",
                        json={
                            "user_session_id": "test-session-123",
                            "initial_message": "Hello, I need help with passport",
                        },
                    )

                    # Then should return success
                    assert response.status_code == 200
                    data = response.json()
                    assert data["session_id"] == "test-session-123"
                    assert "conversation_id" in data
                    assert "welcome_message" in data
                    assert data["navigation_options"] == []

    def test_start_conversation_existing_session(self, test_client):
        """Test starting conversation with existing session"""
        # Mock existing conversation context
        mock_conversation_context = Mock(spec=ConversationContext)
        mock_conversation_context.user_session_id = "existing-session"
        mock_conversation_context.id = uuid.uuid4()
        mock_conversation_context.navigation_options = [{"label": "Test Option"}]
        mock_conversation_context.current_service_category_id = None

        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = (
                        mock_conversation_context
                    )

                    mock_search_service.return_value
                    mock_ai_service.return_value

                    # When starting conversation with existing session
                    response = test_client.post(
                        "/api/conversation/start",
                        json={"user_session_id": "existing-session"},
                    )

                    # Then should return existing session
                    assert response.status_code == 200
                    data = response.json()
                    assert data["session_id"] == "existing-session"
                    assert data["navigation_options"] == [{"label": "Test Option"}]

    def test_start_conversation_with_service_context(self, test_client):
        """Test starting conversation with service context"""
        # Mock service category
        mock_service_category = Mock()
        mock_service_category.id = uuid.uuid4()
        mock_service_category.name = "Passport Services"
        mock_service_category.description = "Passport application and renewal"

        # Mock conversation context
        mock_conversation_context = Mock(spec=ConversationContext)
        mock_conversation_context.user_session_id = "service-session"
        mock_conversation_context.id = uuid.uuid4()
        mock_conversation_context.navigation_options = [
            {"label": "Requirements", "action_type": "info"}
        ]
        mock_conversation_context.current_service_category_id = mock_service_category.id

        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = None
                    mock_data_instance.get_service_category.return_value = (
                        mock_service_category
                    )
                    mock_data_instance.get_navigation_options_by_category.return_value = [
                        Mock(
                            label="Requirements",
                            action_type="info",
                            target_url=None,
                            description="Requirements",
                        )
                    ]
                    mock_data_instance.create_conversation_context.return_value = (
                        mock_conversation_context
                    )

                    mock_search_service.return_value
                    mock_ai_service.return_value

                    # When starting conversation with service context
                    response = test_client.post(
                        "/api/conversation/start",
                        json={
                            "user_session_id": "service-session",
                            "service_category_id": str(mock_service_category.id),
                        },
                    )

                    # Then should return service context
                    assert response.status_code == 200
                    data = response.json()
                    assert data["session_id"] == "service-session"
                    assert data["service_context"] is not None
                    assert data["navigation_options"] == [
                        {"label": "Requirements", "action_type": "info"}
                    ]

    def test_send_message_success(self, test_client):
        """Test successful message sending"""
        # Mock conversation context
        mock_conversation_context = Mock(spec=ConversationContext)
        mock_conversation_context.user_session_id = "test-session"
        mock_conversation_context.id = uuid.uuid4()
        mock_conversation_context.navigation_options = []
        mock_conversation_context.current_service_category_id = None
        mock_conversation_context.conversation_history = []
        mock_conversation_context.get_recent_messages.return_value = []

        # Mock AI service response
        mock_ai_response = {
            "response": "Here's how to apply for a passport...",
            "navigation_suggestions": [
                {"label": "Make appointment", "action_type": "appointment"}
            ],
            "usage": {"total_tokens": 100},
        }

        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = (
                        mock_conversation_context
                    )
                    mock_data_instance.update_conversation_context.return_value = (
                        mock_conversation_context
                    )

                    mock_search_instance = mock_search_service.return_value
                    mock_search_instance.search_documents.return_value = []

                    mock_ai_instance = mock_ai_service.return_value
                    mock_ai_instance.generate_government_guidance.return_value = (
                        mock_ai_response
                    )

                    # When sending message
                    response = test_client.post(
                        "/api/conversation/message",
                        json={
                            "session_id": "test-session",
                            "message": "How do I apply for a passport?",
                        },
                    )

                    # Then should return success
                    assert response.status_code == 200
                    data = response.json()
                    assert data["response"] == "Here's how to apply for a passport..."
                    assert data["navigation_options"] == [
                        {"label": "Make appointment", "action_type": "appointment"}
                    ]
                    assert data["usage"]["total_tokens"] == 100

    def test_send_message_conversation_not_found(self, test_client):
        """Test sending message to non-existent conversation"""
        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = None

                    mock_search_service.return_value
                    mock_ai_service.return_value

                    # When sending message to non-existent conversation
                    response = test_client.post(
                        "/api/conversation/message",
                        json={"session_id": "non-existent-session", "message": "Hello"},
                    )

                    # Then should return 404
                    assert response.status_code == 404
                    assert "Conversation not found" in response.json()["detail"]

    def test_get_conversation_history_success(self, test_client):
        """Test successful conversation history retrieval"""
        # Mock conversation context with history
        mock_conversation_context = Mock(spec=ConversationContext)
        mock_conversation_context.user_session_id = "test-session"
        mock_conversation_context.id = uuid.uuid4()
        mock_conversation_context.navigation_options = []
        mock_conversation_context.current_service_category_id = None

        # Create actual Message objects
        from datetime import datetime

        test_timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        mock_message = Message(
            role="user", content="Test message", timestamp=test_timestamp, metadata={}
        )

        mock_conversation_context.conversation_history = [mock_message]

        with patch("src.api.conversation.DataService") as mock_data_service:
            with patch("src.api.conversation.SearchService") as mock_search_service:
                with patch("src.api.conversation.AIService") as mock_ai_service:
                    mock_data_instance = (
                        mock_data_service.return_value.__enter__.return_value
                    )
                    mock_data_instance.get_conversation_context.return_value = (
                        mock_conversation_context
                    )

                    mock_search_service.return_value
                    mock_ai_service.return_value

                    # When getting conversation history
                    response = test_client.get("/api/conversation/test-session/history")

                    # Then should return history
                    assert response.status_code == 200
                    data = response.json()
                    assert data["session_id"] == "test-session"
                    assert len(data["history"]) == 1
                    assert data["history"][0]["role"] == "user"

    def test_get_conversation_history_not_found(self, test_client):
        """Test conversation history retrieval for non-existent conversation"""
        with patch("src.api.conversation.DataService") as mock_data_service:
            mock_instance = mock_data_service.return_value.__enter__.return_value
            mock_instance.get_conversation_context.return_value = None

            # When getting history for non-existent conversation
            response = test_client.get("/api/conversation/non-existent/history")

            # Then should return 404
            assert response.status_code == 404
            assert "Conversation not found" in response.json()["detail"]
