"""
Embedding-related data models for City Guide Smart Assistant
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class DocumentEmbedding(BaseModel):
    """Represents vector embeddings for government service documents"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_id: uuid.UUID = Field(
        ..., description="Reference to official information source"
    )
    document_url: str = Field(..., description="Original document URL")
    document_title: str = Field(..., description="Document title")
    document_content: str = Field(..., description="Processed document content")
    chunk_index: int = Field(default=0, description="Index for document chunks")
    embedding_vector: list[float] = Field(
        ..., description="Vector embedding (1024 dimensions for Qwen3-Embedding-0.6B)"
    )
    embedding_model: str = Field(
        default="Qwen/Qwen3-Embedding-0.6B", description="Model used for embedding"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("document_content")
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Document content must be non-empty")
        return v.strip()

    @validator("embedding_vector")
    def validate_embedding_dimension(cls, v):
        expected_dimension = 1024  # Qwen3-Embedding-0.6B dimension
        if len(v) != expected_dimension:
            raise ValueError(
                f"Embedding vector must be {expected_dimension} dimensions"
            )
        return v

    @validator("metadata")
    def validate_metadata(cls, v):
        # Ensure source priority is set
        if "source_priority" not in v:
            v["source_priority"] = "official"  # default to official
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class SearchQuery(BaseModel):
    """Represents user search queries for analytics and improvement"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: str = Field(..., description="User session identifier")
    query_text: str = Field(..., description="Original search query")
    query_embedding: list[float] = Field(..., description="Query embedding vector")
    search_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Retrieved document IDs and scores"
    )
    hybrid_score: float | None = Field(None, description="Combined hybrid search score")
    response_quality: int | None = Field(
        None, ge=1, le=5, description="User feedback rating (1-5)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("query_text")
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Query text cannot be empty")
        return v.strip()

    @validator("query_embedding")
    def validate_query_embedding(cls, v):
        expected_dimension = 1024  # Qwen3-Embedding-0.6B dimension
        if len(v) != expected_dimension:
            raise ValueError(f"Query embedding must be {expected_dimension} dimensions")
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class SearchResult(BaseModel):
    """Represents a single search result with relevance scoring"""

    document_id: uuid.UUID
    document_title: str
    document_content: str
    source_url: str
    similarity_score: float
    keyword_score: float | None = None
    hybrid_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("similarity_score")
    def validate_similarity_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Similarity score must be between 0 and 1")
        return v

    class Config:
        json_encoders = {
            uuid.UUID: str,
        }


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search combining semantic and keyword search"""

    query: str = Field(..., description="Search query text")
    service_category_id: uuid.UUID | None = Field(
        None, description="Filter by service category"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )
    include_keyword_search: bool = Field(
        default=True, description="Include BM25 keyword search"
    )
    include_semantic_search: bool = Field(
        default=True, description="Include semantic vector search"
    )

    @validator("query")
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    class Config:
        json_encoders = {
            uuid.UUID: str,
        }
