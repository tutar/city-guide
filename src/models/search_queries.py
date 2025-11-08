"""
Search query models for City Guide Smart Assistant
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchQuery(BaseModel):
    """Represents user search queries for analytics and improvement"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_session_id: str = Field(..., description="Anonymous session identifier")
    query_text: str = Field(
        ..., min_length=1, max_length=1000, description="Original search query"
    )
    normalized_query: str = Field(
        ..., min_length=1, max_length=1000, description="Normalized search query"
    )
    search_type: str = Field(
        default="hybrid",
        description="Type of search: hybrid, vector, keyword",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Search filters applied (service_type, location, etc.)",
    )
    result_count: int = Field(default=0, ge=0, description="Number of results returned")
    processing_time_ms: int = Field(
        default=0, ge=0, description="Search processing time in milliseconds"
    )
    user_feedback: Optional[str] = Field(
        None, description="User feedback on search results"
    )
    satisfaction_score: Optional[int] = Field(
        None, ge=1, le=5, description="User satisfaction score (1-5)"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("search_type")
    @classmethod
    def validate_search_type(cls, v):
        valid_types = ["hybrid", "vector", "keyword"]
        if v not in valid_types:
            raise ValueError(f"Search type must be one of: {valid_types}")
        return v

    @field_validator("query_text")
    @classmethod
    def query_text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Query text cannot be empty")
        return v.strip()

    @field_validator("normalized_query")
    @classmethod
    def normalized_query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Normalized query cannot be empty")
        return v.strip()

    def calculate_success_metrics(self) -> dict[str, Any]:
        """Calculate search success metrics"""
        return {
            "has_results": self.result_count > 0,
            "processing_efficiency": self.processing_time_ms
            / max(self.result_count, 1),
            "user_satisfaction": self.satisfaction_score is not None,
        }

    def mark_satisfaction(self, score: int, feedback: Optional[str] = None) -> None:
        """Record user satisfaction with search results"""
        if not 1 <= score <= 5:
            raise ValueError("Satisfaction score must be between 1 and 5")

        self.satisfaction_score = score
        if feedback:
            self.user_feedback = feedback

    model_config = ConfigDict(
        json_encoders={
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class SearchAnalytics(BaseModel):
    """Aggregated search analytics data"""

    period_start: datetime = Field(..., description="Start of analytics period")
    period_end: datetime = Field(..., description="End of analytics period")
    total_searches: int = Field(..., ge=0, description="Total searches in period")
    successful_searches: int = Field(
        ..., ge=0, description="Searches with at least one result"
    )
    average_processing_time: float = Field(
        ..., ge=0.0, description="Average processing time in milliseconds"
    )
    average_satisfaction_score: Optional[float] = Field(
        None, ge=1.0, le=5.0, description="Average user satisfaction score"
    )
    top_queries: list[dict[str, Any]] = Field(
        default_factory=list, description="Most frequent search queries"
    )
    query_success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Percentage of successful searches"
    )

    @property
    def failed_searches(self) -> int:
        """Calculate number of failed searches"""
        return self.total_searches - self.successful_searches

    @property
    def failure_rate(self) -> float:
        """Calculate search failure rate"""
        if self.total_searches == 0:
            return 0.0
        return self.failed_searches / self.total_searches

    def add_search_query(self, query: SearchQuery) -> None:
        """Add a search query to analytics (for real-time updates)"""
        self.total_searches += 1

        if query.result_count > 0:
            self.successful_searches += 1

        # Update average processing time
        current_total_time = self.average_processing_time * (self.total_searches - 1)
        self.average_processing_time = (
            current_total_time + query.processing_time_ms
        ) / self.total_searches

        # Update average satisfaction score
        if query.satisfaction_score:
            if self.average_satisfaction_score is None:
                self.average_satisfaction_score = query.satisfaction_score
            else:
                current_total_score = self.average_satisfaction_score * (
                    self.total_searches - 1
                )
                self.average_satisfaction_score = (
                    current_total_score + query.satisfaction_score
                ) / self.total_searches


class QuerySuggestion(BaseModel):
    """Represents search query suggestions"""

    original_query: str = Field(..., description="Original user query")
    suggested_query: str = Field(..., description="Suggested improved query")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in suggestion"
    )
    reason: str = Field(..., description="Reason for suggestion")
    usage_count: int = Field(
        default=0, ge=0, description="How often suggestion was used"
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    def increment_usage(self) -> None:
        """Increment usage count for this suggestion"""
        self.usage_count += 1

    def is_high_confidence(self) -> bool:
        """Check if suggestion has high confidence"""
        return self.confidence_score >= 0.8
