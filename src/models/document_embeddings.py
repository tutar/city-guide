"""
Document embedding models for City Guide Smart Assistant
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class DocumentEmbedding(BaseModel):
    """Represents document embeddings for semantic search"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    service_category_id: uuid.UUID = Field(..., description="Related service category")
    document_type: str = Field(
        ...,
        description="Type of document: requirements, procedures, locations, faqs",
    )
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(
        ..., min_length=1, max_length=65535, description="Document content"
    )
    embedding: list[float] = Field(
        ..., description="Vector embedding of the document content"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source, language, etc.)",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(
        default=True, description="Whether this embedding is active"
    )

    @validator("document_type")
    @classmethod
    def validate_document_type(cls, v):
        valid_types = ["requirements", "procedures", "locations", "faqs"]
        if v not in valid_types:
            raise ValueError(f"Document type must be one of: {valid_types}")
        return v

    @validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v):
        if len(v) != 1024:
            raise ValueError(f"Embedding must be 1024-dimensional, got {len(v)}")
        return v

    @validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vector"""
        return len(self.embedding)

    def update_embedding(self, new_embedding: list[float]) -> None:
        """Update the embedding vector"""
        if len(new_embedding) != 1024:
            raise ValueError("New embedding must be 1024-dimensional")
        self.embedding = new_embedding
        self.updated_at = datetime.now(UTC)

    def mark_inactive(self) -> None:
        """Mark this embedding as inactive"""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class SearchResult(BaseModel):
    """Represents a search result with similarity score"""

    document: DocumentEmbedding
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score (0-1)"
    )
    rank: int = Field(..., ge=1, description="Rank in search results")

    @validator("similarity_score")
    @classmethod
    def validate_similarity_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity score must be between 0.0 and 1.0")
        return v

    def is_relevant(self, threshold: float = 0.7) -> bool:
        """Check if result is relevant based on similarity threshold"""
        return self.similarity_score >= threshold


class BatchEmbeddingRequest(BaseModel):
    """Request for batch embedding generation"""

    documents: list[dict[str, Any]] = Field(
        ..., description="List of documents to embed"
    )
    document_type: str = Field(..., description="Type of documents being embedded")
    service_category_id: uuid.UUID = Field(
        ..., description="Service category for all documents"
    )

    @validator("documents")
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError("At least one document must be provided")
        return v


class BatchEmbeddingResponse(BaseModel):
    """Response for batch embedding generation"""

    embeddings: list[DocumentEmbedding] = Field(
        ..., description="Generated document embeddings"
    )
    total_processed: int = Field(..., description="Total documents processed")
    failed_count: int = Field(..., description="Number of failed embeddings")
    processing_time: float = Field(..., description="Processing time in seconds")

    @property
    def success_rate(self) -> float:
        """Calculate success rate of embedding generation"""
        if self.total_processed == 0:
            return 0.0
        return (self.total_processed - self.failed_count) / self.total_processed
