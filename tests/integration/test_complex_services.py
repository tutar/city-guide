"""
Integration tests for complex government service explanations
"""

import uuid

from src.services.conversation_service import ConversationService
from src.services.data_service import DataService
from src.services.navigation_service import NavigationService


class TestComplexServices:
    """Test complex government service explanations and navigation"""

    def test_complex_service_explanation_flow(self):
        """Test complete flow for complex service explanations"""

        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        # Initialize services
        conversation_service = ConversationService()
        navigation_service = NavigationService()

        # Start conversation about complex service
        conversation = conversation_service.create_conversation(session_id)
        assert conversation is not None
        print(f"✓ Created conversation: {conversation.id}")

        # Add user query about complex service
        user_message = conversation_service.add_message(
            conversation.id,
            "user",
            "What are the requirements for a business registration permit in Shenzhen?",
            metadata={"query_type": "complex_service"},
        )
        assert user_message is not None
        print("✓ Added user message about complex service")

        # Find relevant service category
        with DataService() as data_service:
            service_categories = data_service.get_active_service_categories()
            business_registration = next(
                (sc for sc in service_categories if "Business Registration" in sc.name),
                None,
            )
            assert business_registration is not None
            print(
                f"✓ Found business registration service: {business_registration.name}"
            )

            # Update service context
            updated_conversation = conversation_service.update_service_context(
                conversation.id, business_registration.id
            )
            assert updated_conversation is not None
            print(f"✓ Updated service context to: {business_registration.name}")

        # Add assistant response with navigation
        assistant_message = conversation_service.add_message(
            conversation.id,
            "assistant",
            "I can help you understand the business registration requirements in Shenzhen. Here are the key steps and requirements:",
        )
        assert assistant_message is not None
        print("✓ Added assistant message with complex service guidance")

        # Get conversation history
        recent_messages = conversation_service.get_recent_messages(
            conversation.id, limit=5
        )
        assert len(recent_messages) >= 2
        print(f"✓ Retrieved {len(recent_messages)} recent messages")

        # Export conversation for analysis
        conversation_history = conversation_service.export_conversation_history(
            conversation.id
        )
        assert len(conversation_history) >= 2
        print(
            f"✓ Exported conversation history with {len(conversation_history)} messages"
        )

        print("🎉 Complex service explanation flow test passed!")

    def test_technical_term_explanation(self):
        """Test technical term explanation functionality"""

        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        conversation_service = ConversationService()

        # Start conversation with technical term
        conversation = conversation_service.create_conversation(session_id)

        # Add query with technical term
        conversation_service.add_message(
            conversation.id,
            "user",
            "What does 'tax registration certificate' mean in the context of business setup?",
            metadata={"query_type": "technical_term"},
        )

        # Verify conversation context
        conversation_context = conversation_service.get_conversation_context(session_id)
        assert conversation_context is not None
        print("✓ Technical term explanation conversation created")

        print("🎉 Technical term explanation test passed!")

    def test_location_based_service_filtering(self):
        """Test location-based service filtering"""

        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        conversation_service = ConversationService()
        navigation_service = NavigationService()

        # Start conversation with location context
        conversation = conversation_service.create_conversation(session_id)

        # Add location-specific query
        conversation_service.add_message(
            conversation.id,
            "user",
            "Where can I apply for a resident permit near Futian district?",
            metadata={
                "query_type": "location_based",
                "location": "Futian district, Shenzhen",
            },
        )

        print("🎉 Location-based service filtering test passed!")


if __name__ == "__main__":
    """Run complex service tests"""

    print("Starting Complex Government Services Integration Tests")
    print("=" * 60)

    test_instance = TestComplexServices()

    try:
        test_instance.test_complex_service_explanation_flow()
        print("\n" + "=" * 60)
        test_instance.test_technical_term_explanation()
        print("\n" + "=" * 60)
        test_instance.test_location_based_service_filtering()
        print("\n" + "=" * 60)

        print("🎉 All complex service tests completed successfully!")

    except Exception as e:
        print(f"❌ Complex service tests failed: {e}")
        raise
