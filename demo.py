#!/usr/bin/env python3
"""
Demo script for City Guide Smart Assistant
"""

import uuid

import requests

BASE_URL = "http://localhost:8000"


def demo_conversation():
    """Demonstrate the conversation flow"""

    print("🚀 City Guide Smart Assistant Demo")
    print("=" * 50)

    # Start a conversation
    session_id = f"demo_session_{uuid.uuid4().hex[:8]}"
    print(f"📝 Starting conversation with session: {session_id}")

    response = requests.post(
        f"{BASE_URL}/api/conversation/start",
        json={"user_session_id": session_id, "user_preferences": {"language": "zh-CN"}},
    )

    if response.status_code != 200:
        print(f"❌ Failed to start conversation: {response.text}")
        return

    data = response.json()
    print(f"✅ Conversation started: {data['conversation_id']}")
    print(f"🤖 Welcome message: {data['welcome_message']}")

    # Send a message about passport services
    print("\n💬 Sending message: 'I need help with Hong Kong passport application'")

    response = requests.post(
        f"{BASE_URL}/api/conversation/message",
        json={
            "session_id": session_id,
            "message": "I need help with Hong Kong passport application",
        },
    )

    if response.status_code != 200:
        print(f"❌ Failed to send message: {response.text}")
        return

    data = response.json()
    print(f"✅ Assistant response: {data['response']}")

    if data["navigation_options"]:
        print(f"🔗 Navigation options: {len(data['navigation_options'])} available")
        for i, option in enumerate(data["navigation_options"], 1):
            print(
                f"   {i}. {option.get('label', 'Unknown')} - {option.get('description', '')}"
            )

    # Get conversation history
    print("\n📜 Getting conversation history...")
    response = requests.get(f"{BASE_URL}/api/conversation/{session_id}/history")

    if response.status_code == 200:
        history_data = response.json()
        print(f"✅ Conversation history: {len(history_data['history'])} messages")
        for msg in history_data["history"]:
            print(f"   {msg['role'].upper()}: {msg['content']}")

    # Test service categories
    print("\n🏛️  Testing service categories...")

    # Get health check with readiness
    response = requests.get(f"{BASE_URL}/health/readiness")
    if response.status_code == 200:
        health_data = response.json()
        print(f"✅ System health: {health_data['status']}")
        for service, status in health_data["checks"].items():
            print(f"   {service}: {status['status']} - {status['details']}")

    print("\n🎉 Demo completed successfully!")
    print(f"📊 You can view API documentation at: {BASE_URL}/docs")


if __name__ == "__main__":
    demo_conversation()
