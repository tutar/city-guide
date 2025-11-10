#!/usr/bin/env python3
"""
Force recreate vector index with COSINE metric type
"""

import logging
from src.services.embedding_service import EmbeddingService
from pymilvus import utility

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def force_recreate_index():
    """Force recreate vector index with COSINE metric type"""
    try:
        embedding_service = EmbeddingService()

        # Get current index info
        print("Current index information:")
        try:
            index_info = embedding_service.collection.index()
            print(f"  Index name: {index_info.index_name}")
            print(f"  Index type: {index_info.params.get('index_type', 'unknown')}")
            print(f"  Metric type: {index_info.params.get('metric_type', 'unknown')}")
        except Exception as e:
            print(f"  Failed to get index info: {e}")

        # Drop existing index
        print("\nDropping existing index...")
        try:
            embedding_service.collection.drop_index()
            print("  Index dropped successfully")
        except Exception as e:
            print(f"  Failed to drop index: {e}")

        # Create new index with COSINE
        print("\nCreating new index with COSINE metric type...")
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 1024},
        }

        embedding_service.collection.create_index("embedding_vector", index_params)
        print("  New index created successfully")

        # Verify new index
        print("\nVerifying new index...")
        index_info = embedding_service.collection.index()
        print(f"  Index name: {index_info.index_name}")
        print(f"  Index type: {index_info.params.get('index_type', 'unknown')}")
        print(f"  Metric type: {index_info.params.get('metric_type', 'unknown')}")

        # Load collection
        print("\nLoading collection...")
        embedding_service.collection.load()
        print("  Collection loaded successfully")

        return {
            "status": "success",
            "index_type": index_info.params.get("index_type"),
            "metric_type": index_info.params.get("metric_type"),
        }

    except Exception as e:
        logger.error(f"Failed to recreate index: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Force recreating vector index with COSINE metric type...")
    result = force_recreate_index()

    if result["status"] == "success":
        print(f"\nIndex recreation completed successfully!")
        print(f"Index type: {result['index_type']}")
        print(f"Metric type: {result['metric_type']}")
    else:
        print(f"\nFailed to recreate index: {result['error']}")
