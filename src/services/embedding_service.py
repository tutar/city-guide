"""
Embedding service for City Guide Smart Assistant using Milvus vector database
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from src.models.document_embeddings import DocumentEmbedding
from src.models.search_queries import SearchQuery
from src.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for managing vector embeddings and semantic search"""

    def __init__(self):
        self.collection_name = settings.milvus.collection
        self.embedding_dimension = settings.ai.embedding_dimension
        self._connect()
        self._setup_collection()

    def _connect(self):
        """Connect to Milvus server"""
        try:
            connections.connect(
                alias="default", host=settings.milvus.host, port=settings.milvus.port
            )
            logger.info(
                f"Connected to Milvus at {settings.milvus.host}:{settings.milvus.port}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _setup_collection(self):
        """Setup or get the document embeddings collection"""
        try:
            if not utility.has_collection(self.collection_name):
                self._create_collection()
            else:
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")

            # Load collection for immediate use
            self.collection.load()
            logger.info(f"Collection loaded: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to setup collection: {e}")
            raise

    def _create_collection(self):
        """Create the document embeddings collection"""
        try:
            # Define schema - Unified design
            fields = [
                # Primary key and identifiers
                FieldSchema(
                    name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36
                ),
                FieldSchema(
                    name="service_category_id", dtype=DataType.VARCHAR, max_length=36
                ),
                FieldSchema(
                    name="document_url", dtype=DataType.VARCHAR, max_length=500
                ),
                FieldSchema(
                    name="document_type", dtype=DataType.VARCHAR, max_length=50
                ),
                # Document content
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                # Vector and indexing
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.embedding_dimension,
                ),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                # Metadata and version control
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(
                    name="embedding_model", dtype=DataType.VARCHAR, max_length=100
                ),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]

            schema = CollectionSchema(
                fields, description="Document embeddings for government services"
            )
            self.collection = Collection(self.collection_name, schema)

            # Create index for vector search
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            }
            self.collection.create_index("embedding", index_params)

            logger.info(f"Created collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def store_document_embedding(self, document_embedding: DocumentEmbedding) -> str:
        """Store a document embedding in Milvus"""
        try:
            # Prepare data for insertion - Unified schema
            data = [
                [str(document_embedding.id)],  # id
                [str(document_embedding.service_category_id)],  # service_category_id
                [document_embedding.metadata.get("source", "")],  # document_url
                [document_embedding.document_type],  # document_type
                [document_embedding.title],  # title
                [document_embedding.content],  # content
                [document_embedding.embedding],  # embedding
                [document_embedding.metadata.get("section_index", 0)],  # chunk_index
                [document_embedding.metadata],  # metadata
                ["Qwen/Qwen3-Embedding-0.6B"],  # embedding_model
                [int(datetime.now(timezone.utc).timestamp())],  # created_at
            ]

            # Insert into collection
            self.collection.insert(data)
            self.collection.flush()

            logger.info(f"Stored document embedding: {document_embedding.id}")
            return str(document_embedding.id)

        except Exception as e:
            logger.error(f"Failed to store document embedding: {e}")
            raise

    def search_similar_documents(
        self,
        query_embedding: list[float],
        limit: int = 10,
        filter_expression: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            # Search parameters
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # Execute search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=filter_expression,
                output_fields=[
                    "id",
                    "service_category_id",
                    "document_url",
                    "document_type",
                    "title",
                    "content",
                    "chunk_index",
                    "metadata",
                ],
            )

            # Format results
            search_results = []
            for hit in results[0]:
                # For COSINE metric_type, distance is negative similarity
                # COSINE similarity ranges from -1 to 1, we need to map to 0-1
                # similarity_score = (1 + (-hit.distance)) / 2
                similarity_score = (1 + (-hit.distance)) / 2

                result = {
                    "document_id": uuid.UUID(hit.entity.get("id")),
                    "service_category_id": uuid.UUID(
                        hit.entity.get("service_category_id")
                    ),
                    "document_url": hit.entity.get("document_url"),
                    "document_type": hit.entity.get("document_type"),
                    "title": hit.entity.get("title"),
                    "content": hit.entity.get("content"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "metadata": hit.entity.get("metadata", {}),
                    "similarity_score": similarity_score,
                }
                search_results.append(result)

            logger.info(f"Found {len(search_results)} similar documents")
            return search_results

        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            raise

    def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Get document embedding by ID"""
        try:
            # Query by primary key
            result = self.collection.query(
                expr=f"id == '{document_id}'",
                output_fields=[
                    "id",
                    "service_category_id",
                    "document_url",
                    "document_type",
                    "title",
                    "content",
                    "chunk_index",
                    "metadata",
                    "embedding_model",
                    "created_at",
                ],
            )

            if result:
                document = result[0]
                return {
                    "id": uuid.UUID(document["id"]),
                    "service_category_id": uuid.UUID(document["service_category_id"]),
                    "document_url": document["document_url"],
                    "document_type": document["document_type"],
                    "title": document["title"],
                    "content": document["content"],
                    "chunk_index": document["chunk_index"],
                    "metadata": document["metadata"],
                    "embedding_model": document["embedding_model"],
                    "created_at": datetime.fromtimestamp(document["created_at"]),
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            raise

    def delete_document_embedding(self, document_id: str) -> bool:
        """Delete a document embedding by ID"""
        try:
            self.collection.delete(expr=f"id in ['{document_id}']")
            self.collection.flush()

            logger.info(f"Deleted document embedding: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document embedding: {e}")
            raise

    def get_collection_stats(self) -> dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = self.collection.describe()
            num_entities = self.collection.num_entities

            return {
                "collection_name": stats.get("collection_name", "unknown"),
                "num_entities": num_entities,
                "description": stats.get("description", ""),
                "fields": [field.get("name", "") for field in stats.get("fields", [])],
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    def create_search_query_collection(self):
        """Create a separate collection for search query analytics"""
        try:
            search_query_collection_name = f"{self.collection_name}_queries"

            if not utility.has_collection(search_query_collection_name):
                # Define schema for search queries
                fields = [
                    FieldSchema(
                        name="id",
                        dtype=DataType.VARCHAR,
                        is_primary=True,
                        max_length=36,
                    ),
                    FieldSchema(
                        name="session_id", dtype=DataType.VARCHAR, max_length=255
                    ),
                    FieldSchema(
                        name="query_text", dtype=DataType.VARCHAR, max_length=1000
                    ),
                    FieldSchema(
                        name="query_embedding",
                        dtype=DataType.FLOAT_VECTOR,
                        dim=self.embedding_dimension,
                    ),
                    FieldSchema(name="response_quality", dtype=DataType.INT64),
                    FieldSchema(name="created_at", dtype=DataType.INT64),
                ]

                schema = CollectionSchema(fields, description="Search query analytics")
                self.search_query_collection = Collection(
                    search_query_collection_name, schema
                )

                # Create index for query embeddings
                index_params = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 1024},
                }
                self.search_query_collection.create_index(
                    "query_embedding", index_params
                )

                logger.info(
                    f"Created search query collection: {search_query_collection_name}"
                )
            else:
                self.search_query_collection = Collection(search_query_collection_name)
                logger.info(
                    f"Using existing search query collection: {search_query_collection_name}"
                )

        except Exception as e:
            logger.error(f"Failed to create search query collection: {e}")
            raise

    def store_search_query(self, search_query: SearchQuery) -> str:
        """Store a search query for analytics"""
        try:
            if not hasattr(self, "search_query_collection"):
                self.create_search_query_collection()

            # Prepare data for insertion
            data = [
                [str(search_query.id)],  # id
                [search_query.session_id],  # session_id
                [search_query.query_text],  # query_text
                [search_query.query_embedding],  # query_embedding
                [
                    search_query.response_quality
                    if search_query.response_quality
                    else -1
                ],  # response_quality
                [int(datetime.now(timezone.utc).timestamp())],  # created_at
            ]

            # Insert into collection
            self.search_query_collection.insert(data)
            self.search_query_collection.flush()

            logger.info(f"Stored search query: {search_query.id}")
            return str(search_query.id)

        except Exception as e:
            logger.error(f"Failed to store search query: {e}")
            raise
