# Research: City Guide Smart Assistant

**Date**: 2025-11-06
**Feature**: City Guide Smart Assistant
**Purpose**: Document technology choices and implementation decisions with Deepseek API and hybrid search requirements

## Technology Stack Decisions

### AI Model: Deepseek API

**Decision**: Use Deepseek API for AI reasoning and conversation generation

**Rationale**:
- Deepseek provides competitive performance with cost-effective pricing
- Strong Chinese language understanding capabilities for government services
- Good API stability and developer support
- Suitable for retrieval-augmented generation (RAG) workflows

**Alternatives considered**:
- **OpenAI API**: Higher cost, potential geopolitical considerations
- **Local models**: Insufficient performance for production government service application
- **Other Chinese LLMs**: Deepseek offers good balance of performance and cost

### Vector Database: Qdrant

**Decision**: Use Qdrant for vector storage and similarity search

**Rationale**:
- High-performance vector similarity search
- Good Python client support
- Efficient filtering capabilities
- Open-source with commercial support options

**Alternatives considered**:
- **Chroma**: Simpler but less mature for production use
- **Pinecone**: Managed service but higher cost and vendor lock-in
- **Weaviate**: More complex setup for this use case

### Embedding Model: SentenceTransformers

**Decision**: Use SentenceTransformers for document and query embeddings

**Rationale**:
- Excellent Chinese language support with models like `paraphrase-multilingual-MiniLM-L12-v2`
- Good balance of performance and accuracy
- Easy integration with Python ecosystem
- Can run locally or via API

**Alternatives considered**:
- **OpenAI embeddings**: Higher cost and API dependency
- **BERT-based models**: More computationally intensive
- **Custom models**: Too complex for MVP

### Hybrid Search Strategy

**Decision**: Implement hybrid search combining dense and sparse retrieval

**Rationale**:
- **Dense retrieval (vector search)**: Handles semantic similarity and paraphrased queries
- **Sparse retrieval (BM25)**: Handles exact keyword matches and specific terminology
- **Fusion ranking**: Combines both approaches for optimal relevance

**Implementation**:
- Vector search for semantic similarity using embeddings
- BM25 for keyword-based retrieval
- Reciprocal Rank Fusion (RRF) for result combination
- Source priority weighting for official vs auxiliary sources

## Architecture Decisions

### Retrieval-Augmented Generation (RAG) Pipeline

**Decision**: Implement full RAG pipeline with hybrid search

**Rationale**:
- Ensures information accuracy by grounding responses in official sources
- Reduces AI hallucinations
- Enables real-time information updates
- Provides source attribution for trust building

**Pipeline Steps**:
1. Data ingestion from official sources (Shenzhen government websites)
2. Document processing and chunking
3. Vector embedding generation
4. Hybrid search at query time
5. Context enhancement for Deepseek API
6. Response generation with source attribution

### Data Processing Pipeline

**Decision**: Implement automated data processing with monitoring

**Rationale**:
- Government information changes frequently
- Requires robust error handling and monitoring
- Multiple data sources need coordination

**Components**:
- **Government crawler**: For official Shenzhen government websites
- **Local guide crawler**: For Shenzhen local guide supplementary information
- **Document processor**: For chunking and cleaning
- **Embedding generator**: For vector creation
- **Data validator**: For accuracy verification

### Source Priority Management

**Decision**: Implement source priority system with official-first approach

**Rationale**:
- Government services require absolute accuracy
- Official sources have highest authority
- Supplementary sources provide context and interpretation

**Implementation**:
- Official government sources: Highest priority
- Local guide sources: Supplementary with clear attribution
- Conflict resolution: Always prefer official sources
- Source weighting in search ranking

## Implementation Patterns

### Conversation Context Management

**Decision**: Maintain conversation context with hybrid search integration

**Rationale**:
- Enables contextual search based on conversation history
- Supports multi-turn interactions
- Maintains user preferences and service context

### Dynamic Navigation System

**Decision**: Implement context-aware navigation with search integration

**Rationale**:
- Navigation options should reflect search results and conversation context
- Enables intuitive exploration of related services
- Maintains consistency across conversation flows

### Data Validation Strategy

**Decision**: Multi-layer validation with source verification

**Rationale**:
- Government services require high data accuracy
- Multiple sources need verification
- Real-time validation against official sources

## Performance Considerations

### Hybrid Search Optimization

**Decision**: Implement caching and optimization for hybrid search

**Rationale**:
- Vector search can be computationally intensive
- BM25 search is fast but less semantic
- Fusion ranking needs optimization for real-time performance

**Optimizations**:
- Embedding caching for common queries
- Result caching with TTL
- Parallel execution of dense and sparse search
- Index optimization for government service terminology

### Response Time Targets

**Decision**: Optimize for sub-1s AI response times

**Rationale**:
- Government service users expect quick responses
- Complex RAG pipeline needs optimization
- Real-time conversation requires low latency

## Security Considerations

### Data Protection

**Decision**: Implement comprehensive data protection measures

**Rationale**:
- Government service data requires confidentiality
- User conversations may contain sensitive information
- External API integrations need security

### External API Security

**Decision**: Implement rate limiting and request validation for Deepseek API

**Rationale**:
- Prevents API abuse and cost overruns
- Ensures service reliability
- Maintains good relationship with API provider

## Monitoring and Observability

### Search Quality Monitoring

**Decision**: Implement search quality metrics and monitoring

**Rationale**:
- Hybrid search effectiveness needs continuous evaluation
- User feedback integration for improvement
- Performance monitoring for optimization

**Metrics**:
- Search relevance scores
- User satisfaction ratings
- Response accuracy measurements
- Search latency monitoring