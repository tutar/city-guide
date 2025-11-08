#!/usr/bin/env python3
"""
Integration test for City Guide Smart Assistant system
Tests conversation flow and navigation system integration
"""

import logging
import uuid

from src.services.conversation_service import ConversationService
from src.services.data_service import DataService
from src.services.navigation_service import NavigationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_conversation_flow():
    """Test complete conversation flow with navigation integration"""

    print("\n=== Integration Test: Conversation Flow ===")

    try:
        # Initialize services
        conversation_service = ConversationService()
        navigation_service = NavigationService()

        # Create a test session
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        print(f"Created test session: {session_id}")

        # Test 1: Create conversation
        conversation = conversation_service.create_conversation(
            user_session_id=session_id,
            user_preferences={"language": "en", "location": "Shenzhen"},
        )
        print(f"✓ Created conversation: {conversation.id}")

        # Test 2: Add user message
        conversation = conversation_service.add_message(
            session_id=session_id,
            role="user",
            content="I need help with Hong Kong passport application",
            metadata={"query_type": "passport_help"},
        )
        print("✓ Added user message to conversation")

        # Test 3: Get service categories from database
        with DataService() as data_service:
            service_categories = data_service.get_active_service_categories()
            print(f"✓ Found {len(service_categories)} service categories")

            # Find Hong Kong/Macau Passport service
            passport_service = None
            for service in service_categories:
                if "Hong Kong/Macau Passport" in service.name:
                    passport_service = service
                    break

            if passport_service:
                print(f"✓ Found passport service: {passport_service.name}")

                # Test 4: Update service context
                conversation = conversation_service.update_service_context(
                    session_id=session_id, service_category_id=passport_service.id
                )
                print(f"✓ Updated service context to: {passport_service.name}")

                # Test 5: Get navigation options
                nav_options = navigation_service.get_navigation_options_by_category(
                    service_category_id=passport_service.id
                )
                print(f"✓ Retrieved {len(nav_options)} navigation options")

                # Display navigation options
                for i, option in enumerate(nav_options, 1):
                    print(f"  {i}. {option['label']} - {option['description']}")

                # Test 6: Add assistant response with navigation
                conversation = conversation_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content="I can help you with Hong Kong passport services. Here are the available options:",
                    metadata={"navigation_options": nav_options},
                )
                print("✓ Added assistant message with navigation options")

                # Test 7: Get conversation stats
                stats = conversation_service.get_conversation_stats(session_id)
                print(f"✓ Conversation stats: {stats['total_messages']} messages")

                # Test 8: Get recent messages
                recent_messages = conversation_service.get_recent_messages(
                    session_id, limit=5
                )
                print(f"✓ Retrieved {len(recent_messages)} recent messages")

                # Test 9: Export conversation history
                export_data = conversation_service.export_conversation_history(
                    session_id
                )
                print(
                    f"✓ Exported conversation history with {len(export_data['conversation_history'])} messages"
                )

                # Test 10: Test navigation service filtering
                filtered_options = navigation_service.filter_navigation_options(
                    options=nav_options, action_types=["requirements", "appointment"]
                )
                print(
                    f"✓ Filtered to {len(filtered_options)} options (requirements & appointment)"
                )

                # Test 11: Test navigation statistics
                nav_stats = navigation_service.get_navigation_statistics()
                print(
                    f"✓ Navigation statistics: {nav_stats['total_options']} total options"
                )

                print("\n🎉 All integration tests passed!")
                return True

            else:
                print("✗ Could not find Hong Kong/Macau Passport service")
                return False

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


def test_navigation_generation():
    """Test dynamic navigation generation"""

    print("\n=== Integration Test: Navigation Generation ===")

    try:
        from src.services.navigation_generator import NavigationGenerator

        navigation_generator = NavigationGenerator()

        # Test conversation context
        conversation_context = {
            "current_query": "passport application requirements",
            "user_preferences": {"language": "en"},
            "current_service_category_id": None,
        }

        # Generate navigation options
        nav_options = navigation_generator.generate_dynamic_navigation_options(
            conversation_context=conversation_context,
            search_results=[
                {
                    "document_type": "requirements",
                    "similarity_score": 0.85,
                    "title": "Passport Requirements",
                }
            ],
        )

        print(f"✓ Generated {len(nav_options)} dynamic navigation options")

        for i, option in enumerate(nav_options, 1):
            print(
                f"  {i}. {option['label']} - {option['source']} (priority: {option['priority']})"
            )

        # Test filtering
        filtered_options = navigation_generator.filter_navigation_options(
            options=nav_options, action_types=["requirements"], min_confidence=0.5
        )

        print(f"✓ Filtered to {len(filtered_options)} high-confidence options")

        print("\n🎉 Navigation generation tests passed!")
        return True

    except Exception as e:
        logger.error(f"Navigation generation test failed: {e}")
        return False


if __name__ == "__main__":
    """Run integration tests"""

    print("Starting City Guide Smart Assistant Integration Tests")
    print("=" * 60)

    # Run tests
    test1_passed = test_conversation_flow()
    test2_passed = test_navigation_generation()

    print("\n" + "=" * 60)
    print("Integration Test Results:")
    print(f"  Conversation Flow: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"  Navigation Generation: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All integration tests completed successfully!")
        exit(0)
    else:
        print("\n❌ Some integration tests failed")
        exit(1)
