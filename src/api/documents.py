"""
Document access API endpoints for City Guide Smart Assistant

This module provides endpoints for document access verification, navigation,
and preview functionality for document source attribution.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize services
_document_service = DocumentService()


class DocumentAccessRequest(BaseModel):
    """Request model for document access verification."""

    document_id: str = Field(..., description="Document source UUID")


class DocumentAccessResponse(BaseModel):
    """Response model for document access verification."""

    document_id: str = Field(..., description="Document source UUID")
    accessible: bool = Field(..., description="Whether document is accessible")
    access_state: str = Field(..., description="Document access state")
    permission: str = Field(..., description="Access permission level")
    title: str = Field(..., description="Document title")
    location: str = Field(..., description="Document location/URL")
    reason: str | None = Field(None, description="Reason if not accessible")


class BulkDocumentAccessRequest(BaseModel):
    """Request model for bulk document access verification."""

    document_ids: List[str] = Field(..., description="List of document source UUIDs")


class BulkDocumentAccessResponse(BaseModel):
    """Response model for bulk document access verification."""

    results: Dict[str, DocumentAccessResponse] = Field(
        ..., description="Access results for each document"
    )
    statistics: Dict[str, Any] = Field(..., description="Bulk access statistics")


class DocumentPreviewRequest(BaseModel):
    """Request model for document preview."""

    document_id: str = Field(..., description="Document source UUID")
    preview_type: str = Field(
        default="metadata", description="Preview type: metadata, excerpt, or full"
    )


class DocumentPreviewResponse(BaseModel):
    """Response model for document preview."""

    document_id: str = Field(..., description="Document source UUID")
    preview_type: str = Field(..., description="Preview type requested")
    title: str = Field(..., description="Document title")
    location: str = Field(..., description="Document location/URL")
    access_state: str = Field(..., description="Document access state")
    preview_content: Dict[str, Any] = Field(
        ..., description="Preview content based on preview type"
    )
    attribution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document attribution metadata"
    )


@router.post("/access/verify", response_model=DocumentAccessResponse)
async def verify_document_access(request: DocumentAccessRequest):
    """
    Verify access to a specific document source.

    This endpoint checks if a document is accessible and returns detailed
    access information including permission level and access state.
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

        # Verify document access
        access_info = _document_service.verify_document_access(document_id)

        return DocumentAccessResponse(
            document_id=str(document_id),
            accessible=access_info["accessible"],
            access_state=access_info["access_state"],
            permission=access_info["permission"],
            title=access_info["title"],
            location=access_info["location"],
            reason=access_info.get("reason"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify document access for {request.document_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to verify document access: {str(e)}"
        )


@router.post("/access/bulk-verify", response_model=BulkDocumentAccessResponse)
async def bulk_verify_document_access(request: BulkDocumentAccessRequest):
    """
    Verify access for multiple documents in bulk.

    This endpoint efficiently checks access for multiple documents
    and returns aggregated statistics.
    """
    try:
        # Parse document IDs
        document_ids = []
        for doc_id_str in request.document_ids:
            try:
                document_ids.append(UUID(doc_id_str))
            except ValueError:
                logger.warning(f"Skipping invalid document ID: {doc_id_str}")

        if not document_ids:
            raise HTTPException(
                status_code=400, detail="No valid document IDs provided"
            )

        # Bulk verify access
        bulk_results = _document_service.bulk_verify_access(document_ids)

        # Convert results to response format
        results = {}
        accessible_count = 0

        for doc_id, access_info in bulk_results.items():
            response = DocumentAccessResponse(
                document_id=str(doc_id),
                accessible=access_info["accessible"],
                access_state=access_info["access_state"],
                permission=access_info["permission"],
                title=access_info["title"],
                location=access_info["location"],
                reason=access_info.get("reason"),
            )
            results[str(doc_id)] = response

            if access_info["accessible"]:
                accessible_count += 1

        # Calculate statistics
        total_count = len(document_ids)
        statistics = {
            "total_documents": total_count,
            "accessible_documents": accessible_count,
            "unaccessible_documents": total_count - accessible_count,
            "accessibility_rate": accessible_count / total_count
            if total_count > 0
            else 0.0,
        }

        return BulkDocumentAccessResponse(results=results, statistics=statistics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk verify document access: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk verify document access: {str(e)}"
        )


@router.post("/preview", response_model=DocumentPreviewResponse)
async def get_document_preview(request: DocumentPreviewRequest):
    """
    Get document preview information.

    This endpoint provides preview information for a document source,
    including metadata, excerpts, or full content based on preview type.
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

        # Verify access first
        access_info = _document_service.verify_document_access(document_id)
        if not access_info["accessible"]:
            raise HTTPException(
                status_code=403,
                detail=f"Document not accessible: {access_info.get('reason', 'Access denied')}",
            )

        # Generate preview content based on type
        preview_content = {}

        if request.preview_type == "metadata":
            preview_content = {
                "title": document_source.title,
                "location": document_source.location,
                "access_state": document_source.access_state,
                "permission": document_source.get_access_permission(),
                "created_at": document_source.created_at.isoformat(),
                "updated_at": document_source.updated_at.isoformat(),
                "access_info": document_source.access_info,
                "is_accessible": document_source.is_accessible(),
            }
        elif request.preview_type == "excerpt":
            # In a real implementation, this would extract document excerpts
            # For now, provide enhanced metadata
            preview_content = {
                "title": document_source.title,
                "location": document_source.location,
                "summary": f"Document source: {document_source.title}",
                "key_metadata": {
                    "access_state": document_source.access_state,
                    "permission": document_source.get_access_permission(),
                    "attribution_keys": list(
                        document_source.attribution_metadata.keys()
                    ),
                },
                "excerpt_available": False,  # Placeholder for real excerpt extraction
            }
        elif request.preview_type == "full":
            # In a real implementation, this would fetch full document content
            preview_content = {
                "title": document_source.title,
                "location": document_source.location,
                "full_content_available": False,  # Placeholder for real content
                "metadata": {
                    "access_state": document_source.access_state,
                    "permission": document_source.get_access_permission(),
                    "created_at": document_source.created_at.isoformat(),
                    "updated_at": document_source.updated_at.isoformat(),
                },
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid preview type: {request.preview_type}"
            )

        return DocumentPreviewResponse(
            document_id=str(document_id),
            preview_type=request.preview_type,
            title=document_source.title,
            location=document_source.location,
            access_state=document_source.access_state,
            preview_content=preview_content,
            attribution_metadata=document_source.attribution_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document preview for {request.document_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document preview: {str(e)}"
        )


@router.get("/{document_id}/logs")
async def get_document_access_logs(document_id: str, limit: int = 50):
    """
    Get access logs for a specific document.

    This endpoint returns the access log history for a document source,
    showing when and how the document was accessed.
    """
    try:
        # Parse document ID
        try:
            doc_id = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid document ID format: {document_id}"
            )

        # Get access logs
        logs = _document_service.get_document_access_logs(
            document_id=doc_id, limit=limit
        )

        # Format logs for response
        formatted_logs = []
        for log in logs:
            formatted_logs.append(
                {
                    "timestamp": log["timestamp"].isoformat(),
                    "action": log["action"],
                    "success": log["success"],
                    "details": log.get("details"),
                }
            )

        return {
            "document_id": document_id,
            "total_logs": len(formatted_logs),
            "logs": formatted_logs,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access logs for {document_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document access logs: {str(e)}"
        )


@router.get("/stats")
async def get_document_service_stats():
    """
    Get document service statistics.

    This endpoint returns overall statistics about the document service,
    including document counts, access rates, and cache performance.
    """
    try:
        stats = _document_service.get_service_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get document service stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document service statistics: {str(e)}",
        )


@router.get("/analytics")
async def get_document_analytics(document_id: str | None = None):
    """
    Get detailed document access analytics.

    This endpoint returns detailed analytics data about document access
    patterns, including access counts, success rates, and activity timeline.
    """
    try:
        # Parse document ID if provided
        doc_uuid = None
        if document_id:
            try:
                doc_uuid = UUID(document_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid document ID format: {document_id}"
                )

        # Get analytics data
        analytics = _document_service.get_analytics_data(doc_uuid)

        return {"document_id": document_id, "analytics": analytics}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document analytics: {str(e)}"
        )
