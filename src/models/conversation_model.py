"""
Conversation-related data models for City Guide Smart Assistant
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Message(BaseModel):
    """Represents a single message in a conversation"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] | None = Field(default_factory=dict)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        valid_roles = ["user", "assistant"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {valid_roles}")
        return v

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_encoders={
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class ConversationContext(BaseModel):
    """Represents the current state of user interaction"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_session_id: str = Field(..., description="Anonymous session identifier")
    current_service_category_id: uuid.UUID | None = Field(
        None, description="Reference to current service"
    )
    conversation_history: list[Message] = Field(default_factory=list)
    navigation_options: list[dict[str, Any]] = Field(default_factory=list)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(default=True, description="Whether session is still active")

    # Service relationship tracking
    service_relationships: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Track relationships between services accessed in this conversation",
    )
    related_services_suggested: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Track related services that have been suggested to the user",
    )
    service_transitions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Track transitions between different service categories",
    )

    @field_validator("user_session_id")
    @classmethod
    def session_id_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()

    @field_validator("conversation_history")
    @classmethod
    def conversation_history_validation(cls, v):
        # Ensure conversation history doesn't grow too large
        if len(v) > 100:
            raise ValueError("Conversation history too large, consider archiving")
        return v

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a new message to the conversation history"""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.conversation_history.append(message)
        self.last_activity = datetime.now(UTC)

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Get recent messages from conversation history"""
        return self.conversation_history[-limit:]

    def get_recent_messages_dict(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent messages as dictionaries for AI service (more efficient)"""
        recent_messages = self.conversation_history[-limit:]
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in recent_messages
        ]

    def should_archive(self) -> bool:
        """Check if conversation should be archived due to inactivity"""
        if not self.is_active:
            return True

        # Ensure both datetimes are timezone-aware for comparison
        current_time = datetime.now(UTC)
        last_activity = (
            self.last_activity.replace(tzinfo=UTC)
            if self.last_activity.tzinfo is None
            else self.last_activity
        )

        time_since_activity = current_time - last_activity
        return time_since_activity.total_seconds() > 1800  # 30 minutes

    def mark_completed(self) -> None:
        """Mark conversation as completed"""
        self.is_active = False

    def add_service_relationship(
        self,
        source_service_id: uuid.UUID,
        target_service_id: uuid.UUID,
        relationship_type: str,
        relevance_score: float = 0.5,
    ) -> None:
        """Add a service relationship to tracking"""
        relationship = {
            "source_service_id": str(source_service_id),
            "target_service_id": str(target_service_id),
            "relationship_type": relationship_type,
            "relevance_score": relevance_score,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.service_relationships.append(relationship)

    def add_related_service_suggestion(
        self,
        service_id: uuid.UUID,
        service_name: str,
        reason: str,
        relevance_score: float = 0.5,
    ) -> None:
        """Track a related service suggestion"""
        suggestion = {
            "service_id": str(service_id),
            "service_name": service_name,
            "reason": reason,
            "relevance_score": relevance_score,
            "suggested_at": datetime.now(UTC).isoformat(),
        }
        self.related_services_suggested.append(suggestion)

    def add_service_transition(
        self,
        from_service_id: uuid.UUID,
        to_service_id: uuid.UUID,
        transition_type: str = "user_navigation",
    ) -> None:
        """Track a service transition"""
        transition = {
            "from_service_id": str(from_service_id),
            "to_service_id": str(to_service_id),
            "transition_type": transition_type,
            "transition_time": datetime.now(UTC).isoformat(),
        }
        self.service_transitions.append(transition)

    def get_related_services_history(self) -> list[dict[str, Any]]:
        """Get history of related services suggested"""
        return self.related_services_suggested

    def get_service_transitions(self) -> list[dict[str, Any]]:
        """Get all service transitions in this conversation"""
        return self.service_transitions

    def get_service_relationships(self) -> list[dict[str, Any]]:
        """Get all service relationships tracked in this conversation"""
        return self.service_relationships

    def get_most_relevant_related_services(
        self, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get most relevant related services based on conversation context"""
        # Sort by relevance score and timestamp
        sorted_suggestions = sorted(
            self.related_services_suggested,
            key=lambda x: (x.get("relevance_score", 0), x.get("suggested_at", "")),
            reverse=True,
        )
        return sorted_suggestions[:limit]

    model_config = ConfigDict(
        json_encoders={
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class ConversationState(BaseModel):
    """Represents conversation state transitions"""

    state: str = Field(
        default="created",
        description="Current state: created, active, inactive, completed",
    )
    transitions: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "created": ["active"],
            "active": ["inactive", "completed"],
            "inactive": ["active", "completed"],
            "completed": [],
        }
    )

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        valid_states = ["created", "active", "inactive", "completed"]
        if v not in valid_states:
            raise ValueError(f"State must be one of: {valid_states}")
        return v

    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is valid"""
        return target_state in self.transitions.get(self.state, [])

    def transition_to(self, target_state: str) -> None:
        """Transition to target state if valid"""
        if not self.can_transition_to(target_state):
            raise ValueError(f"Invalid transition from {self.state} to {target_state}")
        self.state = target_state
