#!/usr/bin/env python3
"""
Debug conversation update issue
"""

import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from src.services.conversation_service import ConversationService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_conversation_update():
    """Test conversation creation and update"""

    print("\n=== Testing Conversation Update ===")

    try:
        conversation_service = ConversationService()

        # Create a test session
        session_id = "test_session_debug"
        print(f"Created test session: {session_id}")

        # Test 1: Create conversation
        conversation = conversation_service.create_conversation(
            user_session_id=session_id,
            user_preferences={"language": "en", "location": "Shenzhen"},
        )
        print(f"✓ Created conversation: {conversation.id}")

        # Check conversation history type
        print(f"Conversation history type: {type(conversation.conversation_history)}")
        if conversation.conversation_history:
            print(f"First message type: {type(conversation.conversation_history[0])}")

        # Test 2: Add user message
        conversation = conversation_service.add_message(
            session_id=session_id,
            role="user",
            content="I need help with Hong Kong passport application",
            metadata={"query_type": "passport_help"},
        )
        print("✓ Added user message to conversation")

        # Check updated conversation history type
        print(
            f"Updated conversation history type: {type(conversation.conversation_history)}"
        )
        if conversation.conversation_history:
            print(f"First message type: {type(conversation.conversation_history[0])}")

        print("\n🎉 Conversation update test passed!")
        return True

    except Exception as e:
        logger.error(f"Conversation update test failed: {e}")
        return False


if __name__ == "__main__":
    """Run conversation debug test"""

    print("Starting Conversation Debug Test")
    print("=" * 50)

    test_passed = test_conversation_update()

    print("\n" + "=" * 50)
    print(f"Conversation Debug Test: {'PASSED' if test_passed else 'FAILED'}")
