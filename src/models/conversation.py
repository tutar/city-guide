"""
Conversation-related data models for City Guide Smart Assistant
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid


class Message(BaseModel):
    """Represents a single message in a conversation"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["user", "assistant"]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class ConversationContext(BaseModel):
    """Represents the current state of user interaction"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_session_id: str = Field(..., description="Anonymous session identifier")
    current_service_category_id: Optional[uuid.UUID] = Field(None, description="Reference to current service")
    conversation_history: List[Message] = Field(default_factory=list)
    navigation_options: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Whether session is still active")

    @validator('user_session_id')
    def session_id_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError('Session ID cannot be empty')
        return v.strip()

    @validator('conversation_history')
    def conversation_history_validation(cls, v):
        # Ensure conversation history doesn't grow too large
        if len(v) > 100:
            raise ValueError('Conversation history too large, consider archiving')
        return v

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new message to the conversation history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
        self.last_activity = datetime.utcnow()

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages from conversation history"""
        return self.conversation_history[-limit:]

    def should_archive(self) -> bool:
        """Check if conversation should be archived due to inactivity"""
        if not self.is_active:
            return True

        time_since_activity = datetime.utcnow() - self.last_activity
        return time_since_activity.total_seconds() > 1800  # 30 minutes

    def mark_completed(self) -> None:
        """Mark conversation as completed"""
        self.is_active = False

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class ConversationState(BaseModel):
    """Represents conversation state transitions"""

    state: str = Field(default="created", description="Current state: created, active, inactive, completed")
    transitions: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "created": ["active"],
            "active": ["inactive", "completed"],
            "inactive": ["active", "completed"],
            "completed": []
        }
    )

    @validator('state')
    def validate_state(cls, v):
        valid_states = ["created", "active", "inactive", "completed"]
        if v not in valid_states:
            raise ValueError(f'State must be one of: {valid_states}')
        return v

    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is valid"""
        return target_state in self.transitions.get(self.state, [])

    def transition_to(self, target_state: str) -> None:
        """Transition to target state if valid"""
        if not self.can_transition_to(target_state):
            raise ValueError(f'Invalid transition from {self.state} to {target_state}')
        self.state = target_state