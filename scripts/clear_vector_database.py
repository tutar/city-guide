#!/usr/bin/env python3
"""
Clear the vector database collection for document embeddings
"""

import logging
from src.services.embedding_service import EmbeddingService
from pymilvus import utility

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_vector_database():
    """Clear the document embeddings collection"""
    try:
        embedding_service = EmbeddingService()

        # Get collection stats before clearing
        stats_before = embedding_service.get_collection_stats()
        logger.info(f"Collection stats before clearing: {stats_before}")

        # Drop the collection
        collection_name = embedding_service.collection_name
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            logger.info(f"Successfully dropped collection: {collection_name}")
        else:
            logger.info(f"Collection {collection_name} does not exist")

        # Recreate the collection
        embedding_service._setup_collection()

        # Get collection stats after clearing
        stats_after = embedding_service.get_collection_stats()
        logger.info(f"Collection stats after clearing: {stats_after}")

        return {
            "collection_name": collection_name,
            "documents_before": stats_before.get("num_entities", 0),
            "documents_after": stats_after.get("num_entities", 0),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Failed to clear vector database: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Starting vector database clearing...")
    result = clear_vector_database()

    if result["status"] == "success":
        print(f"\nVector database cleared successfully!")
        print(f"Documents before: {result['documents_before']}")
        print(f"Documents after: {result['documents_after']}")
    else:
        print(f"\nFailed to clear vector database: {result['error']}")
