"""
Conversation service for City Guide Smart Assistant
"""

import logging
import uuid
from datetime import UTC, datetime

from src.models.conversation_model import ConversationContext
from src.services.data_service import DataService

# Configure logging
logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation history and context"""

    def __init__(self):
        self.data_service = DataService()

    def create_conversation(
        self, user_session_id: str, user_preferences: dict | None = None
    ) -> ConversationContext:
        """Create a new conversation context"""
        try:
            conversation = ConversationContext(
                user_session_id=user_session_id,
                user_preferences=user_preferences or {},
            )

            # Save to database
            with self.data_service as data_service:
                saved_conversation = data_service.create_conversation_context(
                    conversation
                )

            logger.info(f"Created new conversation: {saved_conversation.id}")
            return saved_conversation

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    def get_conversation(self, session_id: str) -> ConversationContext | None:
        """Get conversation context by session ID"""
        try:
            with self.data_service as data_service:
                conversation = data_service.get_conversation_context(session_id)

            if conversation:
                logger.debug(f"Retrieved conversation: {conversation.id}")
            else:
                logger.debug(f"No conversation found for session: {session_id}")

            return conversation

        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            raise

    def add_message(
        self, session_id: str, role: str, content: str, metadata: dict | None = None
    ) -> ConversationContext:
        """Add a message to conversation history"""
        try:
            with self.data_service as data_service:
                # Get existing conversation
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    raise ValueError(
                        f"Conversation not found for session: {session_id}"
                    )

                # Add message
                conversation.add_message(role, content, metadata)

                # Update last activity
                conversation.last_activity = datetime.now(UTC)

                # Save updated conversation
                updated_conversation = data_service.update_conversation_context(
                    session_id, conversation
                )

            logger.info(
                f"Added message to conversation {updated_conversation.id}: {role}"
            )
            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to add message to conversation: {e}")
            raise

    def update_service_context(
        self, session_id: str, service_category_id: uuid.UUID
    ) -> ConversationContext:
        """Update the service context for a conversation"""
        try:
            with self.data_service as data_service:
                # Get existing conversation
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    raise ValueError(
                        f"Conversation not found for session: {session_id}"
                    )

                # Update service context
                conversation.current_service_category_id = service_category_id

                # Get navigation options for the service
                nav_options = data_service.get_navigation_options_by_category(
                    service_category_id
                )
                conversation.navigation_options = [
                    {
                        "label": option.label,
                        "action_type": option.action_type,
                        "target_url": str(option.target_url)
                        if option.target_url
                        else None,
                        "description": option.description,
                        "priority": option.priority,
                    }
                    for option in nav_options
                ]

                # Update last activity
                conversation.last_activity = datetime.now(UTC)

                # Save updated conversation
                updated_conversation = data_service.update_conversation_context(
                    session_id, conversation
                )

            logger.info(
                f"Updated service context for conversation {updated_conversation.id}: {service_category_id}"
            )
            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to update service context: {e}")
            raise

    def update_navigation_options(
        self, session_id: str, navigation_options: list
    ) -> ConversationContext:
        """Update navigation options for a conversation"""
        try:
            with self.data_service as data_service:
                # Get existing conversation
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    raise ValueError(
                        f"Conversation not found for session: {session_id}"
                    )

                # Update navigation options
                conversation.navigation_options = navigation_options

                # Update last activity
                conversation.last_activity = datetime.now(UTC)

                # Save updated conversation
                updated_conversation = data_service.update_conversation_context(
                    session_id, conversation
                )

            logger.info(
                f"Updated navigation options for conversation {updated_conversation.id}"
            )
            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to update navigation options: {e}")
            raise

    def get_recent_messages(self, session_id: str, limit: int = 10) -> list:
        """Get recent messages from conversation history"""
        try:
            with self.data_service as data_service:
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    return []

                recent_messages = conversation.get_recent_messages(limit)
                return [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "metadata": msg.metadata,
                    }
                    for msg in recent_messages
                ]

        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []

    def mark_conversation_completed(self, session_id: str) -> ConversationContext:
        """Mark a conversation as completed"""
        try:
            with self.data_service as data_service:
                # Get existing conversation
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    raise ValueError(
                        f"Conversation not found for session: {session_id}"
                    )

                # Mark as completed
                conversation.mark_completed()

                # Save updated conversation
                updated_conversation = data_service.update_conversation_context(
                    session_id, conversation
                )

            logger.info(f"Marked conversation as completed: {updated_conversation.id}")
            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to mark conversation as completed: {e}")
            raise

    def cleanup_inactive_conversations(self, max_age_hours: int = 24) -> int:
        """Clean up inactive conversations older than specified hours"""
        try:
            cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
            cleaned_count = 0

            with self.data_service as data_service:
                # Get inactive conversations
                inactive_conversations = data_service.get_inactive_conversations(
                    cutoff_time
                )

                # Archive or delete them
                for conversation in inactive_conversations:
                    try:
                        # Archive conversation (in production, you might move to archive table)
                        conversation.is_active = False
                        data_service.update_conversation_context(
                            conversation.user_session_id, conversation
                        )
                        cleaned_count += 1

                        logger.info(
                            f"Archived inactive conversation: {conversation.id}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to archive conversation {conversation.id}: {e}"
                        )

            logger.info(f"Cleaned up {cleaned_count} inactive conversations")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup inactive conversations: {e}")
            return 0

    def get_conversation_stats(self, session_id: str) -> dict:
        """Get statistics for a conversation"""
        try:
            with self.data_service as data_service:
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    return {}

                stats = {
                    "session_id": conversation.user_session_id,
                    "conversation_id": str(conversation.id),
                    "total_messages": len(conversation.conversation_history),
                    "user_messages": len(
                        [
                            m
                            for m in conversation.conversation_history
                            if m.role == "user"
                        ]
                    ),
                    "assistant_messages": len(
                        [
                            m
                            for m in conversation.conversation_history
                            if m.role == "assistant"
                        ]
                    ),
                    "navigation_options_count": len(conversation.navigation_options),
                    "is_active": conversation.is_active,
                    "created_at": conversation.created_at,
                    "last_activity": conversation.last_activity,
                    "duration_minutes": (
                        conversation.last_activity - conversation.created_at
                    ).total_seconds()
                    / 60,
                }

                return stats

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {}

    def export_conversation_history(self, session_id: str) -> dict:
        """Export complete conversation history"""
        try:
            with self.data_service as data_service:
                conversation = data_service.get_conversation_context(session_id)
                if not conversation:
                    return {}

                export_data = {
                    "session_id": conversation.user_session_id,
                    "conversation_id": str(conversation.id),
                    "created_at": conversation.created_at.isoformat(),
                    "last_activity": conversation.last_activity.isoformat(),
                    "is_active": conversation.is_active,
                    "current_service_category_id": str(
                        conversation.current_service_category_id
                    )
                    if conversation.current_service_category_id
                    else None,
                    "user_preferences": conversation.user_preferences,
                    "navigation_options": conversation.navigation_options,
                    "conversation_history": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat(),
                            "metadata": msg.metadata,
                        }
                        for msg in conversation.conversation_history
                    ],
                }

                return export_data

        except Exception as e:
            logger.error(f"Failed to export conversation history: {e}")
            return {}
