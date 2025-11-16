# Data Model: City Guide Smart Assistant

**Date**: 2025-11-07
**Feature**: City Guide Smart Assistant

## Core Entities

### ServiceCategory
Represents a government service area with associated procedures and requirements.

**Fields**:
- `id` (UUID): Primary key
- `name` (string): Service category name (e.g., "Passports", "Visas", "Permits")
- `description` (string): Brief description of the service
- `official_source_url` (string): URL to official government information
- `last_verified` (datetime): When information was last verified
- `is_active` (boolean): Whether this service is currently available
- `created_at` (datetime): Record creation timestamp
- `updated_at` (datetime): Last update timestamp

**Validation Rules**:
- Name must be unique
- Official source URL must be valid and accessible
- Last verified must be within last 30 days

### ConversationContext
Represents the current state of user interaction including current topic, navigation options, and conversation history.

**Fields**:
- `id` (UUID): Primary key
- `user_session_id` (string): Anonymous session identifier
- `current_service_category_id` (UUID, foreign key): Reference to current service
- `conversation_history` (JSON): Array of message objects with timestamps
- `user_preferences` (JSON): User language, location preferences
- `created_at` (datetime): Session start timestamp
- `last_activity` (datetime): Last user interaction timestamp
- `is_active` (boolean): Whether session is still active

**State Transitions**:
- `created` → `active` (when first message received)
- `active` → `inactive` (after 30 minutes of inactivity)
- `active` → `completed` (when user explicitly ends conversation)

### NavigationOption
Represents contextual action items that adapt based on user needs and conversation flow.

**Fields**:
- `id` (UUID): Primary key
- `service_category_id` (UUID, foreign key): Parent service category
- `label` (string): Display text for navigation option
- `action_type` (enum): ["explain", "requirements", "appointment", "location", "related"]
- `target_url` (string, nullable): URL for external actions
- `description` (string): Detailed description of what this option provides
- `priority` (integer): Display order priority (1-10)
- `is_active` (boolean): Whether this option is currently available

**Validation Rules**:
- Label must be clear and actionable
- Action type must be one of predefined values
- Target URL must be valid when provided

### OfficialInformationSource
Represents authoritative data sources with validation mechanisms and update tracking.

**Fields**:
- `id` (UUID): Primary key
- `name` (string): Source name (e.g., "Shenzhen Government Portal")
- `base_url` (string): Base URL for the source
- `api_endpoint` (string, nullable): API endpoint if available
- `update_frequency` (enum): ["daily", "weekly", "monthly", "on_change"]
- `last_checked` (datetime): When source was last checked
- `status` (enum): ["active", "inactive", "error"]
- `error_count` (integer): Number of consecutive errors
- `created_at` (datetime): Record creation timestamp

### DocumentEmbedding
Represents vector embeddings for government service documents to enable semantic search.

**Fields**:
- `id` (UUID): Primary key
- `source_id` (UUID, foreign key): Reference to official information source
- `document_url` (string): Original document URL
- `document_title` (string): Document title
- `document_content` (text): Processed document content
- `chunk_index` (integer): Index for document chunks
- `embedding_vector` (vector): Vector embedding (1024 dimensions for Qwen3-Embedding-0.6B)
- `embedding_model` (string): Model used for embedding (Qwen/Qwen3-Embedding-0.6B)
- `metadata` (JSON): Additional metadata (source priority, update date, etc.)
- `created_at` (datetime): Embedding creation timestamp

**Validation Rules**:
- Document content must be non-empty
- Embedding vector must be valid dimension
- Source priority must be set (official vs auxiliary)

### SearchQuery
Represents user search queries for analytics and improvement.

**Fields**:
- `id` (UUID): Primary key
- `session_id` (string): User session identifier
- `query_text` (string): Original search query
- `query_embedding` (vector): Query embedding vector
- `search_results` (JSON): Retrieved document IDs and scores
- `hybrid_score` (float): Combined hybrid search score
- `response_quality` (integer, nullable): User feedback rating (1-5)
- `created_at` (datetime): Query timestamp

## Relationships

- **ConversationContext** → **ServiceCategory** (Many-to-One)
  - Multiple conversations can reference the same service category
  - Conversation context tracks current service category

- **ServiceCategory** → **OfficialInformationSource** (Many-to-Many)
  - Service categories can have multiple official sources
  - Sources can provide information for multiple service categories

- **OfficialInformationSource** → **DocumentEmbedding** (One-to-Many)
  - One source can have multiple document embeddings
  - Embeddings are tied to their source for priority management

- **SearchQuery** → **ConversationContext** (Many-to-One)
  - Multiple search queries can belong to one conversation
  - Search queries are tied to conversation sessions

## Data Integrity Rules

### Service Information Accuracy
- All service information must reference at least one official source
- Information must be verified within 30 days
- Any conflicting information between sources must be flagged for manual review
- Official sources have priority over auxiliary sources

### Conversation Context Management
- Inactive conversations are automatically archived after 24 hours
- Conversation history is anonymized and contains no PII

### Vector Embedding Management
- Embeddings must be regenerated when source documents change
- Source priority must be maintained in embedding metadata
- Document chunks must be semantically meaningful for search

### External Data Validation
- All external URLs must be validated for accessibility
- API responses must be validated against expected schemas
- Rate limiting must be implemented for external API calls
- Source monitoring must detect website structure changes

## Indexing Strategy

### Primary Indexes
- `ServiceCategory.id` (primary key)
- `ConversationContext.user_session_id` (session lookup)
- `DocumentEmbedding.source_id` (source-based queries)

### Performance Indexes
- `ServiceCategory.is_active` (active services filter)
- `ConversationContext.last_activity` (cleanup operations)
- `OfficialInformationSource.status` (source monitoring)
- `DocumentEmbedding.embedding_model` (model-specific queries)

### Vector Indexes
- `DocumentEmbedding.embedding_vector` (vector similarity search)
- `SearchQuery.query_embedding` (query analysis)

## Infrastructure Data Models

### ServiceDependency
Tracks infrastructure service dependencies for deployment and monitoring.

**Fields**:
- `id` (UUID): Primary key
- `service_name` (string): Service name (e.g., "PostgreSQL", "Milvus", "Redis")
- `service_type` (enum): ["database", "cache", "vector_db", "api"]
- `version` (string): Required version
- `health_check_url` (string, nullable): URL for health checks
- `is_required` (boolean): Whether service is required for operation
- `created_at` (datetime): Record creation timestamp
- `updated_at` (datetime): Last update timestamp

### EnvironmentConfiguration
Manages environment-specific configuration settings.

**Fields**:
- `id` (UUID): Primary key
- `environment` (enum): ["development", "staging", "production"]
- `config_key` (string): Configuration key
- `config_value` (string): Configuration value
- `is_secret` (boolean): Whether value is sensitive
- `description` (string): Configuration description
- `created_at` (datetime): Record creation timestamp
- `updated_at` (datetime): Last update timestamp

## Infrastructure Relationships

- **ServiceDependency** → **EnvironmentConfiguration** (One-to-Many)
  - Service dependencies can have multiple environment configurations
  - Configurations are specific to deployment environments

## Infrastructure Validation Rules

### Service Dependency Management
- Required services must have health check endpoints defined
- Service versions must be compatible with application requirements
- Missing required services must trigger application startup failures

### Environment Configuration
- Secret values must be encrypted at rest
- Development configurations must not be used in production
- Configuration changes must be tracked with audit trail

## Data Retention Policies

### Conversation Data
- Active conversation data: 30 days
- Archived conversation data: 1 year (anonymized)
- Analytics data: 2 years (aggregated)

### Service Information
- Service category data: Permanent (with version history)
- Navigation options: Permanent (with audit trail)
- Official source data: Permanent (with update history)

### Vector Data
- Document embeddings: Permanent (with regeneration on change)
- Search queries: 6 months (for analytics and improvement)
- Query embeddings: 3 months (for search optimization)

### Infrastructure Data
- Service dependency data: Permanent
- Environment configurations: Permanent (with version history)
