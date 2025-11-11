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
    access_info: Dict[str, Any] = Field(
        default_factory=dict, description="Access permissions and metadata"
    )
    attribution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for attribution tracking"
    )
    access_state: str = Field(
        default="available",
        description="Document access state: available, unavailable, restricted",
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

    @field_validator("access_state")
    @classmethod
    def validate_access_state(cls, v):
        valid_states = {"available", "unavailable", "restricted"}
        if v not in valid_states:
            raise ValueError(f"Access state must be one of: {valid_states}")
        return v

    @field_validator("access_info")
    @classmethod
    def validate_access_info(cls, v):
        """Ensure access_info contains required permission fields."""
        required_fields = {"permission"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Access info must contain: {required_fields}")
        return v

    def is_accessible(self) -> bool:
        """Check if document is currently accessible."""
        return self.access_state == "available"

    def get_access_permission(self) -> str:
        """Get the document access permission level."""
        return self.access_info.get("permission", "unknown")

    def update_access_state(self, new_state: str) -> None:
        """Update document access state."""
        valid_states = {"available", "unavailable", "restricted"}
        if new_state not in valid_states:
            raise ValueError(f"Invalid access state: {new_state}")

        self.access_state = new_state
        self.updated_at = datetime.now()

    def add_attribution_metadata(self, key: str, value: Any) -> None:
        """Add attribution metadata."""
        self.attribution_metadata[key] = value
        self.updated_at = datetime.now()


class DocumentSourceWithEmbedding(BaseModel):
    """
    Combined document source with embedding information.

    This model combines DocumentSource with DocumentEmbedding for complete
    document information including both attribution metadata and embedding data.
    """

    document_source: DocumentSource
    document_embedding: Optional[DocumentEmbedding] = None

    @property
    def is_embedded(self) -> bool:
        """Check if document has embedding data."""
        return self.document_embedding is not None

    @property
    def combined_metadata(self) -> Dict[str, Any]:
        """Combine metadata from both source and embedding."""
        combined = {}
        if self.document_embedding:
            combined.update(self.document_embedding.metadata)
        combined.update(self.document_source.attribution_metadata)
        return combined


class DocumentSourceCreate(BaseModel):
    """Model for creating new document sources."""

    document_embedding_id: UUID = Field(
        ..., description="Reference to document embedding"
    )
    title: str = Field(..., min_length=1, description="Document title for display")
    location: str = Field(..., description="Document storage location/URL")
    access_info: Dict[str, Any] = Field(
        default_factory=dict, description="Access permissions and metadata"
    )
    attribution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for attribution tracking"
    )


class DocumentSourceUpdate(BaseModel):
    """Model for updating existing document sources."""

    title: Optional[str] = Field(
        None, min_length=1, description="Document title for display"
    )
    location: Optional[str] = Field(None, description="Document storage location/URL")
    access_info: Optional[Dict[str, Any]] = Field(
        None, description="Access permissions and metadata"
    )
    attribution_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for attribution tracking"
    )
    access_state: Optional[str] = Field(None, description="Document access state")


class DocumentSourceSearchResult(BaseModel):
    """Search result for document sources."""

    document_source: DocumentSource
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    rank: int = Field(..., ge=1, description="Rank in search results")

    def is_relevant(self, threshold: float = 0.7) -> bool:
        """Check if result is relevant based on relevance threshold."""
        return self.relevance_score >= threshold
