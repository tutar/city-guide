"""
Health check endpoints for City Guide Smart Assistant
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.services.data_service import DataService
from src.services.embedding_service import EmbeddingService
from src.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint"""
    return {"status": "healthy", "service": settings.app_name}


@router.get("/readiness")
async def readiness_check() -> dict[str, Any]:
    """Readiness check for all dependencies"""
    checks = {
        "database": {"status": "unknown", "details": ""},
        "vector_database": {"status": "unknown", "details": ""},
        "ai_service": {"status": "unknown", "details": ""},
    }

    try:
        # Check PostgreSQL database
        with DataService() as data_service:
            data_service.session.execute(text("SELECT 1"))
            checks["database"]["status"] = "healthy"
            checks["database"]["details"] = "Database connection successful"
    except Exception as e:
        checks["database"]["status"] = "unhealthy"
        checks["database"]["details"] = f"Database connection failed: {str(e)}"

    try:
        # Check Milvus vector database
        embedding_service = EmbeddingService()
        stats = embedding_service.get_collection_stats()
        checks["vector_database"]["status"] = "healthy"
        checks["vector_database"][
            "details"
        ] = f"Milvus collection: {stats['collection_name']}, entities: {stats['num_entities']}"
    except Exception as e:
        checks["vector_database"]["status"] = "unhealthy"
        checks["vector_database"]["details"] = f"Milvus connection failed: {str(e)}"

    try:
        # Check AI service (basic embedding generation)
        from src.services.ai_service import AIService

        ai_service = AIService()
        test_embedding = ai_service.generate_embedding("test")
        checks["ai_service"]["status"] = "healthy"
        checks["ai_service"][
            "details"
        ] = f"AI service working, embedding dimension: {len(test_embedding)}"
    except Exception as e:
        checks["ai_service"]["status"] = "unhealthy"
        checks["ai_service"]["details"] = f"AI service failed: {str(e)}"

    # Determine overall status
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    overall_status = "healthy" if all_healthy else "degraded"

    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
    }


@router.get("/liveness")
async def liveness_check() -> dict[str, str]:
    """Liveness check for container orchestration"""
    return {
        "status": "alive",
        "service": settings.app_name,
        "timestamp": "2025-11-08T13:25:00Z",  # This would be dynamic in production
    }


@router.get("/version")
async def version_info() -> dict[str, str]:
    """Get service version information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": "development",  # This could be configurable
    }


@router.get("/metrics")
async def metrics_endpoint() -> dict[str, Any]:
    """Basic metrics endpoint for monitoring"""
    try:
        # Database metrics
        with DataService() as data_service:
            # Get service categories count
            categories_count = data_service.session.execute(
                text("SELECT COUNT(*) FROM service_categories WHERE is_active = true")
            ).scalar()

            # Get conversation contexts count
            contexts_count = data_service.session.execute(
                text(
                    "SELECT COUNT(*) FROM conversation_contexts WHERE is_active = true"
                )
            ).scalar()

        # Vector database metrics
        embedding_service = EmbeddingService()
        vector_stats = embedding_service.get_collection_stats()

        return {
            "database": {
                "service_categories": categories_count or 0,
                "conversation_contexts": contexts_count or 0,
            },
            "vector_database": {
                "collection_name": vector_stats["collection_name"],
                "num_entities": vector_stats["num_entities"],
            },
            "service": {
                "name": settings.app_name,
                "version": settings.app_version,
            },
        }

    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")
