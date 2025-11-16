# Quick Start: Document Source Attribution

**Feature**: Add document source attribution to AI-generated responses
**Branch**: 001-document-attribution

## Overview

This feature enhances the existing AI conversation system to include document source attribution at the sentence level, enabling users to verify information sources and access original documents.

## Key Changes

### Backend Changes
- **Enhanced Response Format**: `/api/conversation/message` now returns attribution data alongside AI responses
- **Attribution Tracking**: Sentence-level mapping between response content and source documents
- **Document Metadata**: Extended document repository with attribution support

### Frontend Changes
- **Attribution Display**: UI components to show document sources inline and in citation lists
- **Document Navigation**: Clickable references to access original source documents

## API Usage

### Enhanced Conversation Endpoint

```python
# Request (unchanged)
POST /api/conversation/message
{
  "message": "What are the main tourist attractions?",
  "conversation_id": "uuid-here"
}

# Response (enhanced)
{
  "response": "The Eiffel Tower is a major attraction in Paris [1]. The Louvre Museum houses famous artworks [2].",
  "conversation_id": "uuid-here",
  "attribution": {
    "sentence_attributions": [
      {
        "sentence_index": 0,
        "document_id": "doc-uuid-1",
        "confidence_score": 0.95
      },
      {
        "sentence_index": 1,
        "document_id": "doc-uuid-2",
        "confidence_score": 0.92
      }
    ],
    "citation_list": {
      "document_sources": [
        {
          "id": "doc-uuid-1",
          "title": "Paris Travel Guide 2024",
          "location": "/documents/paris-guide.pdf",
          "access_info": {"permission": "public"}
        },
        {
          "id": "doc-uuid-2",
          "title": "Museum Collections Database",
          "location": "/documents/museums.json",
          "access_info": {"permission": "public"}
        }
      ]
    }
  }
}
```

## Implementation Steps

### Phase 1: Backend Attribution Tracking
1. Extend AI response generation to track document usage
2. Implement sentence-level attribution mapping
3. Enhance `/api/conversation/message` response format
4. Add attribution data models and services

### Phase 2: Frontend Attribution Display
1. Create attribution display components
2. Implement inline source markers
3. Add citation list display
4. Enable document navigation from references

### Phase 3: Testing & Validation
1. Unit tests for attribution tracking
2. Integration tests for end-to-end flow
3. Performance testing to ensure <10% impact
4. User acceptance testing

## Testing

Run the test suite:
```bash
cd src && pytest tests/unit/test_attribution_service.py
cd src && pytest tests/integration/test_attribution_integration.py
```

## Performance Considerations

- Attribution tracking should not impact response generation speed by more than 10%
- Use efficient data structures for attribution mapping
- Cache frequently accessed document metadata
- Implement graceful degradation for document access failures

## Migration Notes

- Backward compatible: Existing clients will continue to work
- New attribution data is additive to existing response format
- No breaking changes to existing API contracts
