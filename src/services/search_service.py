"""
Search service for City Guide Smart Assistant implementing hybrid search with RRF fusion
"""

import logging
from typing import Any

from src.models.embeddings import HybridSearchRequest, SearchResult
from src.services.ai_service import AIService
from src.services.bm25_service import BM25Service
from src.services.data_service import DataService
from src.services.embedding_service import EmbeddingService

# Configure logging
logger = logging.getLogger(__name__)


class SearchService:
    """Service for hybrid search combining semantic and keyword search"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.ai_service = AIService()
        self.bm25_service = BM25Service()

    def hybrid_search(self, search_request: HybridSearchRequest) -> list[SearchResult]:
        """Perform hybrid search with RRF fusion"""
        try:
            # Generate query embedding
            query_embedding = self.ai_service.generate_embedding(search_request.query)

            # Perform semantic search
            semantic_results = []
            if search_request.include_semantic_search:
                semantic_results = self._semantic_search(
                    query_embedding, search_request
                )

            # Perform keyword search
            keyword_results = []
            if search_request.include_keyword_search:
                keyword_results = self._keyword_search(
                    search_request.query, search_request
                )

            # Combine results using RRF fusion
            combined_results = self._rrf_fusion(
                semantic_results, keyword_results, search_request.limit
            )

            logger.info(f"Hybrid search completed: {len(combined_results)} results")
            return combined_results

        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            raise

    def _semantic_search(
        self, query_embedding: list[float], search_request: HybridSearchRequest
    ) -> list[dict[str, Any]]:
        """Perform semantic vector search"""
        try:
            # Build filter expression if service category is specified
            filter_expression = None
            if search_request.service_category_id:
                filter_expression = (
                    f"source_id == '{search_request.service_category_id}'"
                )

            # Search for similar documents
            semantic_results = self.embedding_service.search_similar_documents(
                query_embedding=query_embedding,
                limit=search_request.limit * 2,  # Get more results for fusion
                filter_expression=filter_expression,
            )

            # Convert to SearchResult format
            results = []
            for result in semantic_results:
                search_result = SearchResult(
                    document_id=result["document_id"],
                    document_title=result["document_title"],
                    document_content="",  # Content would be fetched separately
                    source_url=result["document_url"],
                    similarity_score=result["similarity_score"],
                    metadata=result.get("metadata", {}),
                )
                results.append(search_result)

            logger.debug(f"Semantic search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _keyword_search(
        self, query: str, search_request: HybridSearchRequest
    ) -> list[dict[str, Any]]:
        """Perform keyword search using BM25"""
        try:
            # Use BM25 service for keyword search
            bm25_results = self.bm25_service.search(
                query, limit=search_request.limit * 2
            )

            # Convert to SearchResult format
            keyword_results = []
            for result in bm25_results:
                search_result = SearchResult(
                    document_id=result.get("id", "unknown"),
                    document_title=result.get("document_title", "Unknown"),
                    document_content=result.get("document_content", ""),
                    source_url=result.get("source_url", ""),
                    similarity_score=result.get("bm25_score", 0),
                    keyword_score=result.get("bm25_score", 0),
                    metadata=result.get("metadata", {}),
                )
                keyword_results.append(search_result)

            logger.debug(f"BM25 keyword search found {len(keyword_results)} results")
            return keyword_results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _rrf_fusion(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
        limit: int,
    ) -> list[SearchResult]:
        """Combine search results using Reciprocal Rank Fusion"""
        try:
            # Create mapping of document_id to result
            all_results = {}

            # Add semantic results with ranks
            for rank, result in enumerate(semantic_results, 1):
                doc_id = str(result.document_id)
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "result": result,
                        "semantic_rank": rank,
                        "keyword_rank": None,
                    }
                else:
                    all_results[doc_id]["semantic_rank"] = rank

            # Add keyword results with ranks
            for rank, result in enumerate(keyword_results, 1):
                doc_id = str(result.document_id)
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "result": result,
                        "semantic_rank": None,
                        "keyword_rank": rank,
                    }
                else:
                    all_results[doc_id]["keyword_rank"] = rank

            # Calculate RRF scores
            k = 60  # RRF constant
            scored_results = []

            for doc_id, data in all_results.items():
                rrf_score = 0

                # Add semantic rank contribution
                if data["semantic_rank"] is not None:
                    rrf_score += 1 / (k + data["semantic_rank"])

                # Add keyword rank contribution
                if data["keyword_rank"] is not None:
                    rrf_score += 1 / (k + data["keyword_rank"])

                # Update the result with hybrid score
                result = data["result"]
                result.hybrid_score = rrf_score
                scored_results.append((rrf_score, result))

            # Sort by RRF score
            scored_results.sort(key=lambda x: x[0], reverse=True)

            # Return top results
            final_results = [result for score, result in scored_results[:limit]]

            logger.debug(f"RRF fusion completed: {len(final_results)} final results")
            return final_results

        except Exception as e:
            logger.error(f"RRF fusion failed: {e}")
            # Fallback to semantic results
            return semantic_results[:limit]

    def generate_dynamic_navigation_options(
        self, conversation_context: dict[str, Any], search_results: list[SearchResult]
    ) -> list[dict[str, Any]]:
        """Generate dynamic navigation options based on conversation context and search results"""
        try:
            navigation_options = []

            # Add navigation options based on search results
            for result in search_results[:3]:  # Top 3 results
                option = {
                    "label": f"Learn more about {result.document_title}",
                    "action_type": "explain",
                    "target_url": result.source_url,
                    "description": f"Detailed information about {result.document_title}",
                    "priority": 5,
                }
                navigation_options.append(option)

            # Add service category navigation if available
            if conversation_context.get("current_service_category_id"):
                with DataService() as data_service:
                    category_options = data_service.get_navigation_options_by_category(
                        conversation_context["current_service_category_id"]
                    )

                    for option in category_options:
                        navigation_options.append(
                            {
                                "label": option.label,
                                "action_type": option.action_type,
                                "target_url": option.target_url,
                                "description": option.description,
                                "priority": option.priority,
                            }
                        )

            # Generate AI-powered suggestions
            current_context = conversation_context.get("current_query", "")
            available_services = [
                result.document_title for result in search_results[:5]
            ]

            ai_suggestions = self.ai_service.generate_navigation_suggestions(
                current_context, available_services
            )

            for suggestion in ai_suggestions:
                navigation_options.append(
                    {
                        "label": suggestion["label"],
                        "action_type": suggestion["action_type"],
                        "priority": 3,
                    }
                )

            # Sort by priority
            navigation_options.sort(key=lambda x: x.get("priority", 5))

            logger.info(f"Generated {len(navigation_options)} navigation options")
            return navigation_options

        except Exception as e:
            logger.error(f"Failed to generate navigation options: {e}")
            return []

    def filter_navigation_options_by_category(
        self, navigation_options: list[dict[str, Any]], service_category_id: str
    ) -> list[dict[str, Any]]:
        """Filter navigation options by service category"""
        try:
            # This would filter options based on service category relevance
            # For now, return all options
            return navigation_options

        except Exception as e:
            logger.error(f"Failed to filter navigation options: {e}")
            return navigation_options

    def add_external_url_handling(self, url: str) -> dict[str, Any]:
        """Handle external URLs for appointment systems and other external services"""
        try:
            # Validate URL format
            if not url.startswith(("http://", "https://")):
                raise ValueError("Invalid URL format")

            # Check if it's a government service URL
            government_domains = [
                "gov.cn",
                "sz.gov.cn",
                "hongkong.gov.hk",
                "macau.gov.mo",
            ]

            is_government_url = any(domain in url for domain in government_domains)

            return {
                "url": url,
                "is_government_url": is_government_url,
                "requires_validation": not is_government_url,
                "handling_type": "external_redirect",
            }

        except Exception as e:
            logger.error(f"Failed to handle external URL: {e}")
            raise

    def search_documents(
        self, query: str, service_category_id: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Search for documents using hybrid search

        This method provides a simplified interface for document search
        that can be used by the conversation API.
        """
        try:
            # Create search request
            search_request = HybridSearchRequest(
                query=query,
                limit=limit,
                include_semantic_search=True,
                include_keyword_search=True,
                service_category_id=service_category_id,
            )

            # Perform hybrid search
            search_results = self.hybrid_search(search_request)

            # Convert to simple dict format for API response
            documents = []
            for result in search_results:
                doc = {
                    "document_id": str(result.document_id),
                    "document_title": result.document_title,
                    "document_content": result.document_content,
                    "source_url": result.source_url,
                    "similarity_score": result.similarity_score,
                    "hybrid_score": getattr(result, "hybrid_score", 0),
                    "metadata": result.metadata,
                }
                documents.append(doc)

            logger.info(f"Search documents completed: {len(documents)} results")
            return documents

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            # Return empty list as fallback
            return []

    def get_related_services(
        self, current_service: str, user_session_id: str
    ) -> list[dict[str, Any]]:
        """Get related services based on current service and conversation context"""
        try:
            # Define service relationships
            service_relationships = {
                "passport": [
                    {
                        "name": "Hong Kong Visa Services",
                        "description": "Visa application and extension services",
                        "relevance_score": 0.8,
                        "reason": "Often needed together for international travel"
                    },
                    {
                        "name": "Hong Kong ID Card Services",
                        "description": "ID card application and renewal",
                        "relevance_score": 0.6,
                        "reason": "Common identification document"
                    },
                    {
                        "name": "Business Registration",
                        "description": "Business registration and licensing",
                        "relevance_score": 0.4,
                        "reason": "May be needed for business travel"
                    }
                ],
                "visa": [
                    {
                        "name": "Hong Kong Passport Services",
                        "description": "Passport application and renewal services",
                        "relevance_score": 0.8,
                        "reason": "Required for visa applications"
                    },
                    {
                        "name": "Employment Services",
                        "description": "Work permit and employment services",
                        "relevance_score": 0.7,
                        "reason": "Often related to work visas"
                    },
                    {
                        "name": "Residence Services",
                        "description": "Residence permit and registration",
                        "relevance_score": 0.6,
                        "reason": "Related to long-term stays"
                    }
                ],
                "business registration": [
                    {
                        "name": "Tax Registration",
                        "description": "Tax registration and filing services",
                        "relevance_score": 0.9,
                        "reason": "Required after business registration"
                    },
                    {
                        "name": "Employment Services",
                        "description": "Work permit and employment services",
                        "relevance_score": 0.7,
                        "reason": "Needed for hiring employees"
                    },
                    {
                        "name": "Business Licensing",
                        "description": "Additional business licenses and permits",
                        "relevance_score": 0.8,
                        "reason": "Complementary to business registration"
                    }
                ]
            }

            # Get conversation context for additional context
            with DataService() as data_service:
                conversation_context = data_service.get_conversation_context(user_session_id)

            # Find related services
            current_service_lower = current_service.lower()
            related_services = []

            # Check for exact matches
            for service_name, related_list in service_relationships.items():
                if service_name in current_service_lower:
                    related_services.extend(related_list)
                    break

            # If no exact match, check for partial matches
            if not related_services:
                for service_name, related_list in service_relationships.items():
                    if any(word in current_service_lower for word in service_name.split()):
                        related_services.extend(related_list)
                        break

            # If still no matches, return some general suggestions
            if not related_services:
                related_services = [
                    {
                        "name": "Hong Kong Passport Services",
                        "description": "Passport application and renewal services",
                        "relevance_score": 0.5,
                        "reason": "Common government service"
                    },
                    {
                        "name": "Hong Kong Visa Services",
                        "description": "Visa application and extension services",
                        "relevance_score": 0.4,
                        "reason": "Common government service"
                    },
                    {
                        "name": "Business Registration",
                        "description": "Business registration and licensing",
                        "relevance_score": 0.3,
                        "reason": "Common government service"
                    }
                ]

            # Sort by relevance score
            related_services.sort(key=lambda x: x["relevance_score"], reverse=True)

            logger.info(f"Found {len(related_services)} related services for '{current_service}'")
            return related_services

        except Exception as e:
            logger.error(f"Failed to get related services: {e}")
            return []
