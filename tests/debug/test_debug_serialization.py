#!/usr/bin/env python3
"""
Debug serialization issue
"""

import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from src.models.conversation_model import ConversationContext


def test_serialization():
    """Test what's causing the serialization issue"""

    print("\n=== Testing Serialization ===")

    # Create a simple conversation context
    conversation = ConversationContext(
        user_session_id="test_session",
        user_preferences={"language": "en", "location": "Shenzhen"},
        navigation_options=[
            {
                "label": "Test Option",
                "action_type": "explain",
                "target_url": None,
                "description": "Test description",
                "priority": 5,
            }
        ],
    )

    # Add a message
    conversation.add_message("user", "Test message", {"query_type": "test"})

    print("✓ Created conversation context")

    # Try to serialize conversation history
    try:
        json.dumps(conversation.conversation_history)
        print("✓ Conversation history serialized successfully")
    except Exception as e:
        print(f"✗ Failed to serialize conversation history: {e}")

    # Try to serialize navigation options
    try:
        json.dumps(conversation.navigation_options)
        print("✓ Navigation options serialized successfully")
    except Exception as e:
        print(f"✗ Failed to serialize navigation options: {e}")

    # Try to serialize user preferences
    try:
        json.dumps(conversation.user_preferences)
        print("✓ User preferences serialized successfully")
    except Exception as e:
        print(f"✗ Failed to serialize user preferences: {e}")

    # Try to serialize the whole conversation
    try:
        json.dumps(conversation.model_dump())
        print("✓ Whole conversation serialized successfully")
    except Exception as e:
        print(f"✗ Failed to serialize whole conversation: {e}")


if __name__ == "__main__":
    """Run serialization test"""

    print("Starting Serialization Debug Test")
    print("=" * 40)

    test_serialization()

    print("\n" + "=" * 40)
    print("Serialization Debug Test Complete")
