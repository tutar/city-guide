"""
Document access API endpoints for City Guide Smart Assistant

This module provides endpoints for document access verification,
and preview functionality for document source attribution.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize services
_embedding_service = EmbeddingService()


class DocumentPreviewResponse(BaseModel):
    """Response model for document preview."""

    document_id: str = Field(..., description="Document source UUID")
    title: str = Field(..., description="Document title")
    location: str = Field(..., description="Document location/URL")
    content: str = Field(..., description="Preview content based on preview type")


@router.get("/preview", response_model=DocumentPreviewResponse)
async def get_document_preview(
    document_id: str = Query(..., description="Document source UUID")
):
    """
    Get document preview information.

    This endpoint provides preview information for a document source,
    including metadata, excerpts, or full content based on preview type.
    """
    try:
        # Get document source
        document_source = _embedding_service.get_document_by_id(document_id)
        if not document_source:
            raise HTTPException(
                status_code=404,
                detail=f"Document source not found: {document_id}",
            )

        return DocumentPreviewResponse(
            document_id=document_id,
            title=document_source.get("title", ""),
            location=document_source.get("document_url", ""),
            content=document_source.get("content", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document preview for {document_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document preview: {str(e)}"
        )


@router.get("/citations", response_model=List[DocumentPreviewResponse])
async def get_citation_documents(
    document_ids: List[str] = Query(..., description="要查询的项目名称列表")
):
    """
    Get document preview information.

    This endpoint provides preview information for a document source,
    including metadata, excerpts, or full content based on preview type.
    """
    try:
        documents = []
        for document_id in document_ids:
            # Get document source
            document_source = _embedding_service.get_document_by_id(document_id)
            if not document_source:
                continue

            summary = (
                document_source.get("content", "")[:25] + "..."
            )  # Simple summary logic
            documents.append(
                DocumentPreviewResponse(
                    document_id=document_id,
                    title=document_source.get("title", ""),
                    location=document_source.get("document_url", ""),
                    content=summary,
                )
            )
        return documents

    except Exception as e:
        logger.error(f"Failed to get document preview for {document_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document preview: {str(e)}"
        )
