# Implementation Plan: City Guide Smart Assistant

**Branch**: `001-city-guide-assistant` | **Date**: 2025-11-07 | **Spec**: `/specs/001-city-guide-assistant/research.md`
**Input**: Feature specification from `/specs/001-city-guide-assistant/research.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an AI-powered conversational interface for Shenzhen government services using Deepseek API for reasoning, Qwen3-Embedding-0.6B for embeddings, Milvus for vector storage, Chainlit for frontend, and RRF for hybrid search. The system will provide accurate, step-by-step guidance through natural language interaction with source attribution and context-aware navigation.

## Technical Context

**Language/Version**: Python 3.11+ for backend, Node.js 18+ for frontend
**Primary Dependencies**: FastAPI, Chainlit, transformers, pymilvus, deepseek-api, qdrant-client
**Storage**: PostgreSQL for metadata, Milvus for vectors, Redis for caching
**Testing**: pytest for backend, Jest for frontend, contract testing
**Target Platform**: Linux server for backend, web browser for frontend
**Project Type**: web application (frontend + backend)
**Performance Goals**: <2s AI response time, <1s search latency, 100+ concurrent users
**Constraints**: <200ms p95 for search, <100MB memory per embedding model instance, Chinese language optimization
**Scale/Scope**: 10k government service documents, 50+ service categories, multi-language support

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── conversation.py
│   │   ├── services.py
│   │   └── embeddings.py
│   ├── services/
│   │   ├── search_service.py
│   │   ├── embedding_service.py
│   │   ├── ai_service.py
│   │   └── data_service.py
│   ├── api/
│   │   ├── conversation.py
│   │   ├── services.py
│   │   └── search.py
│   └── utils/
│       ├── config.py
│       ├── logging.py
│       └── validation.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── scripts/
    ├── setup_database.py
    ├── setup_vector_db.py
    └── data_ingestion.py

frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface/
│   │   ├── ServiceNavigation/
│   │   └── SearchResults/
│   ├── pages/
│   │   ├── Home/
│   │   ├── Services/
│   │   └── Conversation/
│   ├── services/
│   │   ├── api.js
│   │   ├── conversation.js
│   │   └── search.js
│   └── utils/
│       ├── constants.js
│       └── helpers.js
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

**Structure Decision**: Web application structure selected with separate backend (FastAPI) and frontend (Chainlit) components. This provides clear separation of concerns, enables independent development and deployment, and supports the conversational AI focus with Chainlit's specialized capabilities.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
