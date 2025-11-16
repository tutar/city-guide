"""
Document source models for attribution tracking.

This module defines models for managing document sources with attribution metadata,
integrating with the existing document embedding system.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from src.models.document_embeddings import DocumentEmbedding


class DocumentSource(BaseModel):
    """
    Extended document source with attribution metadata.

    This model extends the existing DocumentEmbedding with additional
    attribution-specific metadata and access information.
    """

    id: UUID = Field(default_factory=uuid4, description="UUID (primary key)")
    document_embedding_id: UUID = Field(
        ..., description="Reference to document embedding"
    )
    title: str = Field(..., min_length=1, description="Document title for display")
    location: str = Field(..., description="Document storage location/URL")
    attribution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for attribution tracking"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When document was added"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last metadata update"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title must be non-empty")
        return v.strip()

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError("Location must be non-empty")
        return v.strip()

    def add_attribution_metadata(self, key: str, value: Any) -> None:
        """Add attribution metadata."""
        self.attribution_metadata[key] = value
        self.updated_at = datetime.now()


class DocumentSourceCreate(BaseModel):
    """Model for creating new document sources."""

    document_embedding_id: UUID = Field(
        ..., description="Reference to document embedding"
    )
    title: str = Field(..., min_length=1, description="Document title for display")
    location: str = Field(..., description="Document storage location/URL")
    attribution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for attribution tracking"
    )


class DocumentSourceUpdate(BaseModel):
    """Model for updating existing document sources."""

    title: Optional[str] = Field(
        None, min_length=1, description="Document title for display"
    )
    location: Optional[str] = Field(None, description="Document storage location/URL")
    attribution_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for attribution tracking"
    )
