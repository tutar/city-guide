"""
Integration tests for service relationship mapping and cross-service navigation
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from src.models.conversation_model import ConversationContext, Message
from src.models.services import ServiceCategory, NavigationOption
from src.services.data_service import DataService
from src.services.search_service import SearchService


class TestServiceRelationships:
    """Test suite for service relationship mapping and cross-service navigation"""

    def test_service_relationship_mapping_integration(self):
        """Test integration of service relationship mapping with conversation context"""
        # Given a conversation about passport services
        with patch("src.services.data_service.DataService") as mock_data_service:
            with patch("src.services.search_service.SearchService") as mock_search_service:
                # Mock service categories with relationships
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

                id_card_category = ServiceCategory(
                    id=uuid.uuid4(),
                    name="Hong Kong ID Card Services",
                    description="ID card application and renewal",
                )

                # Mock conversation context
                conversation_context = ConversationContext(
                    user_session_id="test-session-123",
                    current_service_category_id=passport_category.id,
                    conversation_history=[
                        Message(
                            role="user",
                            content="How do I apply for a passport?",
                            timestamp=datetime.now(UTC),
                        ),
                        Message(
                            role="assistant",
                            content="Here are the passport requirements...",
                            timestamp=datetime.now(UTC),
                        ),
                    ],
                )

                # Setup mock data service
                mock_data_instance = mock_data_service.return_value.__enter__.return_value
                mock_data_instance.get_conversation_context.return_value = conversation_context
                mock_data_instance.get_service_category.return_value = passport_category
                mock_data_instance.get_all_service_categories.return_value = [
                    passport_category, visa_category, id_card_category
                ]

                # Setup mock search service for related services
                mock_search_instance = mock_search_service.return_value
                mock_search_instance.get_related_services.return_value = [
                    {
                        "name": "Hong Kong Visa Services",
                        "description": "Visa application and extension services",
                        "relevance_score": 0.8,
                        "reason": "Often needed together for international travel"
                    },
                    {
                        "name": "Hong Kong ID Card Services",
                        "description": "ID card application and renewal",
                        "relevance_score": 0.6,
                        "reason": "Common identification document"
                    }
                ]

                # When getting related services
                with DataService() as data_service:
                    current_context = data_service.get_conversation_context("test-session-123")
                    current_category = data_service.get_service_category(current_context.current_service_category_id)
                    all_categories = data_service.get_all_service_categories()

                related_services = mock_search_instance.get_related_services(
                    current_category.name, "test-session-123"
                )

                # Then should return related services with proper relationships
                assert len(related_services) == 2
                assert related_services[0]["name"] == "Hong Kong Visa Services"
                assert related_services[0]["relevance_score"] == 0.8
                assert related_services[1]["name"] == "Hong Kong ID Card Services"
                assert related_services[1]["relevance_score"] == 0.6

                # Verify conversation context is maintained
                assert current_context.current_service_category_id == passport_category.id
                assert len(all_categories) == 3

    def test_cross_service_navigation_flow_integration(self):
        """Test cross-service navigation flow between related services"""
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

            # Mock conversation context with navigation history
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=passport_category.id,
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
                navigation_options=[
                    {
                        "label": "Related: Visa Services",
                        "action_type": "navigate_service",
                        "target_service_id": str(visa_category.id),
                        "priority": 2
                    }
                ]
            )

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.get_service_category.return_value = visa_category
            mock_data_instance.update_conversation_context.return_value = conversation_context

            # When user navigates to related service
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")

                # Simulate user selecting related service
                related_service_id = context.navigation_options[0]["target_service_id"]
                new_category = data_service.get_service_category(uuid.UUID(related_service_id))

                # Update context with new service category
                context.current_service_category_id = new_category.id
                updated_context = data_service.update_conversation_context(context)

            # Then conversation context should be updated with new service
            assert updated_context.current_service_category_id == visa_category.id
            assert updated_context.user_session_id == "test-session-123"

            # Verify navigation history is maintained
            assert len(updated_context.conversation_history) == 2
            assert updated_context.navigation_options[0]["label"] == "Related: Visa Services"

    def test_service_relationship_context_persistence(self):
        """Test that service relationships persist across conversation turns"""
        # Given a conversation with multiple service interactions
        with patch("src.services.data_service.DataService") as mock_data_service:
            # Mock conversation context with service relationship tracking
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=uuid.uuid4(),
                conversation_history=[
                    Message(
                        role="user",
                        content="passport application",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="assistant",
                        content="Passport application process...",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="user",
                        content="what about visa requirements",
                        timestamp=datetime.now(UTC),
                    ),
                ],
                navigation_options=[
                    {
                        "label": "Passport Requirements",
                        "action_type": "requirements",
                        "priority": 1
                    },
                    {
                        "label": "Related: Visa Services",
                        "action_type": "navigate_service",
                        "priority": 2
                    }
                ]
            )

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.update_conversation_context.return_value = conversation_context

            # When adding new message about related service
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")

                # Add new message about visa services
                context.add_message(
                    role="user",
                    content="visa application process"
                )

                # Update context
                updated_context = data_service.update_conversation_context(context)

            # Then context should persist with new message and maintain relationships
            assert len(updated_context.conversation_history) == 4
            assert updated_context.conversation_history[3].content == "visa application process"
            assert updated_context.conversation_history[3].role == "user"

            # Verify navigation options still include related services
            assert len(updated_context.navigation_options) == 2
            assert any("Related: Visa Services" in opt["label"] for opt in updated_context.navigation_options)

    def test_service_relationship_analytics_integration(self):
        """Test integration of service relationship analytics"""
        # Given multiple service interactions
        with patch("src.services.data_service.DataService") as mock_data_service:
            with patch("src.services.search_service.SearchService") as mock_search_service:
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

                # Mock conversation context with service transitions
                conversation_context = ConversationContext(
                    user_session_id="test-session-123",
                    current_service_category_id=passport_category.id,
                    conversation_history=[
                        Message(
                            role="user",
                            content="passport",
                            timestamp=datetime.now(UTC),
                        ),
                        Message(
                            role="assistant",
                            content="Passport information...",
                            timestamp=datetime.now(UTC),
                        ),
                        Message(
                            role="user",
                            content="visa requirements",
                            timestamp=datetime.now(UTC),
                        ),
                    ],
                )

                # Setup mock data service
                mock_data_instance = mock_data_service.return_value.__enter__.return_value
                mock_data_instance.get_conversation_context.return_value = conversation_context
                mock_data_instance.get_service_category.side_effect = [passport_category, visa_category]

                # Setup mock search service for relationship analytics
                mock_search_instance = mock_search_service.return_value
                mock_search_instance.get_related_services.return_value = [
                    {
                        "name": "Visa Services",
                        "description": "Visa application and extension services",
                        "relevance_score": 0.8,
                        "reason": "Common service transition"
                    }
                ]

                # When analyzing service relationships
                with DataService() as data_service:
                    context = data_service.get_conversation_context("test-session-123")

                    # Extract service transitions from conversation history
                    service_transitions = []
                    for i in range(len(context.conversation_history) - 1):
                        current_msg = context.conversation_history[i]
                        next_msg = context.conversation_history[i + 1]

                        # Simple keyword-based service detection
                        if "passport" in current_msg.content.lower() and "visa" in next_msg.content.lower():
                            service_transitions.append({
                                "from": "passport",
                                "to": "visa",
                                "context": "user query transition"
                            })

                # Get related services for analytics
                related_services = mock_search_instance.get_related_services(
                    "passport", "test-session-123"
                )

                # Then should detect service transitions and relationships
                assert len(service_transitions) == 1
                assert service_transitions[0]["from"] == "passport"
                assert service_transitions[0]["to"] == "visa"

                assert len(related_services) == 1
                assert related_services[0]["name"] == "Visa Services"
                assert related_services[0]["relevance_score"] == 0.8

    def test_multi_service_navigation_flow(self):
        """Test navigation flow involving multiple related services"""
        # Given user navigating through multiple related services
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

            id_card_category = ServiceCategory(
                id=uuid.uuid4(),
                name="ID Card Services",
                description="ID card application and renewal",
            )

            # Mock conversation context with multi-service navigation
            conversation_context = ConversationContext(
                user_session_id="test-session-123",
                current_service_category_id=passport_category.id,
                conversation_history=[
                    Message(
                        role="user",
                        content="passport",
                        timestamp=datetime.now(UTC),
                    ),
                    Message(
                        role="assistant",
                        content="Passport services...",
                        timestamp=datetime.now(UTC),
                    ),
                ],
                navigation_options=[
                    {
                        "label": "Passport Requirements",
                        "action_type": "requirements",
                        "priority": 1
                    },
                    {
                        "label": "Related: Visa Services",
                        "action_type": "navigate_service",
                        "target_service_id": str(visa_category.id),
                        "priority": 2
                    },
                    {
                        "label": "Related: ID Card Services",
                        "action_type": "navigate_service",
                        "target_service_id": str(id_card_category.id),
                        "priority": 3
                    }
                ]
            )

            # Setup mock data service
            mock_data_instance = mock_data_service.return_value.__enter__.return_value
            mock_data_instance.get_conversation_context.return_value = conversation_context
            mock_data_instance.get_service_category.side_effect = [
                passport_category, visa_category, id_card_category
            ]
            mock_data_instance.update_conversation_context.return_value = conversation_context

            # When user navigates through multiple services
            with DataService() as data_service:
                context = data_service.get_conversation_context("test-session-123")

                # Navigate to visa services
                visa_service_id = context.navigation_options[1]["target_service_id"]
                visa_category = data_service.get_service_category(uuid.UUID(visa_service_id))
                context.current_service_category_id = visa_category.id

                # Navigate to ID card services
                id_card_service_id = context.navigation_options[2]["target_service_id"]
                id_card_category = data_service.get_service_category(uuid.UUID(id_card_service_id))
                context.current_service_category_id = id_card_category.id

                updated_context = data_service.update_conversation_context(context)

            # Then context should reflect final service selection
            assert updated_context.current_service_category_id == id_card_category.id
            assert len(updated_context.navigation_options) == 3

            # Verify all related services are tracked
            service_ids = [
                opt["target_service_id"] for opt in updated_context.navigation_options
                if "target_service_id" in opt
            ]
            assert len(service_ids) == 2
            assert str(visa_category.id) in service_ids
            assert str(id_card_category.id) in service_ids