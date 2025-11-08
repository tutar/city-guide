"""
Embedding service for City Guide Smart Assistant using Milvus vector database
"""

import logging
import uuid
from datetime import datetime
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

        except Exception as e:
            logger.error(f"Failed to setup collection: {e}")
            raise

    def _create_collection(self):
        """Create the document embeddings collection"""
        try:
            # Define schema
            fields = [
                FieldSchema(
                    name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36
                ),
                FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(
                    name="document_url", dtype=DataType.VARCHAR, max_length=500
                ),
                FieldSchema(
                    name="document_title", dtype=DataType.VARCHAR, max_length=500
                ),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(
                    name="embedding_vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.embedding_dimension,
                ),
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
                "metric_type": "L2",
                "params": {"nlist": 1024},
            }
            self.collection.create_index("embedding_vector", index_params)

            logger.info(f"Created collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def store_document_embedding(self, document_embedding: DocumentEmbedding) -> str:
        """Store a document embedding in Milvus"""
        try:
            # Prepare data for insertion
            data = [
                [str(document_embedding.id)],  # id
                [str(document_embedding.source_id)],  # source_id
                [document_embedding.document_url],  # document_url
                [document_embedding.document_title],  # document_title
                [document_embedding.chunk_index],  # chunk_index
                [document_embedding.embedding_vector],  # embedding_vector
                [document_embedding.embedding_model],  # embedding_model
                [int(datetime.utcnow().timestamp())],  # created_at
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
            # Load collection for search
            self.collection.load()

            # Search parameters
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

            # Execute search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding_vector",
                param=search_params,
                limit=limit,
                expr=filter_expression,
                output_fields=[
                    "id",
                    "source_id",
                    "document_url",
                    "document_title",
                    "chunk_index",
                ],
            )

            # Format results
            search_results = []
            for hit in results[0]:
                result = {
                    "document_id": uuid.UUID(hit.entity.get("id")),
                    "source_id": uuid.UUID(hit.entity.get("source_id")),
                    "document_url": hit.entity.get("document_url"),
                    "document_title": hit.entity.get("document_title"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "similarity_score": 1
                    - hit.distance,  # Convert distance to similarity
                    "metadata": {},
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
            self.collection.load()

            # Query by primary key
            result = self.collection.query(
                expr=f"id == '{document_id}'",
                output_fields=[
                    "id",
                    "source_id",
                    "document_url",
                    "document_title",
                    "chunk_index",
                    "embedding_model",
                    "created_at",
                ],
            )

            if result:
                document = result[0]
                return {
                    "id": uuid.UUID(document["id"]),
                    "source_id": uuid.UUID(document["source_id"]),
                    "document_url": document["document_url"],
                    "document_title": document["document_title"],
                    "chunk_index": document["chunk_index"],
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
                "collection_name": stats.collection_name,
                "num_entities": num_entities,
                "description": stats.description,
                "fields": [field.name for field in stats.fields],
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
                    "metric_type": "L2",
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
                [int(datetime.utcnow().timestamp())],  # created_at
            ]

            # Insert into collection
            self.search_query_collection.insert(data)
            self.search_query_collection.flush()

            logger.info(f"Stored search query: {search_query.id}")
            return str(search_query.id)

        except Exception as e:
            logger.error(f"Failed to store search query: {e}")
            raise
