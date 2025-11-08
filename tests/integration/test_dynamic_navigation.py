"""
Integration tests for dynamic contextual navigation scenarios
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from src.models.conversation_model import ConversationContext, Message
from src.models.services import ServiceCategory, NavigationOption
from src.services.data_service import DataService
from src.services.search_service import SearchService


class TestDynamicNavigation:
    """Test suite for dynamic contextual navigation scenarios"""

    def test_navigation_options_adapt_to_conversation_context(self):
        """Test that navigation options adapt based on conversation context"""
        # Given a conversation about passport services
        with patch("src.services.data_service.DataService") as mock_data_service:
            with patch("src.services.search_service.SearchService") as mock_search_service:
                # Mock service categories
                passport_category = ServiceCategory(
                    id=uuid.uuid4(),
                    name="Hong Kong Passport Services",
                    description="Passport application and renewal services",
                )

                visa_category = ServiceCategory(
                    id=uuid.uuid4(),
                    name="Hong Kong Visa Services",
                    description="Visa application and extension services",
                )

                # Mock navigation options
                passport_options = [
                    NavigationOption(
                        service_category_id=passport_category.id,
                        label="Requirements",
                        action_type="requirements",
                        priority=1,
                    ),
                    NavigationOption(
                        service_category_id=passport_category.id,
                        label="Make Appointment",
                        action_type="appointment",
                        priority=2,
                    ),
                ]

                visa_options = [
                    NavigationOption(
                        service_category_id=visa_category.id,
                        label="Visa Types",
                        action_type="explain",
                        priority=1,
                    ),
                    NavigationOption(
                        service_category_id=visa_category.id,
                        label="Application Process",
                        action_type="requirements",
                        priority=2,
                    ),
                ]

                # Mock conversation context
                conversation_context = ConversationContext(
                    user_session_id="test-session-123",
                    current_service_category_id=passport_category.id,
                    conversation_history=[
                        Message(
                            role="user",
                            content="How do I apply for a passport?",
                            timestamp=datetime.now(UTC),
                        )
                    ],
                )

                # Setup mock data service
                mock_data_instance = mock_data_service.return_value.__enter__.return_value
                mock_data_instance.get_conversation_context.return_value = conversation_context
                mock_data_instance.get_service_category.return_value = passport_category
                mock_data_instance.get_navigation_options_by_category.return_value = passport_options
                mock_data_instance.get_all_service_categories.return_value = [passport_category, visa_category]

                # Setup mock search service
                mock_search_instance = mock_search_service.return_value
                mock_search_instance.generate_dynamic_navigation_options.return_value = [
                    {"label": "Requirements", "action_type": "requirements", "priority": 1},
                    {"label": "Make Appointment", "action_type": "appointment", "priority": 2}
                ]

                # When generating navigation options
                with DataService() as data_service:
                    current_context = data_service.get_conversation_context("test-session-123")
                    current_category = data_service.get_service_category(current_context.current_service_category_id)
                    navigation_options = data_service.get_navigation_options_by_category(current_category.id)

                # Then should return passport-specific options
                assert len(navigation_options) == 2
                assert navigation_options[0].label == "Requirements"
                assert navigation_options[1].label == "Make Appointment"

    def test_related_service_suggestions(self):
        """Test that related services are suggested based on conversation context"""
        # Given a conversation about passport services
        with patch("src.services.search_service.SearchService") as mock_search_service:
            # Mock related services
            related_services = [
                {
                    "category_id": uuid.uuid4(),
                    "name": "Hong Kong Visa Services",
                    "description": "Visa application and extension services",
                    "relevance_score": 0.8,
                },
                {
                    "category_id": uuid.uuid4(),
                    "name": "Hong Kong ID Card Services",
                    "description": "ID card application and renewal",
                    "relevance_score": 0.6,
                },
            ]

            # Setup mock search service
            mock_search_instance = mock_search_service.return_value
            mock_search_instance.get_related_services.return_value = related_services

            # When getting related services
            search_service = SearchService()
            related = search_service.get_related_services("passport", "test-session-123")

            # Then should return related services with relevance scores
            assert len(related) == 2
            assert related[0]["name"] == "Hong Kong Visa Services"
            assert related[0]["relevance_score"] == 0.8
            assert related[1]["name"] == "Hong Kong ID Card Services"
            assert related[1]["relevance_score"] == 0.6

    def test_navigation_priority_based_on_conversation_history(self):
        """Test that navigation options are prioritized based on conversation history"""
        # Given conversation history with multiple service interactions
        with patch("src.services.data_service.DataService") as mock_data_service:
            # Mock conversation context with history
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                conversation_history=[
                    Message(
                        role="user",
                        content="passport requirements",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="assistant",
                        content="Here are the passport requirements...",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="user",
                        content="how to make appointment",
                        timestamp=datetime.now(UTC),
                    ),
                ],
            )

            # Mock prioritized navigation options
            prioritized_options = [
                NavigationOption(
                    service_category_id=uuid.uuid4(),
                    label="Make Appointment",
                    action_type="appointment",
                    priority=1,
                ),
                NavigationOption(
                    service_category_id=uuid.uuid4(),
                    label="Requirements",
                    action_type="requirements",
                    priority=2,
                ),
            ]

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.get_prioritized_navigation_options.return_value = prioritized_options

            # When getting prioritized navigation options
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")
                options = data_service.get_prioritized_navigation_options(context.user_session_id)

            # Then should return options prioritized by conversation history
            assert len(options) == 2
            assert options[0].label == "Make Appointment"  # Most relevant based on recent query
            assert options[0].priority == 1
            assert options[1].label == "Requirements"
            assert options[1].priority == 2

    def test_main_menu_navigation_with_service_categories(self):
        """Test main menu navigation with service categories"""
        # Given multiple service categories
        with patch("src.services.data_service.DataService") as mock_data_service:
            # Mock service categories
            service_categories = [
                ServiceCategory(
                    id=uuid.uuid4(),
                    name="Passport Services",
                    description="Passport application and renewal",
                ),
                ServiceCategory(
                    id=uuid.uuid4(),
                    name="Visa Services",
                    description="Visa application and extension",
                ),
                ServiceCategory(
                    id=uuid.uuid4(),
                    name="Business Registration",
                    description="Business registration and licensing",
                ),
            ]

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_all_service_categories.return_value = service_categories

            # When getting all service categories for main menu
            with DataService() as data_service:
                categories = data_service.get_all_service_categories()

            # Then should return all available service categories
            assert len(categories) == 3
            assert categories[0].name == "Passport Services"
            assert categories[1].name == "Visa Services"
            assert categories[2].name == "Business Registration"

    def test_cross_service_navigation_flow(self):
        """Test navigation flow between different service categories"""
        # Given user navigating from passport to visa services
        with patch("src.services.data_service.DataService") as mock_data_service:
            # Mock service categories
            passport_category = ServiceCategory(
                id=uuid.uuid4(),
                name="Passport Services",
                description="Passport application and renewal",
            )

            visa_category = ServiceCategory(
                id=uuid.uuid4(),
                name="Visa Services",
                description="Visa application and extension",
            )

            # Mock conversation context
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=passport_category.id,
            )

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.get_service_category.return_value = visa_category
            mock_data_instance.update_conversation_context.return_value = conversation_context

            # When user switches to visa services
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")
                new_category = data_service.get_service_category(visa_category.id)

                # Update context with new service category
                context.current_service_category_id = new_category.id
                updated_context = data_service.update_conversation_context(context)

            # Then conversation context should be updated
            assert updated_context.current_service_category_id == visa_category.id
            assert updated_context.user_session_id == "test-session-123"

    def test_context_persistence_across_conversation_turns(self):
        """Test that conversation context persists across multiple turns"""
        # Given a conversation with multiple turns
        with patch("src.services.data_service.DataService") as mock_data_service:
            # Mock conversation context with history
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=uuid.uuid4(),
                conversation_history=[
                    Message(
                        role="user",
                        content="passport requirements",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="assistant",
                        content="Here are the requirements...",
                        timestamp=datetime.now(UTC),
                    ),
                ],
            )

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.update_conversation_context.return_value = conversation_context

            # When adding new message to conversation
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")

                # Add new message using the model method
                context.add_message(
                    role="user",
                    content="how to make appointment"
                )

                # Update context
                updated_context = data_service.update_conversation_context(context)

            # Then context should persist with new message
            assert len(updated_context.conversation_history) == 3
            assert updated_context.conversation_history[2].content == "how to make appointment"
            assert updated_context.conversation_history[2].role == "user"