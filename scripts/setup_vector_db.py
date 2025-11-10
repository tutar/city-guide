#!/usr/bin/env python3
"""
Vector database setup script for City Guide Smart Assistant
"""

import logging

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from src.utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_to_milvus():
    """Connect to Milvus vector database"""
    try:
        connections.connect(
            alias="default",
            host=settings.milvus.host,
            port=settings.milvus.port,
        )
        logger.info(
            f"Connected to Milvus at {settings.milvus.host}:{settings.milvus.port}"
        )
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise


def create_collection():
    """Create document embeddings collection"""
    collection_name = settings.milvus.collection

    # Check if collection already exists
    if utility.has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists")
        return Collection(collection_name)

    # Define collection schema
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
        FieldSchema(name="service_category_id", dtype=DataType.VARCHAR, max_length=36),
        FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(
        fields, description="Document embeddings for city guide services"
    )

    # Create collection
    collection = Collection(name=collection_name, schema=schema)

    # Create index for vector search
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128},
    }

    collection.create_index("embedding", index_params)
    logger.info(f"Created collection '{collection_name}' with vector index")

    return collection


def create_partitions(collection: Collection):
    """Create partitions for different document types"""
    partitions = ["requirements", "procedures", "locations", "faqs"]

    for partition_name in partitions:
        if not collection.has_partition(partition_name):
            collection.create_partition(partition_name)
            logger.info(f"Created partition '{partition_name}'")
        else:
            logger.info(f"Partition '{partition_name}' already exists")


def main():
    """Main setup function"""
    logger.info("Starting vector database setup...")

    try:
        connect_to_milvus()
        collection = create_collection()
        create_partitions(collection)

        logger.info("Vector database setup completed successfully")

    except Exception as e:
        logger.error(f"Vector database setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
