# Implementation Plan: City Guide Smart Assistant

**Branch**: `001-city-guide-assistant` | **Date**: 2025-11-07 | **Spec**: `/specs/001-city-guide-assistant/spec.md`
**Input**: Feature specification from `/specs/001-city-guide-assistant/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an AI-powered conversational assistant that provides accurate, step-by-step guidance for Shenzhen government services through natural language interaction. The system uses Deepseek API for AI reasoning and implements hybrid search (vector + keyword) with Milvus vector database for enhanced information retrieval. Features include dynamic contextual navigation, integration with official data sources, and conversation context management using Chainlit for the frontend interface.

## Technical Context

**Language/Version**: Python 3.11 (backend), Chainlit (frontend)
**Primary Dependencies**: FastAPI (backend), Chainlit (frontend), Deepseek API (AI), PostgreSQL (relational), Milvus (vector database), FlagEmbedding (bge-m3/Qwen3-Embedding-0.6B)
**Storage**: PostgreSQL for structured data, Redis for session/cache, Milvus for embeddings
**Testing**: pytest (backend), Chainlit testing utilities, Playwright (e2e)
**Target Platform**: Web application (Chainlit interface), potential mobile app later
**Project Type**: web - determines source structure
**Performance Goals**: Sub-200ms response times for core interactions, 99.9% uptime, AI response <1s
**Constraints**: <200ms p95 response time, <100MB memory per instance, offline-capable for cached data
**Scale/Scope**: 10k users, 50+ government service categories, 100+ conversation flows, hybrid search with vector embeddings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Code Quality Standards
- **Status**: Compliant
- **Verification**: Plan includes comprehensive documentation, modular architecture, and defined quality gates
- **Rationale**: Government service application requires exceptional reliability and clarity

### ✅ Test-First Development
- **Status**: Compliant
- **Verification**: Test pyramid defined (70/20/10), TDD approach specified
- **Rationale**: Government services require absolute reliability and accuracy

### ✅ User Experience Consistency
- **Status**: Compliant
- **Verification**: Chainlit provides consistent UI patterns, accessibility standards, performance monitoring
- **Rationale**: Must be accessible to all citizens regardless of technical proficiency

### ✅ Performance & Scalability
- **Status**: Compliant
- **Verification**: Sub-200ms response times, 99.9% uptime, scalability designed-in
- **Rationale**: Must remain available during peak usage and emergencies

### ✅ Security & Data Integrity
- **Status**: Compliant
- **Verification**: Multi-layer validation, external API security review, data accuracy verification
- **Rationale**: Handles sensitive citizen information requiring confidentiality

**Overall Status**: ✅ PASS - All constitutional requirements met

### Post-Design Constitution Re-check

After completing Phase 1 design with updated technology stack:

- **✅ Code Quality Standards**: Enhanced with comprehensive integration patterns for Milvus, Chainlit, and BGE-M3
- **✅ Test-First Development**: Updated test strategy includes vector database testing and Chainlit UI testing
- **✅ User Experience Consistency**: Chainlit provides consistent conversational interface with accessibility features
- **✅ Performance & Scalability**: Milvus with BGE-M3 optimizes for sub-1s response times and government-scale deployment
- **✅ Security & Data Integrity**: Self-hosted Milvus ensures data sovereignty, comprehensive validation with source priority

**Final Status**: ✅ PASS - All constitutional requirements maintained with enhanced technical foundation

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
city-guide-assistant/
├── src/
│   ├── models/
│   │   ├── conversation.py
│   │   ├── service_category.py
│   │   ├── navigation_context.py
│   │   └── document_embedding.py
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── navigation_service.py
│   │   ├── data_validation_service.py
│   │   ├── hybrid_search_service.py
│   │   ├── embedding_service.py
│   │   └── deepseek_client.py
│   ├── chainlit_app/
│   │   ├── app.py
│   │   ├── components/
│   │   │   ├── conversation_ui.py
│   │   │   ├── navigation_sidebar.py
│   │   │   └── service_display.py
│   │   └── utils/
│   │       ├── message_handlers.py
│   │       └── ui_helpers.py
│   ├── data/
│   │   ├── crawlers/
│   │   │   ├── government_crawler.py
│   │   │   └── local_guide_crawler.py
│   │   ├── processors/
│   │   │   ├── document_processor.py
│   │   │   └── embedding_generator.py
│   │   └── validators/
│   │       ├── data_validator.py
│   │       └── source_priority.py
│   └── utils/
│       ├── milvus_client.py
│       └── external_api.py
├── tests/
│   ├── unit/
│   │   ├── test_models/
│   │   └── test_services/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_external/
│   ├── contract/
│   │   └── test_contracts/
│   └── performance/
│       └── test_hybrid_search.py
└── requirements/
    ├── requirements.txt
    └── requirements-dev.txt
```

**Structure Decision**: Single project structure with Chainlit frontend integrated into the Python backend. Enhanced backend includes hybrid search capabilities with Milvus vector database integration, Deepseek API client, and data processing pipelines for government service information retrieval and embedding generation using FlagEmbedding models.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
