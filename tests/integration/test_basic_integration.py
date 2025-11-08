#!/usr/bin/env python3
"""
Basic integration test for City Guide Smart Assistant system
Tests conversation flow and navigation system without AI dependencies
"""

import logging
import uuid

from src.services.conversation_service import ConversationService
from src.services.data_service import DataService
from src.services.navigation_service import NavigationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_conversation_basic():
    """Test basic conversation flow without AI dependencies"""

    print("\n=== Basic Integration Test: Conversation Flow ===")

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

                print("\n🎉 All basic integration tests passed!")
                return True

            else:
                print("✗ Could not find Hong Kong/Macau Passport service")
                return False

    except Exception as e:
        logger.error(f"Basic integration test failed: {e}")
        return False


def test_navigation_basic():
    """Test basic navigation functionality"""

    print("\n=== Basic Integration Test: Navigation Service ===")

    try:
        navigation_service = NavigationService()

        # Test 1: Get all active navigation options
        with DataService() as data_service:
            service_categories = data_service.get_active_service_categories()

            if service_categories:
                service_id = service_categories[0].id

                # Test navigation options by category
                nav_options = navigation_service.get_navigation_options_by_category(
                    service_id
                )
                print(f"✓ Retrieved {len(nav_options)} navigation options for service")

                # Test filtering
                filtered_options = navigation_service.filter_navigation_options(
                    options=nav_options, action_types=["requirements", "appointment"]
                )
                print(f"✓ Filtered to {len(filtered_options)} specific action types")

                # Test action type options
                action_options = navigation_service.get_action_type_options(
                    "requirements"
                )
                print(
                    f"✓ Found {len(action_options)} options for 'requirements' action type"
                )

                # Test navigation statistics
                stats = navigation_service.get_navigation_statistics()
                print(f"✓ Navigation stats: {stats['total_options']} total options")

                print("\n🎉 Basic navigation tests passed!")
                return True
            else:
                print("✗ No service categories found")
                return False

    except Exception as e:
        logger.error(f"Basic navigation test failed: {e}")
        return False


if __name__ == "__main__":
    """Run basic integration tests"""

    print("Starting City Guide Smart Assistant Basic Integration Tests")
    print("=" * 60)

    # Run tests
    test1_passed = test_conversation_basic()
    test2_passed = test_navigation_basic()

    print("\n" + "=" * 60)
    print("Basic Integration Test Results:")
    print(f"  Conversation Flow: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"  Navigation Service: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All basic integration tests completed successfully!")
        print("\nSystem Status Summary:")
        print("  ✓ Database services running")
        print("  ✓ Conversation service functional")
        print("  ✓ Navigation service functional")
        print("  ✓ Service data loaded")
        print("  ✓ Complete system integration verified")
        exit(0)
    else:
        print("\n❌ Some basic integration tests failed")
        exit(1)
