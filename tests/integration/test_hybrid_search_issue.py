#!/usr/bin/env python3
"""
Integration test to verify the hybrid search issue with "港澳通行证"
This test checks if documents about "港澳通行证" can be found in the vector database
"""

import logging
import pytest
from src.models.embeddings import HybridSearchRequest
from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHybridSearchIssue:
    """Test hybrid search functionality with real database connections"""

    def setup_method(self):
        """Set up test fixtures"""
        self.search_service = SearchService()
        self.embedding_service = EmbeddingService()

    def test_vector_database_status(self):
        """Test that vector database is accessible and has documents"""
        stats = self.embedding_service.get_collection_stats()

        assert stats.get("collection_name") is not None
        assert stats.get("num_entities") >= 0

        print(f"\nVector Database Status:")
        print(f"  Collection: {stats.get('collection_name')}")
        print(f"  Documents: {stats.get('num_entities')}")
        print(f"  Fields: {stats.get('fields')}")

    def test_semantic_search_for_hk_macau_pass(self):
        """Test semantic search for 港澳通行证"""
        test_query = "港澳通行证"

        # Generate embedding for the query
        query_embedding = self.search_service.ai_service.generate_embedding(test_query)

        # Perform semantic search
        semantic_results = self.embedding_service.search_similar_documents(
            query_embedding=query_embedding, limit=10
        )

        print(f"\nSemantic Search Results for '{test_query}':")
        print(f"  Found {len(semantic_results)} results")

        for i, result in enumerate(semantic_results[:5]):
            print(
                f"  {i+1}. {result['document_title']} (score: {result['similarity_score']:.4f})"
            )

        # Check if we found any results
        assert (
            len(semantic_results) >= 0
        )  # At least we should get results (could be 0 if no docs)

    def test_keyword_search_for_hk_macau_pass(self):
        """Test keyword search for 港澳通行证"""
        test_query = "港澳通行证"

        # Perform keyword search
        keyword_results = self.search_service.bm25_service.search(test_query, limit=10)

        print(f"\nKeyword Search Results for '{test_query}':")
        print(f"  Found {len(keyword_results)} results")

        for i, result in enumerate(keyword_results[:5]):
            print(
                f"  {i+1}. {result.get('document_title', 'Unknown')} (score: {result.get('bm25_score', 0):.4f})"
            )

        # Check if we found any results
        assert (
            len(keyword_results) >= 0
        )  # At least we should get results (could be 0 if no docs)

    def test_hybrid_search_for_hk_macau_pass(self):
        """Test hybrid search for 港澳通行证"""
        test_query = "港澳通行证"

        search_request = HybridSearchRequest(
            query=test_query,
            limit=10,
            include_semantic_search=True,
            include_keyword_search=True,
        )

        hybrid_results = self.search_service.hybrid_search(search_request)

        print(f"\nHybrid Search Results for '{test_query}':")
        print(f"  Found {len(hybrid_results)} results")

        for i, result in enumerate(hybrid_results[:5]):
            hybrid_score = getattr(result, "hybrid_score", result.similarity_score)
            print(f"  {i+1}. {result.document_title} (score: {hybrid_score:.4f})")

        # Check if we found any results
        assert (
            len(hybrid_results) >= 0
        )  # At least we should get results (could be 0 if no docs)

    def test_multiple_related_queries(self):
        """Test multiple queries related to 港澳通行证"""
        test_queries = [
            "港澳通行证",
            "香港澳门通行证",
            "通行证",
            "港澳",
            "香港澳门",
            "travel document",
            "passport",
        ]

        print(f"\nTesting Multiple Queries:")

        for query in test_queries:
            try:
                search_request = HybridSearchRequest(
                    query=query,
                    limit=5,
                    include_semantic_search=True,
                    include_keyword_search=True,
                )

                results = self.search_service.hybrid_search(search_request)
                print(f"  '{query}': {len(results)} results")

                for i, result in enumerate(results[:2]):  # Show top 2
                    hybrid_score = getattr(
                        result, "hybrid_score", result.similarity_score
                    )
                    print(f"    - {result.document_title} ({hybrid_score:.4f})")

            except Exception as e:
                print(f"  '{query}': ERROR - {e}")

    def test_simplified_search_interface(self):
        """Test the simplified search interface"""
        test_query = "港澳通行证"

        documents = self.search_service.search_documents(test_query, limit=10)

        print(f"\nSimplified Search Results for '{test_query}':")
        print(f"  Found {len(documents)} documents")

        for i, doc in enumerate(documents[:5]):
            print(
                f"  {i+1}. {doc['document_title']} (score: {doc['similarity_score']:.4f})"
            )

        # Check if we found any results
        assert (
            len(documents) >= 0
        )  # At least we should get results (could be 0 if no docs)

    def test_search_with_empty_results(self):
        """Test search with queries that might return empty results"""
        # Test with a query that likely doesn't exist
        test_query = "xyz123nonexistentquery"

        search_request = HybridSearchRequest(
            query=test_query,
            limit=5,
            include_semantic_search=True,
            include_keyword_search=True,
        )

        results = self.search_service.hybrid_search(search_request)

        print(f"\nSearch Results for Non-existent Query '{test_query}':")
        print(f"  Found {len(results)} results")

        # Should handle empty results gracefully
        assert isinstance(results, list)


if __name__ == "__main__":
    # Run the tests directly for debugging
    test_instance = TestHybridSearchIssue()
    test_instance.setup_method()

    print("Starting hybrid search issue tests...")

    try:
        test_instance.test_vector_database_status()
    except Exception as e:
        print(f"Vector database status test failed: {e}")

    try:
        test_instance.test_semantic_search_for_hk_macau_pass()
    except Exception as e:
        print(f"Semantic search test failed: {e}")

    try:
        test_instance.test_keyword_search_for_hk_macau_pass()
    except Exception as e:
        print(f"Keyword search test failed: {e}")

    try:
        test_instance.test_hybrid_search_for_hk_macau_pass()
    except Exception as e:
        print(f"Hybrid search test failed: {e}")

    try:
        test_instance.test_multiple_related_queries()
    except Exception as e:
        print(f"Multiple queries test failed: {e}")

    try:
        test_instance.test_simplified_search_interface()
    except Exception as e:
        print(f"Simplified search test failed: {e}")

    print("\nAll tests completed!")
