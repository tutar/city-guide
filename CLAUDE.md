# city-guide Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-07

## Active Technologies
- Python 3.12+ (backend), Chainlit (frontend) + FastAPI (backend), Chainlit (frontend), Deepseek API (AI), PostgreSQL (relational), Milvus (vector database), Qwen3-Embedding-0.6B (embeddings) (001-city-guide-assistant)
- Node.js v22+ for tooling (001-city-guide-assistant)
- PostgreSQL for metadata, Milvus for vectors, Redis for caching (001-city-guide-assistant)

## Project Structure

```text
src/
├── models/
├── services/
├── api/
├── chainlit/
└── utils/

tests/
├── unit/
├── integration/
└── contract/

scripts/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.12+ (backend), Chainlit (frontend): Follow standard conventions

## Recent Changes
- 001-city-guide-assistant: Updated to Python 3.12+ (Python 3.11+ EoL), Node.js v22+ (Node.js 18+ EoL) + FastAPI, Chainlit, transformers, pymilvus, deepseek-api, qdrant-client, Qwen3-Embedding-0.6B


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
