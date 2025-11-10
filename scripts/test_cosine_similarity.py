#!/usr/bin/env python3
"""
Test COSINE similarity calculation in vector search
"""

import logging
from src.services.embedding_service import EmbeddingService
from src.services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cosine_similarity():
    """Test COSINE similarity calculation"""
    try:
        embedding_service = EmbeddingService()
        ai_service = AIService()

        # Test queries with different similarity levels
        test_queries = ["港澳通行证", "香港澳门通行证", "通行证", "护照", "身份证", "完全不相关的查询"]

        print("Testing COSINE similarity with different queries:\n")

        for query in test_queries:
            print(f"Query: '{query}'")

            # Generate embedding
            query_embedding = ai_service.generate_embedding(query)

            # Search with COSINE
            results = embedding_service.search_similar_documents(
                query_embedding=query_embedding, limit=3
            )

            print(f"  Found {len(results)} results")

            for i, result in enumerate(results):
                print(
                    f"    {i+1}. {result['document_title']} (similarity: {result['similarity_score']:.4f})"
                )

            print()

        # Test similarity score range
        print("\nAnalyzing similarity score distribution:")
        all_results = []
        for query in ["港澳通行证", "护照"]:
            query_embedding = ai_service.generate_embedding(query)
            results = embedding_service.search_similar_documents(
                query_embedding=query_embedding, limit=10
            )
            all_results.extend(results)

        if all_results:
            scores = [r["similarity_score"] for r in all_results]
            print(f"  Score range: {min(scores):.4f} - {max(scores):.4f}")
            print(f"  Average score: {sum(scores)/len(scores):.4f}")
            print(f"  COSINE similarity should be between 0 and 1")

        return {
            "status": "success",
            "tested_queries": len(test_queries),
            "total_results": len(all_results),
        }

    except Exception as e:
        logger.error(f"Failed to test COSINE similarity: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Testing COSINE similarity calculation...")
    result = test_cosine_similarity()

    if result["status"] == "success":
        print(f"\nCOSINE similarity test completed successfully!")
        print(f"Tested {result['tested_queries']} queries")
        print(f"Total results analyzed: {result['total_results']}")
    else:
        print(f"\nFailed to test COSINE similarity: {result['error']}")
