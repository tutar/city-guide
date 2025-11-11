# Data Model: Document Source Attribution

**Feature**: Document Source Attribution for AI Responses
**Date**: 2025-11-11

## Entities

### DocumentSource
Represents a source document with metadata for attribution

**Attributes**:
- `id`: UUID (primary key)
- `title`: String - Document title for display
- `location`: String - Document storage location/URL
- `access_info`: JSON - Access permissions and metadata
- `created_at`: DateTime - When document was added
- `updated_at`: DateTime - Last metadata update

**Relationships**:
- One-to-many with `ResponseAttribution`
- One-to-many with `CitationList` entries

### ResponseAttribution
Maps sentences in AI responses to source documents

**Attributes**:
- `id`: UUID (primary key)
- `response_id`: UUID - Reference to AI response
- `sentence_index`: Integer - Position of sentence in response
- `document_source_id`: UUID - Reference to source document
- `confidence_score`: Float - AI confidence in attribution (0.0-1.0)
- `created_at`: DateTime - When attribution was created

**Relationships**:
- Many-to-one with `DocumentSource`
- Many-to-one with AI Response entity

### CitationList
Complete collection of documents referenced in an AI response

**Attributes**:
- `id`: UUID (primary key)
- `response_id`: UUID - Reference to AI response
- `document_sources`: Array[UUID] - List of referenced document IDs
- `created_at`: DateTime - When citation list was created

**Relationships**:
- One-to-many with `DocumentSource`
- One-to-one with AI Response entity

## Validation Rules

### DocumentSource
- `title` must be non-empty
- `location` must be valid storage reference
- `access_info` must contain required permission fields

### ResponseAttribution
- `sentence_index` must be non-negative
- `confidence_score` must be between 0.0 and 1.0
- `response_id` and `document_source_id` must reference valid entities

### CitationList
- `document_sources` must contain valid UUIDs
- Must contain all documents referenced in response attributions

## State Transitions

### Document Access Flow
1. **Available** → Document is accessible and can be referenced
2. **Unavailable** → Document temporarily inaccessible (graceful degradation)
3. **Restricted** → Document access requires additional permissions

### Attribution Tracking Flow
1. **Generating** → AI response being generated with attribution tracking
2. **Attributed** → Response complete with all attributions mapped
3. **Displayed** → Response shown to user with attribution markers

## Data Volume Considerations

- Expected: 5-20 documents per response
- Attribution mapping: 10-50 sentences per response
- Metadata size: <1KB per attribution entry
- Performance target: <10% impact on response generation
