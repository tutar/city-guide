"""
Document service for managing document sources and access.

This service handles document metadata management, access verification,
and integration with the existing document embedding system.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.models.document_source import (
    DocumentSource,
    DocumentSourceWithEmbedding,
    DocumentSourceCreate,
    DocumentSourceUpdate,
    DocumentSourceSearchResult,
)
from src.models.document_embeddings import DocumentEmbedding

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document sources and access."""

    def __init__(self):
        self._document_cache: Dict[UUID, DocumentSource] = {}
        self._access_log: List[Dict[str, Any]] = []
        self._analytics_data: Dict[str, Any] = {
            "total_accesses": 0,
            "successful_accesses": 0,
            "failed_accesses": 0,
            "access_by_action": {},
            "access_by_document": {},
            "access_timeline": [],
        }

    def create_document_source(
        self, create_data: DocumentSourceCreate
    ) -> DocumentSource:
        """
        Create a new document source.

        Args:
            create_data: Document source creation data

        Returns:
            Created DocumentSource object
        """
        document_source = DocumentSource(
            document_embedding_id=create_data.document_embedding_id,
            title=create_data.title,
            location=create_data.location,
            access_info=create_data.access_info,
            attribution_metadata=create_data.attribution_metadata,
        )

        # Cache the document source
        self._document_cache[document_source.id] = document_source

        logger.info(
            f"Created document source {document_source.id}: "
            f"{document_source.title} at {document_source.location}"
        )

        return document_source

    def get_document_source(self, document_id: UUID) -> Optional[DocumentSource]:
        """
        Get document source by ID.

        Args:
            document_id: UUID of the document source

        Returns:
            DocumentSource if found, None otherwise
        """
        document_source = self._document_cache.get(document_id)

        if document_source:
            self._log_access(document_id, "read", success=True)
        else:
            self._log_access(document_id, "read", success=False)

        return document_source

    def get_document_source_with_embedding(
        self,
        document_id: UUID,
        embedding_service: Any = None,  # Would be actual embedding service
    ) -> Optional[DocumentSourceWithEmbedding]:
        """
        Get document source with embedding information.

        Args:
            document_id: UUID of the document source
            embedding_service: Service to fetch embedding data

        Returns:
            DocumentSourceWithEmbedding if found, None otherwise
        """
        document_source = self.get_document_source(document_id)
        if not document_source:
            return None

        # In a real implementation, this would fetch from the embedding service
        document_embedding = None
        if embedding_service:
            # This would be: embedding_service.get_embedding(document_source.document_embedding_id)
            pass

        return DocumentSourceWithEmbedding(
            document_source=document_source, document_embedding=document_embedding
        )

    def sync_with_embedding_system(
        self, embedding_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync document sources with the embedding system.

        Args:
            embedding_documents: List of documents from embedding system

        Returns:
            Sync statistics
        """
        stats = {
            "total_embedding_documents": len(embedding_documents),
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

        for embedding_doc in embedding_documents:
            try:
                # Extract embedding document ID
                embedding_id = embedding_doc.get("id")
                if not embedding_id:
                    stats["errors"] += 1
                    continue

                # Check if document source already exists
                existing_source = self._find_by_embedding_id(embedding_id)

                if existing_source:
                    # Update existing document source
                    update_data = DocumentSourceUpdate(
                        title=embedding_doc.get("title"),
                        location=embedding_doc.get(
                            "location", f"/documents/{embedding_id}"
                        ),
                        attribution_metadata={
                            "embedding_id": str(embedding_id),
                            "document_type": embedding_doc.get(
                                "document_type", "unknown"
                            ),
                            "last_synced": datetime.now().isoformat(),
                        },
                    )
                    self.update_document_source(existing_source.id, update_data)
                    stats["updated"] += 1
                else:
                    # Create new document source
                    create_data = DocumentSourceCreate(
                        document_embedding_id=embedding_id,
                        title=embedding_doc.get("title", "Untitled Document"),
                        location=embedding_doc.get(
                            "location", f"/documents/{embedding_id}"
                        ),
                        access_info={"permission": "public"},
                        attribution_metadata={
                            "embedding_id": str(embedding_id),
                            "document_type": embedding_doc.get(
                                "document_type", "unknown"
                            ),
                            "created_from_sync": True,
                            "last_synced": datetime.now().isoformat(),
                        },
                    )
                    self.create_document_source(create_data)
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to sync document {embedding_doc.get('id')}: {e}")
                stats["errors"] += 1

        logger.info(
            f"Document sync completed: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['errors']} errors"
        )

        return stats

    def _find_by_embedding_id(self, embedding_id: UUID) -> Optional[DocumentSource]:
        """
        Find document source by embedding ID.

        Args:
            embedding_id: Embedding document ID

        Returns:
            DocumentSource if found, None otherwise
        """
        for document_source in self._document_cache.values():
            if document_source.document_embedding_id == embedding_id:
                return document_source
        return None

    def bulk_verify_access(
        self, document_ids: List[UUID]
    ) -> Dict[UUID, Dict[str, Any]]:
        """
        Verify access for multiple documents in bulk.

        Args:
            document_ids: List of document IDs to verify

        Returns:
            Dictionary mapping document ID to access verification results
        """
        results = {}

        for doc_id in document_ids:
            results[doc_id] = self.verify_document_access(doc_id)

        # Calculate bulk statistics
        accessible_count = sum(1 for result in results.values() if result["accessible"])
        logger.info(
            f"Bulk access verification: {accessible_count}/{len(document_ids)} "
            f"documents accessible ({accessible_count/len(document_ids)*100:.1f}%)"
        )

        return results

    def update_document_source(
        self, document_id: UUID, update_data: DocumentSourceUpdate
    ) -> Optional[DocumentSource]:
        """
        Update an existing document source.

        Args:
            document_id: UUID of the document source
            update_data: Update data

        Returns:
            Updated DocumentSource if found, None otherwise
        """
        document_source = self.get_document_source(document_id)
        if not document_source:
            return None

        # Update fields if provided
        if update_data.title is not None:
            document_source.title = update_data.title
        if update_data.location is not None:
            document_source.location = update_data.location
        if update_data.access_info is not None:
            document_source.access_info = update_data.access_info
        if update_data.attribution_metadata is not None:
            document_source.attribution_metadata = update_data.attribution_metadata
        if update_data.access_state is not None:
            document_source.update_access_state(update_data.access_state)

        document_source.updated_at = datetime.now()

        logger.info(f"Updated document source {document_id}")
        self._log_access(document_id, "update", success=True)

        return document_source

    def verify_document_access(self, document_id: UUID) -> Dict[str, Any]:
        """
        Verify document access and return access information.

        Args:
            document_id: UUID of the document source

        Returns:
            Dictionary with access verification results
        """
        document_source = self.get_document_source(document_id)
        if not document_source:
            result = {
                "accessible": False,
                "reason": "Document not found",
                "access_state": "unavailable",
            }
            self._log_access(document_id, "verify", success=False)
            return result

        is_accessible = document_source.is_accessible()
        permission = document_source.get_access_permission()

        result = {
            "accessible": is_accessible,
            "access_state": document_source.access_state,
            "permission": permission,
            "title": document_source.title,
            "location": document_source.location,
        }

        self._log_access(document_id, "verify", success=is_accessible)

        return result

    def handle_document_access_failure(
        self, document_id: UUID, failure_reason: str
    ) -> Dict[str, Any]:
        """
        Handle document access failure with graceful degradation.

        Args:
            document_id: UUID of the document source
            failure_reason: Reason for access failure

        Returns:
            Dictionary with graceful degradation information
        """
        document_source = self.get_document_source(document_id)

        if document_source:
            # Try to update access state if document exists
            try:
                document_source.update_access_state("unavailable")
            except Exception as e:
                logger.warning(f"Failed to update access state for {document_id}: {e}")

        degradation_info = {
            "document_id": str(document_id),
            "accessible": False,
            "failure_reason": failure_reason,
            "graceful_degradation": True,
            "preserved_metadata": {
                "title": document_source.title if document_source else "Unknown",
                "access_state": document_source.access_state
                if document_source
                else "unavailable",
            },
        }

        logger.warning(
            f"Document access failure for {document_id}: {failure_reason}. "
            f"Graceful degradation applied."
        )

        self._log_access(
            document_id, "access_failure", success=False, details=failure_reason
        )

        return degradation_info

    def search_document_sources(
        self, query: str, max_results: int = 10
    ) -> List[DocumentSourceSearchResult]:
        """
        Search document sources by title and metadata.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not query.strip():
            return []

        results = []
        query_lower = query.lower()

        for document_source in self._document_cache.values():
            # Simple text matching for demonstration
            # In production, this would use proper search engine
            relevance_score = 0.0

            # Check title match
            if query_lower in document_source.title.lower():
                relevance_score += 0.7

            # Check metadata match
            for key, value in document_source.attribution_metadata.items():
                if isinstance(value, str) and query_lower in value.lower():
                    relevance_score += 0.3
                    break

            if relevance_score > 0:
                results.append(
                    DocumentSourceSearchResult(
                        document_source=document_source,
                        relevance_score=min(relevance_score, 1.0),
                        rank=len(results) + 1,
                    )
                )

        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Limit results
        results = results[:max_results]

        logger.info(f"Document search for '{query}': found {len(results)} results")

        return results

    def get_document_access_logs(
        self, document_id: Optional[UUID] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get document access logs.

        Args:
            document_id: Optional filter by document ID
            limit: Maximum number of logs to return

        Returns:
            List of access logs
        """
        logs = self._access_log.copy()

        if document_id:
            logs = [log for log in logs if log.get("document_id") == document_id]

        return logs[-limit:]

    def _log_access(
        self,
        document_id: UUID,
        action: str,
        success: bool,
        details: Optional[str] = None,
    ) -> None:
        """Log document access attempt and update analytics."""
        timestamp = datetime.now()
        log_entry = {
            "timestamp": timestamp,
            "document_id": document_id,
            "action": action,
            "success": success,
            "details": details,
        }

        self._access_log.append(log_entry)

        # Update analytics data
        self._update_analytics(log_entry)

        # Keep access log size manageable
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]

    def _update_analytics(self, log_entry: Dict[str, Any]) -> None:
        """Update analytics data with new access log entry."""
        # Update basic counters
        self._analytics_data["total_accesses"] += 1

        if log_entry["success"]:
            self._analytics_data["successful_accesses"] += 1
        else:
            self._analytics_data["failed_accesses"] += 1

        # Update action-based analytics
        action = log_entry["action"]
        if action not in self._analytics_data["access_by_action"]:
            self._analytics_data["access_by_action"][action] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
            }

        self._analytics_data["access_by_action"][action]["total"] += 1
        if log_entry["success"]:
            self._analytics_data["access_by_action"][action]["successful"] += 1
        else:
            self._analytics_data["access_by_action"][action]["failed"] += 1

        # Update document-based analytics
        document_id = str(log_entry["document_id"])
        if document_id not in self._analytics_data["access_by_document"]:
            self._analytics_data["access_by_document"][document_id] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "last_accessed": None,
            }

        self._analytics_data["access_by_document"][document_id]["total"] += 1
        if log_entry["success"]:
            self._analytics_data["access_by_document"][document_id]["successful"] += 1
        else:
            self._analytics_data["access_by_document"][document_id]["failed"] += 1

        self._analytics_data["access_by_document"][document_id][
            "last_accessed"
        ] = log_entry["timestamp"]

        # Update timeline (keep last 100 entries)
        timeline_entry = {
            "timestamp": log_entry["timestamp"].isoformat(),
            "document_id": document_id,
            "action": action,
            "success": log_entry["success"],
        }
        self._analytics_data["access_timeline"].append(timeline_entry)
        if len(self._analytics_data["access_timeline"]) > 100:
            self._analytics_data["access_timeline"] = self._analytics_data[
                "access_timeline"
            ][-50:]

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics
        """
        total_documents = len(self._document_cache)
        accessible_documents = sum(
            1 for doc in self._document_cache.values() if doc.is_accessible()
        )

        # Calculate analytics-based statistics
        total_accesses = self._analytics_data["total_accesses"]
        success_rate = (
            self._analytics_data["successful_accesses"] / total_accesses
            if total_accesses > 0
            else 0.0
        )

        # Get top accessed documents
        top_documents = sorted(
            self._analytics_data["access_by_document"].items(),
            key=lambda x: x[1]["total"],
            reverse=True,
        )[:5]

        # Get action distribution
        action_distribution = {
            action: {
                "total": data["total"],
                "success_rate": data["successful"] / data["total"]
                if data["total"] > 0
                else 0.0,
            }
            for action, data in self._analytics_data["access_by_action"].items()
        }

        return {
            "total_documents": total_documents,
            "accessible_documents": accessible_documents,
            "unavailable_documents": total_documents - accessible_documents,
            "access_log_entries": len(self._access_log),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "analytics": {
                "total_accesses": total_accesses,
                "successful_accesses": self._analytics_data["successful_accesses"],
                "failed_accesses": self._analytics_data["failed_accesses"],
                "success_rate": success_rate,
                "top_documents": [
                    {
                        "document_id": doc_id,
                        "total_accesses": data["total"],
                        "success_rate": data["successful"] / data["total"]
                        if data["total"] > 0
                        else 0.0,
                        "last_accessed": data["last_accessed"].isoformat()
                        if data["last_accessed"]
                        else None,
                    }
                    for doc_id, data in top_documents
                ],
                "action_distribution": action_distribution,
                "recent_activity": self._analytics_data["access_timeline"][-10:],
            },
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified for demonstration)."""
        # In a real implementation, this would track actual cache hits/misses
        total_accesses = len(self._access_log)
        if total_accesses == 0:
            return 0.0

        cache_hits = sum(1 for log in self._access_log if log.get("success", False))
        return cache_hits / total_accesses if total_accesses > 0 else 0.0

    def clear_cache(self) -> None:
        """Clear the document cache."""
        self._document_cache.clear()
        logger.info("Cleared document cache")

    def cleanup_old_logs(self, max_age_hours: int = 24) -> int:
        """
        Clean up old access logs.

        Args:
            max_age_hours: Maximum age of logs to keep in hours

        Returns:
            Number of logs removed
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        initial_count = len(self._access_log)
        self._access_log = [
            log
            for log in self._access_log
            if log["timestamp"].timestamp() > cutoff_time
        ]

        removed_count = initial_count - len(self._access_log)
        logger.info(f"Cleaned up {removed_count} old access logs")

        return removed_count

    def get_analytics_data(self, document_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get detailed analytics data.

        Args:
            document_id: Optional filter by document ID

        Returns:
            Detailed analytics data
        """
        analytics = self._analytics_data.copy()

        if document_id:
            doc_id_str = str(document_id)
            # Filter analytics by document
            analytics["access_by_document"] = {
                doc_id_str: analytics["access_by_document"].get(
                    doc_id_str,
                    {"total": 0, "successful": 0, "failed": 0, "last_accessed": None},
                )
            }
            # Filter timeline by document
            analytics["access_timeline"] = [
                entry
                for entry in analytics["access_timeline"]
                if entry["document_id"] == doc_id_str
            ]

        return analytics
