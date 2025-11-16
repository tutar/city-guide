"""
Attribution data models for document source tracking.

This module defines the data models for tracking document source attribution
in AI-generated responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class DocumentSource(BaseModel):
    """Represents a source document with metadata for attribution."""

    id: UUID = Field(default_factory=uuid4, description="UUID (primary key)")
    title: str = Field(..., min_length=1, description="Document title for display")
    location: str = Field(..., description="Document storage location/URL")
    access_info: Dict[str, Any] = Field(
        default_factory=dict, description="Access permissions and metadata"
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


class SentenceAttribution(BaseModel):
    """Maps sentences in AI responses to source documents."""

    id: UUID = Field(default_factory=uuid4, description="UUID (primary key)")
    response_id: UUID = Field(..., description="Reference to AI response")
    sentence_index: int = Field(
        ..., ge=0, description="Position of sentence in response"
    )
    document_id: UUID = Field(..., description="Reference to source document")
    title: str = Field(..., min_length=1, description="Document title for display")
    document: Dict[str, Any] = Field(
        ..., description="Source document metadata and content"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence in attribution (0.0-1.0)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When attribution was created"
    )


class CitationList(BaseModel):
    """Complete collection of documents referenced in an AI response."""

    id: UUID = Field(default_factory=uuid4, description="UUID (primary key)")
    response_id: UUID = Field(..., description="Reference to AI response")
    document_sources: List[UUID] = Field(
        default_factory=list, description="List of referenced document IDs"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When citation list was created"
    )

    @field_validator("document_sources")
    @classmethod
    def validate_document_sources(cls, v):
        """Ensure document sources list contains valid UUIDs."""
        # This validation ensures all items are UUIDs, but since we're using UUID type,
        # Pydantic will handle the validation automatically
        return v


class ResponseAttribution(BaseModel):
    """Complete attribution data for an AI response."""

    sentence_attributions: List[SentenceAttribution] = Field(
        default_factory=list,
        description="Attribution mapping for each sentence in response",
    )
    citation_list: CitationList = Field(
        ..., description="Complete citation list for the response"
    )


class AttributionMetadata(BaseModel):
    """Metadata for attribution tracking and performance monitoring."""

    total_sentences: int = Field(default=0)
    attributed_sentences: int = Field(default=0)


# State enums for document access and attribution tracking
class DocumentAccessState:
    """Document access states."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"


class AttributionTrackingState:
    """Attribution tracking states."""

    GENERATING = "generating"
    ATTRIBUTED = "attributed"
    DISPLAYED = "displayed"
