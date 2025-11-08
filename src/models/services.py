"""
Service-related data models for City Guide Smart Assistant
"""

import uuid
from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field, validator
from pydantic.networks import HttpUrl


class ServiceCategory(BaseModel):
    """Represents a government service area with associated procedures and requirements"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(
        ..., min_length=1, max_length=255, description="Service category name"
    )
    description: Optional[str] = Field(
        None, description="Brief description of the service"
    )
    official_source_url: Optional[HttpUrl] = Field(
        None, description="URL to official government information"
    )
    last_verified: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(
        default=True, description="Whether this service is currently available"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validator("name")
    @classmethod
    def name_must_be_unique(cls, v):
        # This would be validated at database level
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @validator("last_verified")
    @classmethod
    def last_verified_within_30_days(cls, v):
        # Ensure both datetimes are timezone-aware for comparison
        current_time = datetime.now(UTC)
        verified_time = v.replace(tzinfo=UTC) if v.tzinfo is None else v

        if (current_time - verified_time).days > 30:
            raise ValueError("Service information must be verified within last 30 days")
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class NavigationOption(BaseModel):
    """Represents contextual action items that adapt based on user needs and conversation flow"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    service_category_id: uuid.UUID = Field(..., description="Parent service category")
    label: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display text for navigation option",
    )
    action_type: str = Field(
        ...,
        description="Type of action: explain, requirements, appointment, location, related",
    )
    target_url: Optional[HttpUrl] = Field(None, description="URL for external actions")
    description: Optional[str] = Field(
        None, description="Detailed description of what this option provides"
    )
    priority: int = Field(default=5, ge=1, le=10, description="Display order priority")
    is_active: bool = Field(
        default=True, description="Whether this option is currently available"
    )

    @validator("action_type")
    @classmethod
    def validate_action_type(cls, v):
        valid_types = ["explain", "requirements", "appointment", "location", "related"]
        if v not in valid_types:
            raise ValueError(f"Action type must be one of: {valid_types}")
        return v

    @validator("label")
    @classmethod
    def label_must_be_clear(cls, v):
        if not v.strip():
            raise ValueError("Label must be clear and actionable")
        return v.strip()

    @validator("target_url")
    @classmethod
    def validate_target_url(cls, v, values):
        if values.get("action_type") in ["appointment", "location"]:
            # For appointment and location actions, URL should be provided
            if not v:
                raise ValueError(
                    "Target URL is required for appointment and location actions"
                )
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
        }


class OfficialInformationSource(BaseModel):
    """Represents authoritative data sources with validation mechanisms and update tracking"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(..., min_length=1, max_length=255, description="Source name")
    base_url: HttpUrl = Field(..., description="Base URL for the source")
    api_endpoint: Optional[str] = Field(None, description="API endpoint if available")
    update_frequency: str = Field(
        default="weekly",
        description="Update frequency: daily, weekly, monthly, on_change",
    )
    last_checked: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field(default="active", description="Status: active, inactive, error")
    error_count: int = Field(default=0, description="Number of consecutive errors")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validator("update_frequency")
    @classmethod
    def validate_update_frequency(cls, v):
        valid_frequencies = ["daily", "weekly", "monthly", "on_change"]
        if v not in valid_frequencies:
            raise ValueError(f"Update frequency must be one of: {valid_frequencies}")
        return v

    @validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["active", "inactive", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }
