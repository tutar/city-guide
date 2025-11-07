"""
Integration tests for conversation context management
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from src.models.conversation import ConversationContext, Message, ConversationState
from src.models.services import ServiceCategory


class TestConversationContextIntegration:
    """Integration tests for conversation context management"""

    def test_conversation_context_creation(self):
        """Test creating a conversation context with valid data"""
        # Given valid conversation context data
        session_id = "test-session-123"
        service_category_id = uuid.uuid4()

        # When creating a conversation context
        conversation = ConversationContext(
            user_session_id=session_id,
            current_service_category_id=service_category_id
        )

        # Then it should be created successfully
        assert conversation.user_session_id == session_id
        assert conversation.current_service_category_id == service_category_id
        assert conversation.conversation_history == []
        assert conversation.navigation_options == []
        assert conversation.user_preferences == {}
        assert conversation.is_active == True
        assert isinstance(conversation.id, uuid.UUID)
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.last_activity, datetime)

    def test_conversation_message_flow(self):
        """Test complete message flow in conversation context"""
        # Given a conversation context
        conversation = ConversationContext(user_session_id="test-session-456")

        # When adding multiple messages
        conversation.add_message("user", "How do I get a Hong Kong passport?")
        conversation.add_message("assistant", "To apply for a Hong Kong passport...")
        conversation.add_message("user", "What documents do I need?")
        conversation.add_message("assistant", "You'll need the following documents...")

        # Then conversation history should contain all messages
        assert len(conversation.conversation_history) == 4
        assert conversation.conversation_history[0].role == "user"
        assert conversation.conversation_history[0].content == "How do I get a Hong Kong passport?"
        assert conversation.conversation_history[1].role == "assistant"
        assert conversation.conversation_history[3].role == "assistant"

        # And last activity should be updated
        assert conversation.last_activity > conversation.created_at

    def test_recent_messages_retrieval(self):
        """Test retrieving recent messages from conversation history"""
        # Given a conversation with many messages
        conversation = ConversationContext(user_session_id="test-session-789")

        # Add 15 messages
        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            conversation.add_message(role, f"Message {i}")

        # When retrieving recent messages with default limit
        recent_messages = conversation.get_recent_messages()

        # Then should return last 10 messages
        assert len(recent_messages) == 10
        assert recent_messages[0].content == "Message 5"
        assert recent_messages[-1].content == "Message 14"

        # When retrieving recent messages with custom limit
        recent_messages_5 = conversation.get_recent_messages(limit=5)
        assert len(recent_messages_5) == 5
        assert recent_messages_5[-1].content == "Message 14"

    def test_conversation_archiving_logic(self):
        """Test conversation archiving based on activity"""
        # Given an active conversation
        conversation = ConversationContext(user_session_id="test-session-archiving")

        # When conversation is active and recently active
        conversation.last_activity = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert conversation.should_archive() == False

        # When conversation is inactive
        conversation.is_active = False
        assert conversation.should_archive() == True

        # When conversation is active but inactive for too long
        conversation.is_active = True
        conversation.last_activity = datetime.now(timezone.utc) - timedelta(minutes=35)
        assert conversation.should_archive() == True

    def test_conversation_completion(self):
        """Test marking conversation as completed"""
        # Given an active conversation
        conversation = ConversationContext(user_session_id="test-session-complete")
        assert conversation.is_active == True

        # When marking as completed
        conversation.mark_completed()

        # Then should be inactive
        assert conversation.is_active == False

    def test_conversation_history_validation(self):
        """Test conversation history size validation"""
        # Given a conversation with many messages
        conversation = ConversationContext(user_session_id="test-session-large")

        # Add 100 messages (maximum allowed)
        for i in range(100):
            conversation.add_message("user", f"Message {i}")

        # Should still be valid
        assert len(conversation.conversation_history) == 100

        # When trying to add 101st message
        conversation.add_message("user", "Message 101")

        # Should still work (validation is only on model creation)
        assert len(conversation.conversation_history) == 101

    def test_conversation_with_service_category(self):
        """Test conversation context with service category integration"""
        # Given a service category
        service_category = ServiceCategory(
            name="Hong Kong Passport Services",
            description="Passport application and renewal services"
        )

        # When creating conversation context with service category
        conversation = ConversationContext(
            user_session_id="test-session-service",
            current_service_category_id=service_category.id
        )

        # Then should reference the service category
        assert conversation.current_service_category_id == service_category.id

        # When adding messages related to the service
        conversation.add_message("user", "How do I apply for a Hong Kong passport?")
        conversation.add_message("assistant", "For Hong Kong passport applications...")

        # Then conversation should maintain context
        assert len(conversation.conversation_history) == 2
        assert "Hong Kong passport" in conversation.conversation_history[0].content

    def test_message_metadata_integration(self):
        """Test message metadata in conversation context"""
        # Given a conversation context
        conversation = ConversationContext(user_session_id="test-session-metadata")

        # When adding messages with metadata
        conversation.add_message(
            "user",
            "What are the requirements?",
            metadata={
                "intent": "requirements_query",
                "confidence": 0.95,
                "source": "user_input"
            }
        )

        conversation.add_message(
            "assistant",
            "The requirements include...",
            metadata={
                "sources_used": ["official_website", "government_guidelines"],
                "response_type": "step_by_step_guidance"
            }
        )

        # Then metadata should be preserved
        assert conversation.conversation_history[0].metadata["intent"] == "requirements_query"
        assert conversation.conversation_history[1].metadata["response_type"] == "step_by_step_guidance"

    def test_navigation_options_integration(self):
        """Test navigation options in conversation context"""
        # Given a conversation context
        conversation = ConversationContext(user_session_id="test-session-navigation")

        # When adding navigation options
        navigation_options = [
            {
                "label": "Material Requirements",
                "action_type": "requirements",
                "priority": 1
            },
            {
                "label": "Online Appointment",
                "action_type": "appointment",
                "priority": 2
            },
            {
                "label": "Service Locations",
                "action_type": "location",
                "priority": 3
            }
        ]

        conversation.navigation_options = navigation_options

        # Then navigation options should be accessible
        assert len(conversation.navigation_options) == 3
        assert conversation.navigation_options[0]["label"] == "Material Requirements"
        assert conversation.navigation_options[1]["action_type"] == "appointment"

    def test_conversation_state_transitions(self):
        """Test conversation state transitions"""
        # Given a conversation state
        state = ConversationState()
        assert state.state == "created"

        # When transitioning to active
        state.transition_to("active")
        assert state.state == "active"

        # When transitioning to inactive
        state.transition_to("inactive")
        assert state.state == "inactive"

        # When transitioning back to active
        state.transition_to("active")
        assert state.state == "active"

        # When transitioning to completed
        state.transition_to("completed")
        assert state.state == "completed"

        # Then invalid transitions should raise errors
        with pytest.raises(ValueError) as exc_info:
            state.transition_to("active")
        assert "Invalid transition" in str(exc_info.value)

    def test_conversation_state_validation(self):
        """Test conversation state validation"""
        # Given invalid state
        with pytest.raises(ValidationError) as exc_info:
            ConversationState(state="invalid_state")
        assert "State must be one of" in str(exc_info.value)

        # Given valid states
        valid_states = ["created", "active", "inactive", "completed"]
        for valid_state in valid_states:
            state = ConversationState(state=valid_state)
            assert state.state == valid_state

    def test_conversation_persistence_simulation(self):
        """Simulate conversation context persistence and retrieval"""
        # Given a conversation context with full data
        conversation = ConversationContext(
            user_session_id="test-session-persistence",
            current_service_category_id=uuid.uuid4(),
            navigation_options=[
                {"label": "Requirements", "action_type": "requirements", "priority": 1}
            ],
            user_preferences={
                "language": "en",
                "preferred_format": "step_by_step"
            }
        )

        # Add conversation history
        conversation.add_message("user", "How do I apply?")
        conversation.add_message("assistant", "Here's how to apply...")

        # When serializing to dict (simulating database storage)
        conversation_dict = conversation.model_dump()

        # Then all data should be preserved
        assert conversation_dict["user_session_id"] == "test-session-persistence"
        assert conversation_dict["current_service_category_id"] == conversation.current_service_category_id
        assert len(conversation_dict["conversation_history"]) == 2
        assert len(conversation_dict["navigation_options"]) == 1
        assert conversation_dict["user_preferences"]["language"] == "en"

        # When deserializing from dict (simulating database retrieval)
        restored_conversation = ConversationContext(**conversation_dict)

        # Then should have same data
        assert restored_conversation.user_session_id == conversation.user_session_id
        assert len(restored_conversation.conversation_history) == 2
        assert restored_conversation.conversation_history[0].content == "How do I apply?"

    def test_conversation_context_error_handling(self):
        """Test error handling in conversation context"""
        # Given invalid session ID
        with pytest.raises(ValidationError) as exc_info:
            ConversationContext(user_session_id="")
        assert "Session ID cannot be empty" in str(exc_info.value)

        # Given invalid message role
        with pytest.raises(ValidationError) as exc_info:
            Message(role="invalid", content="test")
        assert "Role must be one of" in str(exc_info.value)

        # Given empty message content
        with pytest.raises(ValidationError) as exc_info:
            Message(role="user", content="")
        assert "Content cannot be empty" in str(exc_info.value)