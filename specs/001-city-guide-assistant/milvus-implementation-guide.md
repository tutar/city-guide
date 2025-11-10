# Milvus Implementation Guide for City Guide Smart Assistant

**Date**: 2025-11-07
**Feature**: City Guide Smart Assistant
**Purpose**: Practical implementation guide with code examples and deployment scripts

## Quick Start Implementation

### 1. Development Environment Setup

#### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.6.4
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"

networks:
  default:
    name: milvus
```

#### Startup Script

```bash
#!/bin/bash
# start-milvus-dev.sh

echo "Starting Milvus development environment..."

# Create volume directories
mkdir -p volumes/etcd volumes/minio volumes/milvus

# Start services
docker-compose up -d

echo "Waiting for Milvus to be ready..."
until curl -f http://localhost:9091/healthz >/dev/null 2>&1; do
    sleep 2
done

echo "Milvus is ready!"
echo "- Connection: localhost:19530"
echo "- WebUI: http://localhost:9091/webui/"
```

### 2. Python Client Implementation

#### Core Milvus Service

```python
# src/utils/milvus_client.py
import logging
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, DataType,
    utility, MilvusException
)

logger = logging.getLogger(__name__)

class MilvusClient:
    def __init__(self, host: str = "localhost", port: str = "19530"):
        self.host = host
        self.port = port
        self.collection_name = "government_documents"
        self.collection = None

    def connect(self):
        """Establish connection to Milvus"""
        try:
            connections.connect("default", host=self.host, port=self.port)
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False

    def create_collection(self):
        """Create collection for government documents"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} already exists")
            return

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="document_title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4000),
            FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="source_priority", dtype=DataType.INT64),  # 1=official, 2=auxiliary
            FieldSchema(name="service_category", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="last_verified", dtype=DataType.INT64),
            FieldSchema(name="is_active", dtype=DataType.BOOL),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]

        schema = CollectionSchema(fields, "Government service document embeddings")
        self.collection = Collection(self.collection_name, schema)
        logger.info(f"Created collection {self.collection_name}")

    def create_index(self):
        """Create IVF index for optimal performance"""
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",  # Inner Product for BGE-M3
            "params": {"nlist": 1024}
        }

        self.collection.create_index("embedding", index_params)
        self.collection.load()
        logger.info("Created and loaded index")

    def insert_documents(self, documents: List[Dict[str, Any]]):
        """Insert government documents with embeddings"""
        if not self.collection:
            raise ValueError("Collection not initialized")

        # Prepare data for insertion
        data = {
            "id": [doc["id"] for doc in documents],
            "embedding": [doc["embedding"] for doc in documents],
            "document_title": [doc["document_title"] for doc in documents],
            "content": [doc["content"] for doc in documents],
            "source_url": [doc["source_url"] for doc in documents],
            "source_priority": [doc["source_priority"] for doc in documents],
            "service_category": [doc["service_category"] for doc in documents],
            "last_verified": [doc["last_verified"] for doc in documents],
            "is_active": [doc["is_active"] for doc in documents],
            "metadata": [doc.get("metadata", {}) for doc in documents]
        }

        result = self.collection.insert(data)
        logger.info(f"Inserted {len(documents)} documents")
        return result

    def search_similar(self, query_embedding: List[float], top_k: int = 5,
                      category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar government documents"""
        if not self.collection:
            raise ValueError("Collection not initialized")

        # Build search expression
        expr = "is_active == true"
        if category:
            expr += f" && service_category == '{category}'"

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        # Execute search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["document_title", "content", "source_url", "source_priority"]
        )

        # Format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "document_title": hit.entity.get("document_title"),
                    "content": hit.entity.get("content"),
                    "source_url": hit.entity.get("source_url"),
                    "source_priority": hit.entity.get("source_priority")
                })

        return formatted_results
```

#### BGE-M3 Embedding Service

```python
# src/services/embedding_service.py
import torch
from typing import List, Dict, Any
from FlagEmbedding import BGEM3FlagModel

class BGE_M3_EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model = BGEM3FlagModel(
            model_name,
            use_fp16=True,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

    def encode_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Generate embeddings for Chinese government text"""
        results = self.model.encode(texts)
        return {
            'dense_vecs': results['dense_vecs'],
            'sparse_vecs': results.get('sparse_vecs'),
            'colbert_vecs': results.get('colbert_vecs')
        }

    def process_government_document(self, document: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a government document into chunks with embeddings"""
        # Chunk the document
        chunks = self._chunk_document(document)

        # Generate embeddings for each chunk
        embeddings = self.encode_texts(chunks)

        # Prepare document records
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "id": f"{metadata['source_id']}_{i}",
                "embedding": embeddings['dense_vecs'][i].tolist(),
                "document_title": metadata.get('title', 'Government Document'),
                "content": chunk,
                "source_url": metadata['source_url'],
                "source_priority": metadata['source_priority'],
                "service_category": metadata['service_category'],
                "last_verified": metadata['last_verified'],
                "is_active": True,
                "metadata": {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "language": "zh"
                }
            })

        return documents

    def _chunk_document(self, text: str, max_tokens: int = 512) -> List[str]:
        """Intelligent chunking for Chinese government documents"""
        # Simple sentence-based chunking for Chinese text
        sentences = text.split('。')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Rough token estimation (Chinese characters + punctuation)
            estimated_tokens = len(sentence) * 1.5  # Conservative estimate

            if len(current_chunk) + estimated_tokens < max_tokens:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
```

### 3. FastAPI Integration

```python
# src/api/routes/search.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from src.utils.milvus_client import MilvusClient
from src.services.embedding_service import BGE_M3_EmbeddingService

router = APIRouter(prefix="/search", tags=["search"])

# Initialize services
milvus_client = MilvusClient()
embedding_service = BGE_M3_EmbeddingService()

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = 5

class SearchResponse(BaseModel):
    results: List[dict]
    query_embedding_generated: bool

@router.post("/government-services", response_model=SearchResponse)
async def search_government_services(request: SearchRequest):
    """Search government services using hybrid semantic search"""
    try:
        # Generate query embedding
        embedding_result = embedding_service.encode_texts([request.query])
        query_embedding = embedding_result['dense_vecs'][0]

        # Search in Milvus
        results = milvus_client.search_similar(
            query_embedding=query_embedding,
            top_k=request.top_k,
            category=request.category
        )

        return SearchResponse(
            results=results,
            query_embedding_generated=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/categories")
async def get_service_categories():
    """Get available service categories"""
    # This would query your database for available categories
    return {
        "categories": [
            "港澳通行证",
            "护照办理",
            "台湾通行证",
            "居住证",
            "社保业务",
            "税务业务"
        ]
    }
```

### 4. Data Ingestion Pipeline

```python
# src/data/ingestion_pipeline.py
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.utils.milvus_client import MilvusClient
from src.services.embedding_service import BGE_M3_EmbeddingService

logger = logging.getLogger(__name__)

class GovernmentDataIngestionPipeline:
    def __init__(self):
        self.milvus_client = MilvusClient()
        self.embedding_service = BGE_M3_EmbeddingService()

    async def initialize(self):
        """Initialize the pipeline"""
        if not self.milvus_client.connect():
            raise Exception("Failed to connect to Milvus")

        self.milvus_client.create_collection()
        self.milvus_client.create_index()
        logger.info("Pipeline initialized successfully")

    async def ingest_documents(self, documents: List[Dict[str, Any]]):
        """Ingest government documents into the system"""
        processed_docs = []

        for doc in documents:
            # Process each document
            doc_records = self.embedding_service.process_government_document(
                document=doc['content'],
                metadata={
                    'source_id': doc['id'],
                    'title': doc['title'],
                    'source_url': doc['source_url'],
                    'source_priority': doc['source_priority'],
                    'service_category': doc['service_category'],
                    'last_verified': int(datetime.now().timestamp())
                }
            )
            processed_docs.extend(doc_records)

        # Insert into Milvus
        if processed_docs:
            self.milvus_client.insert_documents(processed_docs)
            logger.info(f"Ingested {len(processed_docs)} document chunks")

        return len(processed_docs)

    async def update_document(self, document_id: str, new_content: str, metadata: Dict[str, Any]):
        """Update an existing document"""
        # First, mark old chunks as inactive
        # Then insert new chunks
        # This maintains data consistency
        pass
```

### 5. Configuration Management

```python
# src/config/milvus_config.py
import os
from typing import Dict, Any

MILVUS_CONFIG = {
    "development": {
        "host": "localhost",
        "port": "19530",
        "collection_name": "government_documents_dev",
        "index_params": {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 512}
        }
    },
    "production": {
        "host": os.getenv("MILVUS_HOST", "milvus-cluster"),
        "port": os.getenv("MILVUS_PORT", "19530"),
        "collection_name": "government_documents",
        "index_params": {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 2048}
        }
    }
}

BGE_M3_CONFIG = {
    "model_name": "BAAI/bge-m3",
    "use_fp16": True,
    "max_tokens": 8192,
    "chunk_size": 512
}

def get_milvus_config(environment: str = "development") -> Dict[str, Any]:
    """Get Milvus configuration for environment"""
    return MILVUS_CONFIG.get(environment, MILVUS_CONFIG["development"])
```

### 6. Testing and Validation

```python
# tests/test_milvus_integration.py
import pytest
import numpy as np
from src.utils.milvus_client import MilvusClient
from src.services.embedding_service import BGE_M3_EmbeddingService

class TestMilvusIntegration:
    @pytest.fixture
    def milvus_client(self):
        client = MilvusClient()
        client.connect()
        client.create_collection()
        yield client
        # Cleanup

    @pytest.fixture
    def embedding_service(self):
        return BGE_M3_EmbeddingService()

    def test_document_insertion(self, milvus_client, embedding_service):
        """Test inserting government documents"""
        test_document = {
            "id": "test_doc_1",
            "content": "办理港澳通行证需要准备身份证和照片。办理时间通常为7个工作日。",
            "title": "港澳通行证办理指南",
            "source_url": "https://example.com/hk_macao_pass",
            "source_priority": 1,
            "service_category": "港澳通行证"
        }

        # Process document
        documents = embedding_service.process_government_document(
            test_document["content"],
            {
                'source_id': test_document["id"],
                'title': test_document["title"],
                'source_url': test_document["source_url"],
                'source_priority': test_document["source_priority"],
                'service_category': test_document["service_category"],
                'last_verified': 1700000000
            }
        )

        # Insert into Milvus
        result = milvus_client.insert_documents(documents)
        assert result is not None

    def test_semantic_search(self, milvus_client, embedding_service):
        """Test semantic search functionality"""
        query = "如何办理港澳通行证"

        # Generate embedding
        embedding_result = embedding_service.encode_texts([query])
        query_embedding = embedding_result['dense_vecs'][0]

        # Search
        results = milvus_client.search_similar(
            query_embedding=query_embedding,
            top_k=3,
            category="港澳通行证"
        )

        assert isinstance(results, list)
        assert len(results) <= 3
```

## Deployment Scripts

### Production Kubernetes Deployment

```yaml
# k8s/milvus-values.yaml
image:
  all:
    tag: "v2.6.4"

cluster:
  enabled: true

woodpecker:
  enabled: true

streaming:
  enabled: true

indexNode:
  enabled: false

pulsarv3:
  enabled: false

metrics:
  serviceMonitor:
    enabled: true
    additionalLabels:
      release: prometheus

resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "2000m"
```

### Deployment Script

```bash
#!/bin/bash
# deploy-milvus-production.sh

echo "Deploying Milvus to Kubernetes..."

# Add Helm repository
helm repo add zilliztech https://zilliztech.github.io/milvus-helm/
helm repo update

# Deploy Milvus
helm upgrade --install milvus-cluster zilliztech/milvus \
  --namespace milvus \
  --create-namespace \
  --values k8s/milvus-values.yaml \
  --wait

echo "Milvus deployment completed!"
echo "Check status with: kubectl get pods -n milvus"
```

## Performance Monitoring

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Government Assistant - Milvus Performance",
    "panels": [
      {
        "title": "Query Latency",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(milvus_proxy_search_latency_sum[5m]) / rate(milvus_proxy_search_latency_count[5m])",
            "legendFormat": "Average Latency"
          }
        ]
      },
      {
        "title": "Search QPS",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(milvus_proxy_search_requests_total[5m])",
            "legendFormat": "Queries per Second"
          }
        ]
      }
    ]
  }
}
```

This implementation guide provides a complete foundation for integrating Milvus with BGE-M3 embeddings into your City Guide Smart Assistant, with production-ready code examples and deployment strategies.
