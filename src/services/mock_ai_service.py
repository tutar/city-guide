"""
Mock AI service for City Guide Smart Assistant demo
Provides predefined responses for demonstration without external API calls
"""

import logging
from typing import Any

from src.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class MockAIService:
    """Mock service for AI interactions for demo purposes"""

    def __init__(self):
        self.max_tokens = settings.ai.max_tokens
        self.temperature = settings.ai.temperature

    def generate_embedding(self, text: str) -> list[float]:
        """Generate mock embedding vector"""
        try:
            # Return a simple mock embedding
            embedding_vector = [0.1] * 1024  # Qwen3-Embedding-0.6B dimension
            logger.debug(f"Generated mock embedding for text: {text[:50]}...")
            return embedding_vector

        except Exception as e:
            logger.error(f"Failed to generate mock embedding: {e}")
            raise

    def generate_government_guidance(
        self,
        user_query: str,
        context_documents: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Generate mock government service guidance"""
        try:
            # Predefined responses for common queries
            query_lower = user_query.lower()

            if "hong kong" in query_lower and "passport" in query_lower:
                response_text = """I can help you with Hong Kong passport applications! Here's what you need to know:

**Hong Kong Passport Application Process:**

1. **Eligibility**: Hong Kong permanent residents aged 16 or above
2. **Required Documents**:
   - Hong Kong Identity Card
   - Recent color photo (40mm x 50mm)
   - Proof of address (if applicable)

3. **Application Methods**:
   - Online via Immigration Department website
   - In-person at Immigration Department offices
   - Drop-in at designated post offices

4. **Processing Time**: Usually 10 working days
5. **Fee**: HK$370 for 32-page passport

**Next Steps**:
- Check the official Immigration Department website for the latest requirements
- Prepare your documents before applying
- Consider making an appointment online to save time

Is there anything specific about the passport application process you'd like me to explain further?"""
            elif "business" in query_lower and "registration" in query_lower:
                response_text = """I can help with business registration in Shenzhen! Here are the key steps:

**Shenzhen Business Registration Process:**

1. **Business Name Registration**: Check availability and register your business name
2. **Company Registration**: Submit required documents to the Administration for Industry and Commerce
3. **Tax Registration**: Register with the local tax bureau
4. **Social Security Registration**: Register employees for social security

**Required Documents**:
- Business registration application form
- Identity documents of legal representatives
- Proof of business address
- Articles of Association

Would you like more details about any specific step?"""
            else:
                response_text = f"""I understand you're asking about: {user_query}

As a City Guide Smart Assistant, I can help you navigate various government services including:
- Passport and visa applications
- Business registration and permits
- Tax services and filing
- Social security and healthcare
- Resident permits and household registration

Please provide more specific details about what you need help with, and I'll provide step-by-step guidance based on official government procedures."""

            return {
                "response": response_text,
                "usage": {
                    "total_tokens": len(response_text.split()),
                    "prompt_tokens": 50,
                    "completion_tokens": len(response_text.split()),
                },
                "model": "mock-ai-service",
                "context_documents_used": len(context_documents),
                "navigation_suggestions": [
                    {
                        "label": "Learn more about application requirements",
                        "action_type": "explain",
                        "description": "Detailed requirements and eligibility criteria",
                        "priority": 5,
                    },
                    {
                        "label": "Find application locations",
                        "action_type": "location",
                        "description": "Nearest government service centers",
                        "priority": 4,
                    },
                    {
                        "label": "Check official website",
                        "action_type": "external",
                        "target_url": "https://www.immd.gov.hk",
                        "description": "Official government website for latest information",
                        "priority": 3,
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Failed to generate mock government guidance: {e}")
            raise

    def explain_technical_term(self, term: str, context: str) -> str:
        """Generate mock explanation for technical government terms"""
        try:
            return f"""**{term}** explained:

This is a technical term used in government services. In simple terms, it refers to {context.lower()}.

For most citizens, this means you'll need to provide documentation related to this when applying for certain services. The specific requirements may vary depending on the service you're applying for.

Would you like me to help you find the specific requirements for your situation?"""

        except Exception as e:
            logger.error(f"Failed to explain technical term: {e}")
            raise

    def generate_navigation_suggestions(
        self, current_context: str, available_services: list[str]
    ) -> list[dict[str, str]]:
        """Generate mock contextual navigation suggestions"""
        try:
            suggestions = [
                {"label": "Check application status", "action_type": "status"},
                {"label": "Find service locations", "action_type": "location"},
                {"label": "Download application forms", "action_type": "download"},
                {"label": "Contact support", "action_type": "contact"},
            ]
            return suggestions[:3]

        except Exception as e:
            logger.error(f"Failed to generate navigation suggestions: {e}")
            raise
