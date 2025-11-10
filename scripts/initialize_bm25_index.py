#!/usr/bin/env python3
"""
Initialize BM25 index with documents from vector database
"""

import logging
from src.services.bm25_service import BM25Service
from src.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_bm25_index():
    """Initialize BM25 index with documents from vector database"""
    try:
        embedding_service = EmbeddingService()
        bm25_service = BM25Service()

        # Get all documents from vector database
        print("Loading documents from vector database...")

        # We need to get all documents from Milvus
        # For now, let's create a simple query to get all documents
        embedding_service.collection.load()

        # Query all documents (this might be inefficient for large collections)
        results = embedding_service.collection.query(
            expr="",  # Empty expression to get all documents
            limit=1000,  # Set a reasonable limit
            output_fields=["id", "document_title", "document_url", "chunk_index"],
        )

        print(f"Found {len(results)} documents in vector database")

        # Prepare documents for BM25 indexing
        documents_for_bm25 = []
        for doc in results:
            # For BM25, we need document content
            # Since we don't have the full content in Milvus, we'll use title and URL
            # In production, you would need to store document content separately
            document = {
                "id": doc["id"],
                "document_title": doc.get("document_title", "Unknown"),
                "document_content": doc.get(
                    "document_title", ""
                ),  # Use title as content for now
                "source_url": doc.get("document_url", ""),
                "chunk_index": doc.get("chunk_index", 0),
            }
            documents_for_bm25.append(document)

        # Index documents in BM25
        print(f"Indexing {len(documents_for_bm25)} documents in BM25...")
        bm25_service.index_documents(documents_for_bm25)

        # Get BM25 index stats
        stats = bm25_service.get_index_stats()
        print(f"BM25 index initialized successfully!")
        print(f"  Documents: {stats['num_documents']}")
        print(f"  Vocabulary size: {stats['vocabulary_size']}")
        print(f"  Average document length: {stats['avg_document_length']:.2f}")

        # Test search
        print(f"\nTesting BM25 search...")
        test_results = bm25_service.search("港澳通行证", limit=3)
        print(f"  Search for '港澳通行证' returned {len(test_results)} results")

        for i, result in enumerate(test_results):
            print(
                f"    {i+1}. {result.get('document_title', 'Unknown')} (score: {result.get('bm25_score', 0):.4f})"
            )

        return {
            "status": "success",
            "bm25_stats": stats,
            "test_results": len(test_results),
        }

    except Exception as e:
        logger.error(f"Failed to initialize BM25 index: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Initializing BM25 index...")
    result = initialize_bm25_index()

    if result["status"] == "success":
        print(f"\nBM25 index initialization completed successfully!")
        print(f"Test search returned {result['test_results']} results")
    else:
        print(f"\nFailed to initialize BM25 index: {result['error']}")
