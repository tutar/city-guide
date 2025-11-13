# Milvus 统一设计方案

**日期**: 2025-11-12
**功能**: City Guide Smart Assistant
**目的**: 统一的Milvus向量数据库设计方案，整合实现指南和研究文档

## 1. 统一Schema设计

### 核心字段定义

```python
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

# 统一字段定义
fields = [
    # 主键和标识
    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
    FieldSchema(name="service_category_id", dtype=DataType.VARCHAR, max_length=36),
    FieldSchema(name="document_url", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=50),

    # 文档内容
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),

    # 向量和索引
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dimension),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),

    # 元数据和版本控制
    FieldSchema(name="metadata", dtype=DataType.JSON),
    FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="created_at", dtype=DataType.INT64),
]
```

### Metadata结构定义

```python
# 标准metadata结构
metadata = {
    "total_chunks": 5,           # 文档总chunk数
    "language": "zh",            # 文档语言
    "section_type": "procedure",  # 段落类型
    "source_priority": 1,        # 来源优先级 (1=官方, 2=辅助)
    "last_verified": 1700000000, # 最后验证时间戳
    "is_active": True,           # 是否活跃
    "service_category": "港澳通行证",  # 服务类别
    "chunk_characteristics": {   # chunk特征
        "word_count": 150,
        "sentence_count": 3,
        "has_tables": False
    }
}
```

## 2. 设计原则

### 字段统一原则

1. **主键标准化**: 使用36字符UUID格式
2. **服务分类**: `service_category_id` 替代 `service_category`
3. **文档来源**: `document_url` 替代 `source_url`
4. **分块管理**: `chunk_index` 作为独立字段，metadata中维护`total_chunks`
5. **版本控制**: `embedding_model` 记录使用的嵌入模型

### 数据组织策略

```python
# 文档分块示例
{
    "id": "doc_123_chunk_0",
    "service_category_id": "hk_macao_pass",
    "document_url": "https://example.com/hk_macao_pass",
    "document_type": "procedure",
    "title": "港澳通行证办理指南",
    "content": "办理港澳通行证需要准备身份证和照片...",
    "embedding": [0.1, 0.2, 0.3, ...],  # 1024维向量
    "chunk_index": 0,
    "metadata": {
        "total_chunks": 3,
        "language": "zh",
        "section_type": "requirements",
        "source_priority": 1,
        "last_verified": 1700000000,
        "is_active": True,
        "service_category": "港澳通行证",
        "chunk_characteristics": {
            "word_count": 120,
            "sentence_count": 2,
            "has_tables": False
        }
    },
    "embedding_model": "BAAI/bge-m3",
    "created_at": 1700000000
}
```

## 3. 集合创建和索引

### 集合创建脚本

```python
# scripts/setup_vector_db.py
import logging
from pymilvus import (
    Collection, CollectionSchema, DataType, FieldSchema,
    connections, utility
)
from src.utils.config import settings

logger = logging.getLogger(__name__)

def connect_to_milvus():
    """连接Milvus向量数据库"""
    try:
        connections.connect(
            alias="default",
            host=settings.milvus.host,
            port=settings.milvus.port,
        )
        logger.info(f"Connected to Milvus at {settings.milvus.host}:{settings.milvus.port}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise

def create_collection():
    """创建文档嵌入集合"""
    collection_name = settings.milvus.collection
    embedding_dimension = settings.ai.embedding_dimension

    # 检查集合是否已存在
    if utility.has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists")
        return Collection(collection_name)

    # 定义统一schema
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
        FieldSchema(name="service_category_id", dtype=DataType.VARCHAR, max_length=36),
        FieldSchema(name="document_url", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dimension),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(
        fields, description="政府服务文档嵌入向量"
    )

    # 创建集合
    collection = Collection(name=collection_name, schema=schema)

    # 创建向量索引
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128},
    }

    collection.create_index("embedding", index_params)
    logger.info(f"Created collection '{collection_name}' with vector index")

    return collection
```

### 索引策略

```python
# 向量索引配置
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 128},
}

# 可选：为chunk_index创建索引以提高查询性能
collection.create_index(
    "chunk_index",
    {
        "index_type": "STL_SORT",
        "metric_type": "L2"
    }
)
```

## 4. 数据插入和查询

### 文档处理流程

```python
class DocumentProcessor:
    def __init__(self):
        self.embedding_service = BGE_M3_EmbeddingService()

    def process_document(self, document: str, metadata: dict) -> List[Dict]:
        """处理文档并生成向量记录"""
        # 文档分块
        chunks = self._chunk_document(document)

        # 生成嵌入向量
        embeddings = self.embedding_service.encode_texts(chunks)

        # 准备记录
        records = []
        for i, chunk in enumerate(chunks):
            record = {
                "id": f"{metadata['source_id']}_{i}",
                "service_category_id": metadata['service_category_id'],
                "document_url": metadata['document_url'],
                "document_type": metadata['document_type'],
                "title": metadata['title'],
                "content": chunk,
                "embedding": embeddings['dense_vecs'][i].tolist(),
                "chunk_index": i,
                "metadata": {
                    "total_chunks": len(chunks),
                    "language": metadata.get('language', 'zh'),
                    "section_type": metadata.get('section_type', 'general'),
                    "source_priority": metadata.get('source_priority', 2),
                    "last_verified": int(datetime.now().timestamp()),
                    "is_active": True,
                    "service_category": metadata.get('service_category', ''),
                    "chunk_characteristics": self._analyze_chunk(chunk)
                },
                "embedding_model": "BAAI/bge-m3",
                "created_at": int(datetime.now().timestamp())
            }
            records.append(record)

        return records
```

### 查询优化

```python
class VectorSearchService:
    def __init__(self, collection):
        self.collection = collection

    def search_with_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """带上下文的向量搜索"""
        # 生成查询向量
        query_embedding = self.embedding_service.encode_texts([query])['dense_vecs'][0]

        # 搜索参数
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        # 执行搜索
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k * 3,  # 获取更多结果用于上下文重组
            output_fields=["id", "title", "content", "chunk_index", "metadata"]
        )

        # 按文档重组结果
        grouped_results = self._group_by_document(results)

        # 选择每个文档的最佳chunk
        final_results = self._select_best_chunks(grouped_results, top_k)

        return final_results

    def _group_by_document(self, results):
        """按文档分组结果"""
        grouped = {}
        for hits in results:
            for hit in hits:
                doc_id = hit.id.rsplit('_', 1)[0]  # 提取文档ID
                if doc_id not in grouped:
                    grouped[doc_id] = []
                grouped[doc_id].append({
                    'chunk_index': hit.entity.get('chunk_index'),
                    'score': hit.score,
                    'content': hit.entity.get('content'),
                    'metadata': hit.entity.get('metadata')
                })

        # 按chunk_index排序
        for doc_id, chunks in grouped.items():
            chunks.sort(key=lambda x: x['chunk_index'])

        return grouped
```

## 5. 部署和维护

### 开发环境部署

```bash
# 使用Docker Compose启动开发环境
docker-compose up -d

# 运行集合设置脚本
python scripts/setup_vector_db.py
```

### 生产环境配置

```yaml
# k8s/milvus-values.yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "2000m"

index_params:
  nlist: 2048  # 生产环境使用更大的nlist
```

## 6. 监控和性能

### 关键指标

- **查询延迟**: <50ms
- **向量搜索准确率**: >95%
- **内存使用**: 监控向量索引大小
- **文档覆盖率**: 确保所有服务类别都有足够的文档

### 备份策略

```bash
# 定期备份集合
milvus-backup create --collection document_embeddings --backup-name backup_$(date +%Y%m%d)
```

## 7. 迁移指南

### 从旧schema迁移

1. **数据导出**: 导出现有数据
2. **schema转换**: 使用统一schema重新组织数据
3. **数据验证**: 确保所有必需字段都存在
4. **性能测试**: 验证新schema的性能表现

### 向后兼容

- 保持现有API接口不变
- 逐步迁移数据，避免服务中断
- 提供数据验证工具确保迁移质量

---

**总结**: 这个统一设计方案解决了之前schema不一致的问题，提供了标准化的字段定义和metadata结构，确保系统的可维护性和扩展性。
