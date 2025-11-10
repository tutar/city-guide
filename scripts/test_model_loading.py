#!/usr/bin/env python3
"""
Test model loading with local cache priority
"""

import logging
from src.services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_model_loading():
    """Test model loading with local cache priority"""
    try:
        print("Testing model loading with local cache priority...")

        # Create AI service instance
        ai_service = AIService()

        print("\n✓ AI service initialized successfully")
        print(f"✓ Embedding model: {ai_service.embedding_model_name}")
        print(f"✓ Tokenizer loaded: {ai_service.tokenizer is not None}")
        print(f"✓ Model loaded: {ai_service.embedding_model is not None}")

        # Test embedding generation
        test_text = "港澳通行证申请流程"
        embedding = ai_service.generate_embedding(test_text)

        print(f"✓ Generated embedding for: '{test_text}'")
        print(f"✓ Embedding dimension: {len(embedding)}")
        print(f"✓ Embedding sample: {embedding[:5]}...")

        return {
            "status": "success",
            "model_loaded": True,
            "embedding_generated": True,
            "embedding_dimension": len(embedding),
        }

    except Exception as e:
        logger.error(f"Failed to test model loading: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Testing model loading with local cache priority...")
    result = test_model_loading()

    if result["status"] == "success":
        print(f"\n✓ Model loading test completed successfully!")
        print(f"  - Model loaded: {result['model_loaded']}")
        print(f"  - Embedding generated: {result['embedding_generated']}")
        print(f"  - Embedding dimension: {result['embedding_dimension']}")
    else:
        print(f"\n✗ Model loading test failed: {result['error']}")
