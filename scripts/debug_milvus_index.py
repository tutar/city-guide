#!/usr/bin/env python3
"""
Debug Milvus index configuration
"""

import logging
from pymilvus import connections, utility
from src.utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_milvus_index():
    """Debug Milvus index configuration"""
    try:
        # Connect to Milvus
        connections.connect(
            alias="default", host=settings.milvus.host, port=settings.milvus.port
        )

        collection_name = settings.milvus.collection
        print(f"Collection: {collection_name}")

        # Check if collection exists
        if not utility.has_collection(collection_name):
            print(f"Collection {collection_name} does not exist")
            return

        # Get collection info
        from pymilvus import Collection

        collection = Collection(collection_name)

        # Get detailed index info
        print("\n=== Collection Information ===")
        print(f"Collection name: {collection_name}")
        print(f"Number of entities: {collection.num_entities}")

        # Get schema
        schema = collection.schema
        print(f"\n=== Schema ===")
        for field in schema.fields:
            print(
                f"  Field: {field.name}, Type: {field.dtype}, Is Primary: {field.is_primary}"
            )

        # Get index info
        print(f"\n=== Index Information ===")
        try:
            index_info = collection.index()
            print(f"Index name: {index_info.index_name}")
            print(f"Index type: {index_info.params.get('index_type', 'unknown')}")
            print(f"Metric type: {index_info.params.get('metric_type', 'unknown')}")
            print(f"All params: {index_info.params}")
        except Exception as e:
            print(f"Failed to get index info: {e}")

        # Get collection description
        print(f"\n=== Collection Description ===")
        description = collection.describe()
        print(f"Description: {description}")

        # List all collections
        print(f"\n=== All Collections ===")
        collections = utility.list_collections()
        for col in collections:
            print(f"  - {col}")

        # Test search with different metric types
        print(f"\n=== Testing Search Behavior ===")

        # Load collection
        collection.load()

        # Create a simple test embedding
        test_embedding = [0.1] * 1024  # Simple test vector

        # Search with current index
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[test_embedding],
            anns_field="embedding_vector",
            param=search_params,
            limit=3,
            output_fields=["document_title"],
        )

        if results:
            print(f"Search returned {len(results[0])} results")
            for i, hit in enumerate(results[0]):
                title = hit.entity.get("document_title", "Unknown")
                print(f"  {i+1}. {title} (distance: {hit.distance})")

        return {
            "status": "success",
            "collection_name": collection_name,
            "num_entities": collection.num_entities,
        }

    except Exception as e:
        logger.error(f"Failed to debug Milvus index: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Debugging Milvus index configuration...")
    result = debug_milvus_index()

    if result["status"] == "success":
        print(f"\nDebug completed successfully!")
        print(f"Collection: {result['collection_name']}")
        print(f"Entities: {result['num_entities']}")
    else:
        print(f"\nDebug failed: {result['error']}")
