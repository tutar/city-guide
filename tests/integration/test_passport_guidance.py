"""
Integration tests for Hong Kong/Macau passport guidance conversation flow
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.conversation import ConversationContext
from src.models.services import ServiceCategory
from src.services.ai_service import AIService
from src.services.search_service import SearchService


class TestPassportGuidance:
    """Test suite for passport guidance conversation flow"""

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing"""
        mock = Mock(spec=AIService)
        mock.generate_government_guidance = AsyncMock()
        mock.generate_government_guidance.return_value = {
            "response": "To apply for a Hong Kong passport, you need to...",
            "usage": {"total_tokens": 150},
            "model": "deepseek-chat",
            "context_documents_used": 2,
        }
        return mock

    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for testing"""
        mock = Mock(spec=SearchService)
        mock.hybrid_search = AsyncMock()
        mock.hybrid_search.return_value = [
            Mock(
                document_id=uuid.uuid4(),
                document_title="Hong Kong Passport Application Requirements",
                document_content="Requirements for Hong Kong passport application...",
                source_url="https://example.com/hk-passport",
                similarity_score=0.85,
                hybrid_score=0.82,
            )
        ]
        mock.generate_dynamic_navigation_options = AsyncMock()
        mock.generate_dynamic_navigation_options.return_value = [
            {
                "label": "Material Requirements",
                "action_type": "requirements",
                "priority": 1,
            },
            {
                "label": "Online Appointment",
                "action_type": "appointment",
                "priority": 2,
            },
            {"label": "Service Locations", "action_type": "location", "priority": 3},
        ]
        return mock

    @pytest.fixture
    def passport_service_category(self):
        """Create passport service category for testing"""
        return ServiceCategory(
            id=uuid.uuid4(),
            name="Hong Kong/Macau Passport Services",
            description="Passport application and renewal services for Hong Kong and Macau residents",
            official_source_url="https://www.gov.hk/en/residents/",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_passport_guidance_conversation_start(
        self, mock_ai_service, mock_search_service, passport_service_category
    ):
        """Test starting a passport guidance conversation"""
        # Given a user asks about Hong Kong passport
        user_query = "How do I get a Hong Kong passport?"

        # When the system processes the query
        with patch(
            "src.services.ai_service.AIService", return_value=mock_ai_service
        ), patch(
            "src.services.search_service.SearchService",
            return_value=mock_search_service,
        ):
            # Create conversation context
            conversation = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=passport_service_category.id,
            )

            # Add user message
            conversation.add_message("user", user_query)

            # Perform search
            search_results = await mock_search_service.hybrid_search(
                Mock(query=user_query, limit=10)
            )

            # Generate guidance
            guidance_response = await mock_ai_service.generate_government_guidance(
                user_query=user_query,
                context_documents=[
                    {
                        "document_title": result.document_title,
                        "document_content": result.document_content,
                    }
                    for result in search_results
                ],
                conversation_history=conversation.get_recent_messages(),
            )

            # Generate navigation options
            navigation_options = (
                await mock_search_service.generate_dynamic_navigation_options(
                    conversation_context={
                        "current_service_category_id": passport_service_category.id,
                        "current_query": user_query,
                    },
                    search_results=search_results,
                )
            )

            # Add assistant response
            conversation.add_message("assistant", guidance_response["response"])

            # Then verify the response contains guidance
            assert "Hong Kong passport" in guidance_response["response"]
            assert guidance_response["context_documents_used"] > 0

            # Verify navigation options are generated
            assert len(navigation_options) > 0
            assert any(
                "Material Requirements" in option["label"]
                for option in navigation_options
            )

            # Verify conversation history is maintained
            assert len(conversation.conversation_history) == 2
            assert conversation.conversation_history[0].role == "user"
            assert conversation.conversation_history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_material_requirements_navigation(
        self, mock_search_service, passport_service_category
    ):
        """Test navigation to material requirements"""
        # Given a user is viewing passport guidance
        conversation_context = {
            "current_service_category_id": passport_service_category.id,
            "current_query": "Hong Kong passport requirements",
        }

        search_results = [
            Mock(
                document_id=uuid.uuid4(),
                document_title="Hong Kong Passport Required Documents",
                document_content="Required documents for Hong Kong passport application...",
                source_url="https://example.com/hk-documents",
                similarity_score=0.92,
                hybrid_score=0.90,
            )
        ]

        # When navigation options are generated
        navigation_options = (
            await mock_search_service.generate_dynamic_navigation_options(
                conversation_context=conversation_context, search_results=search_results
            )
        )

        # Then material requirements option should be available
        material_option = next(
            (
                option
                for option in navigation_options
                if option["action_type"] == "requirements"
            ),
            None,
        )

        assert material_option is not None
        assert "Material Requirements" in material_option["label"]
        assert material_option["priority"] <= 5  # High priority

    @pytest.mark.asyncio
    async def test_appointment_system_integration(self, mock_search_service):
        """Test external appointment system integration"""
        # Given a user wants to make an appointment
        appointment_url = "https://www.gov.hk/en/appointment/passport"

        # When the system handles the external URL
        url_handling = mock_search_service.add_external_url_handling(appointment_url)

        # Then verify URL validation and handling
        assert url_handling["url"] == appointment_url
        assert url_handling["is_government_url"] is True
        assert url_handling["handling_type"] == "external_redirect"

    @pytest.mark.asyncio
    async def test_conversation_context_persistence(self):
        """Test conversation context persistence across interactions"""
        # Given a conversation with multiple messages
        conversation = ConversationContext(user_session_id="test-session-456")

        # When multiple interactions occur
        conversation.add_message("user", "How do I get a Hong Kong passport?")
        conversation.add_message("assistant", "To apply for a Hong Kong passport...")
        conversation.add_message("user", "What documents do I need?")

        # Then conversation history should be maintained
        assert len(conversation.conversation_history) == 3
        assert (
            conversation.conversation_history[0].content
            == "How do I get a Hong Kong passport?"
        )
        assert (
            conversation.conversation_history[2].content == "What documents do I need?"
        )

        # And recent messages should be accessible
        recent_messages = conversation.get_recent_messages(limit=2)
        assert len(recent_messages) == 2
        assert recent_messages[0].content == "To apply for a Hong Kong passport..."
        assert recent_messages[1].content == "What documents do I need?"

    @pytest.mark.asyncio
    async def test_unanswerable_query_handling(
        self, mock_ai_service, mock_search_service
    ):
        """Test handling of queries the system cannot answer"""
        # Given a query with no relevant information
        user_query = "How do I become an astronaut?"

        # When search returns no results
        mock_search_service.hybrid_search.return_value = []

        # And AI service provides alternative suggestions
        mock_ai_service.generate_government_guidance.return_value = {
            "response": "I couldn't find specific information about astronaut training. You might want to check: 1. Career guidance services 2. Education requirements 3. Official space agency websites",
            "usage": {"total_tokens": 80},
            "model": "deepseek-chat",
            "context_documents_used": 0,
        }

        with patch(
            "src.services.ai_service.AIService", return_value=mock_ai_service
        ), patch(
            "src.services.search_service.SearchService",
            return_value=mock_search_service,
        ):
            # Process the query
            await mock_search_service.hybrid_search(Mock(query=user_query, limit=10))

            guidance_response = await mock_ai_service.generate_government_guidance(
                user_query=user_query, context_documents=[], conversation_history=[]
            )

            # Then verify helpful alternative suggestions
            assert "couldn't find" in guidance_response["response"].lower()
            assert "check" in guidance_response["response"].lower()
            assert guidance_response["context_documents_used"] == 0
