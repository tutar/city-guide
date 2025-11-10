#!/usr/bin/env python3
"""
Check the vector database index configuration
"""

import logging
from src.services.embedding_service import EmbeddingService
from pymilvus import utility

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_vector_index():
    """Check vector database index configuration"""
    try:
        embedding_service = EmbeddingService()

        # Get collection stats
        stats = embedding_service.get_collection_stats()
        print(f"Collection stats: {stats}")

        # Get index information
        index_info = embedding_service.collection.index()
        print(f"\nIndex information:")
        print(f"  Index name: {index_info.index_name}")
        print(f"  Index type: {index_info.params.get('index_type', 'unknown')}")
        print(f"  Metric type: {index_info.params.get('metric_type', 'unknown')}")
        print(f"  Index params: {index_info.params}")

        # Check if collection is loaded
        print(f"\nCollection loaded: {embedding_service.collection.is_loaded}")

        return {
            "collection_stats": stats,
            "index_info": {
                "index_type": index_info.params.get("index_type"),
                "metric_type": index_info.params.get("metric_type"),
                "params": index_info.params,
            },
        }

    except Exception as e:
        logger.error(f"Failed to check vector index: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Checking vector database index configuration...")
    result = check_vector_index()

    if "error" not in result:
        print(f"\nIndex check completed successfully!")
        print(f"Metric type: {result['index_info']['metric_type']}")
    else:
        print(f"\nFailed to check index: {result['error']}")
