"""
Source relevance explanation API endpoints for City Guide Smart Assistant.

This module provides endpoints for calculating and explaining source relevance
in AI responses, including relevance scoring and confidence metrics.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.relevance_service import get_relevance_service
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/relevance", tags=["relevance"])

# Initialize services
_relevance_service = get_relevance_service()
_document_service = DocumentService()


class RelevanceExplanationRequest(BaseModel):
    """Request model for source relevance explanation."""

    document_ids: List[str] = Field(..., description="List of document source UUIDs")
    user_query: str = Field(..., description="Original user query")
    ai_response: str = Field(..., description="AI-generated response")
    context_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional context metadata"
    )


class RelevanceFactor(BaseModel):
    """Model for individual relevance factors."""

    score: float = Field(..., description="Relevance score (0-1)")
    factors: List[str] = Field(..., description="Relevant factors")
    explanation: str = Field(..., description="Factor explanation")


class RelevanceExplanation(BaseModel):
    """Model for source relevance explanation."""

    document_id: str = Field(..., description="Document source UUID")
    title: str = Field(..., description="Document title")
    relevance_score: float = Field(..., description="Overall relevance score (0-1)")
    confidence_level: str = Field(..., description="Confidence level")
    explanation: str = Field(..., description="Human-readable explanation")
    relevance_factors: Dict[str, RelevanceFactor] = Field(
        ..., description="Detailed relevance factors"
    )
    accessibility: bool = Field(..., description="Whether document is accessible")
    access_state: str = Field(..., description="Document access state")


class RelevanceExplanationResponse(BaseModel):
    """Response model for source relevance explanation."""

    explanations: List[RelevanceExplanation] = Field(
        ..., description="Relevance explanations for each document"
    )
    statistics: Dict[str, Any] = Field(..., description="Relevance statistics")


class SingleDocumentRelevanceRequest(BaseModel):
    """Request model for single document relevance explanation."""

    document_id: str = Field(..., description="Document source UUID")
    user_query: str = Field(..., description="Original user query")
    ai_response: str = Field(..., description="AI-generated response")
    context_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional context metadata"
    )


@router.post("/explain", response_model=RelevanceExplanationResponse)
async def explain_source_relevance(request: RelevanceExplanationRequest):
    """
    Explain relevance of multiple document sources in AI response.

    This endpoint calculates relevance scores and generates explanations
    for why specific documents were cited in an AI response.
    """
    try:
        # Parse document IDs
        document_ids = []
        invalid_doc_ids = []

        for doc_id_str in request.document_ids:
            try:
                document_ids.append(UUID(doc_id_str))
            except ValueError:
                invalid_doc_ids.append(doc_id_str)

        if not document_ids:
            raise HTTPException(
                status_code=400, detail="No valid document IDs provided"
            )

        # Get document sources
        document_sources = []
        for doc_id in document_ids:
            doc_source = _document_service.get_document_source(doc_id)
            if doc_source:
                document_sources.append(doc_source)

        if not document_sources:
            raise HTTPException(
                status_code=404, detail="No valid document sources found"
            )

        # Calculate relevance explanations
        explanations = _relevance_service.explain_multiple_sources(
            document_sources=document_sources,
            user_query=request.user_query,
            ai_response=request.ai_response,
            context_metadata=request.context_metadata,
        )

        # Generate statistics
        statistics = _relevance_service.get_relevance_statistics(explanations)

        # Add invalid document info to statistics
        if invalid_doc_ids:
            statistics["invalid_document_ids"] = invalid_doc_ids

        logger.info(
            f"Generated relevance explanations for {len(document_sources)} documents. "
            f"Average relevance: {statistics.get('average_relevance', 0):.3f}"
        )

        return RelevanceExplanationResponse(
            explanations=explanations, statistics=statistics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate relevance explanations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate relevance explanations: {str(e)}",
        )


@router.post("/explain/single", response_model=RelevanceExplanation)
async def explain_single_document_relevance(request: SingleDocumentRelevanceRequest):
    """
    Explain relevance of a single document source.

    This endpoint provides detailed relevance explanation for a single
    document source in the context of an AI response.
    """
    try:
        # Parse document ID
        try:
            document_id = UUID(request.document_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document ID format: {request.document_id}",
            )

        # Get document source
        document_source = _document_service.get_document_source(document_id)
        if not document_source:
            raise HTTPException(
                status_code=404, detail=f"Document not found: {request.document_id}"
            )

        # Calculate relevance explanation
        explanation = _relevance_service.calculate_relevance_score(
            document_source=document_source,
            user_query=request.user_query,
            ai_response=request.ai_response,
            context_metadata=request.context_metadata,
        )

        logger.info(
            f"Generated single document relevance explanation for {request.document_id}. "
            f"Score: {explanation['relevance_score']:.3f}"
        )

        return explanation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to generate single document relevance explanation "
            f"for {request.document_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate relevance explanation: {str(e)}",
        )


@router.get("/statistics")
async def get_relevance_statistics():
    """
    Get relevance service statistics.

    This endpoint returns statistics about the relevance service,
    including cache performance and calculation metrics.
    """
    try:
        # In a real implementation, this would return actual service statistics
        # For now, return basic cache information
        stats = {
            "cache_size": len(_relevance_service._relevance_cache),
            "service_ready": True,
            "calculation_method": "multi-factor weighted scoring",
            "factors_considered": [
                "query relevance",
                "response relevance",
                "metadata relevance",
            ],
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to get relevance statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get relevance statistics: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_relevance_cache():
    """
    Clear the relevance calculation cache.

    This endpoint clears the cache used for relevance calculations,
    forcing fresh calculations on next request.
    """
    try:
        _relevance_service.clear_cache()

        logger.info("Relevance cache cleared")

        return {"success": True, "message": "Relevance cache cleared successfully"}

    except Exception as e:
        logger.error(f"Failed to clear relevance cache: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear relevance cache: {str(e)}"
        )
