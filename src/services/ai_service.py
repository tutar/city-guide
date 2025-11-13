"""
AI service for City Guide Smart Assistant using Deepseek API
"""

import logging
from typing import Any

import requests
import torch
from transformers import AutoModel, AutoTokenizer

from src.utils.config import settings

# Simple in-memory cache for AI responses
_response_cache = {}
_CACHE_MAX_SIZE = 1000
_CACHE_TTL = 300  # 5 minutes

# Configure logging
logger = logging.getLogger(__name__)


def _get_cache_key(
    messages: list[dict[str, str]], system_prompt: str | None = None
) -> str:
    """Generate a cache key from messages and system prompt"""
    import hashlib
    import json

    # Ensure messages are in dict format
    messages_dicts = []
    for msg in messages:
        if hasattr(msg, "role") and hasattr(msg, "content"):
            # Convert Message object to dict
            messages_dicts.append({"role": msg.role, "content": msg.content})
        else:
            # Already a dict
            messages_dicts.append(msg)

    # Create a string representation of the input
    cache_data = {"messages": messages_dicts, "system_prompt": system_prompt}
    cache_str = json.dumps(cache_data, sort_keys=True)

    # Generate hash
    return hashlib.md5(cache_str.encode()).hexdigest()


def _clean_cache():
    """Clean cache if it exceeds maximum size"""
    global _response_cache
    if len(_response_cache) > _CACHE_MAX_SIZE:
        # Remove oldest entries (first 20%)
        keys_to_remove = list(_response_cache.keys())[: _CACHE_MAX_SIZE // 5]
        for key in keys_to_remove:
            _response_cache.pop(key, None)
        logger.info(f"Cleaned cache, removed {len(keys_to_remove)} entries")


class AIService:
    """Service for AI interactions including Deepseek API and embedding models"""

    def __init__(self):
        self.deepseek_api_key = settings.ai.deepseek_api_key
        self.deepseek_base_url = settings.ai.deepseek_base_url
        self.max_tokens = settings.ai.max_tokens
        self.temperature = settings.ai.temperature

        # Initialize embedding model
        self.embedding_model_name = settings.ai.embedding_model
        self._setup_embedding_model()

    def _setup_embedding_model(self):
        """Setup the embedding model for Chinese text with local cache priority"""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")

            # Load from local cache only
            logger.info("Loading model from local cache")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.embedding_model_name,
            )
            self.embedding_model = AutoModel.from_pretrained(
                self.embedding_model_name,
            )

            # Set model to evaluation mode
            self.embedding_model.eval()
            logger.info("Embedding model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text using Qwen3-Embedding-0.6B"""
        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text, return_tensors="pt", padding=True, truncation=True, max_length=512
            )

            # Generate embeddings
            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()

            # Convert to list
            embedding_vector = embeddings.tolist()

            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding_vector

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Send chat completion request to Deepseek API"""
        try:
            # Check cache first
            cache_key = _get_cache_key(messages, system_prompt)
            if cache_key in _response_cache:
                logger.info("Cache hit for AI response")
                return _response_cache[cache_key]

            # Ensure messages are in dict format
            messages_dicts = []
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    # Convert Message object to dict
                    messages_dicts.append({"role": msg.role, "content": msg.content})
                else:
                    # Already a dict
                    messages_dicts.append(msg)

            # Prepare request payload
            payload = {
                "model": "deepseek-chat",
                "messages": messages_dicts,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "stream": False,
            }

            # Add system prompt if provided
            if system_prompt:
                payload["messages"].insert(
                    0, {"role": "system", "content": system_prompt}
                )

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.deepseek_base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(
                    f"Deepseek API error: {response.status_code} - {response.text}"
                )
                raise Exception(f"API request failed: {response.status_code}")

            result = response.json()

            # Cache the result
            _response_cache[cache_key] = result
            _clean_cache()

            logger.info(
                f"Deepseek API response received, tokens used: {result.get('usage', {}).get('total_tokens', 0)}"
            )
            return result

        except requests.exceptions.Timeout:
            logger.error("Deepseek API request timed out")
            raise
        except Exception as e:
            logger.error(f"Failed to get chat completion: {e}")
            raise

    def generate_government_guidance(
        self,
        user_query: str,
        context_documents: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Generate government service guidance using context from search results"""
        try:
            # Prepare system prompt for government service guidance
            system_prompt = """You are a helpful assistant for Shenzhen government services. Your role is to provide accurate, step-by-step guidance for government procedures based on official information sources.

Guidelines:
1. Provide clear, actionable steps
2. Reference official sources when available
3. Be concise but thorough
4. Use simple language
5. Include relevant requirements and documents needed
6. Suggest next steps or related services

Format your response with clear sections and bullet points when appropriate."""

            # Prepare context from documents - OPTIMIZED: limit to top 2 documents and shorter content
            context_text = ""
            for i, doc in enumerate(
                context_documents[:2]
            ):  # OPTIMIZED: Use only top 2 most relevant documents
                context_text += f"\n\nDocument {i+1}: {doc.get('title', 'Unknown')}\n"
                # OPTIMIZED: Shorter content to reduce token count
                context_text += f"Content: {doc.get('content', '')[:300]}..."

            # Prepare user message with context - OPTIMIZED: more concise
            user_message = f"""Query: {user_query}

Context:{context_text}

Provide government service guidance."""

            # Prepare messages for API - OPTIMIZED: limit conversation history
            messages = []

            # Add conversation history if available
            if conversation_history:
                messages.extend(
                    conversation_history[-3:]
                )  # OPTIMIZED: Last 3 messages only

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Get response from Deepseek API with optimized parameters
            response = self.chat_completion(
                messages,
                system_prompt,
                max_tokens=800,  # OPTIMIZED: Limit response length
                temperature=0.3,  # OPTIMIZED: More deterministic responses
            )

            # Extract the assistant's response
            assistant_response = response["choices"][0]["message"]["content"]

            return {
                "response": assistant_response,
                "usage": response.get("usage", {}),
                "model": response.get("model", "deepseek-chat"),
                "context_documents_used": len(context_documents),
            }

        except Exception as e:
            logger.error(f"Failed to generate government guidance: {e}")
            raise

    def explain_technical_term(self, term: str, context: str) -> str:
        """Generate explanation for technical government terms"""
        try:
            system_prompt = """You are a government service expert. Explain technical terms in simple, clear language that ordinary citizens can understand. Focus on practical implications and how it affects their service experience."""

            user_message = f"""Please explain this government term in simple language:

Term: {term}
Context: {context}

Provide a clear, concise explanation that would help someone understand what this term means and why it's important for their government service."""

            messages = [{"role": "user", "content": user_message}]
            response = self.chat_completion(messages, system_prompt)

            return response["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Failed to explain technical term: {e}")
            raise

    def generate_navigation_suggestions(
        self, current_context: str, available_services: list[str]
    ) -> list[dict[str, str]]:
        """Generate contextual navigation suggestions"""
        try:
            system_prompt = """You are a navigation assistant for government services. Suggest relevant next steps or related services based on the current conversation context. Provide suggestions in a clear, actionable format."""

            user_message = f"""Current conversation context: {current_context}

Available services: {', '.join(available_services)}

Suggest 3-5 relevant navigation options that would help the user continue their government service journey. Format each suggestion as a clear action label."""

            messages = [{"role": "user", "content": user_message}]
            response = self.chat_completion(messages, system_prompt)

            # Parse the response to extract navigation suggestions
            suggestions_text = response["choices"][0]["message"]["content"]

            # Simple parsing - in practice, you might want more sophisticated parsing
            suggestions = []
            lines = suggestions_text.split("\n")

            for line in lines:
                line = line.strip()
                if line and (
                    line.startswith("-") or line.startswith("•") or line[0].isdigit()
                ):
                    # Remove bullet points or numbers
                    clean_line = line.lstrip("-• ").lstrip("1234567890. ")
                    if clean_line:
                        suggestions.append(
                            {"label": clean_line, "action_type": "related"}
                        )

            return suggestions[:5]  # Return max 5 suggestions

        except Exception as e:
            logger.error(f"Failed to generate navigation suggestions: {e}")
            raise

    def validate_response_quality(
        self, user_query: str, assistant_response: str
    ) -> dict[str, Any]:
        """Validate the quality of the assistant's response"""
        try:
            system_prompt = """You are a quality assurance expert for government service responses. Evaluate the quality of the assistant's response based on accuracy, completeness, clarity, and helpfulness."""

            user_message = f"""Evaluate this government service response:

User Query: {user_query}
Assistant Response: {assistant_response}

Please provide:
1. Accuracy score (1-5): How accurate is the information?
2. Completeness score (1-5): Does it address all aspects of the query?
3. Clarity score (1-5): Is the response clear and easy to understand?
4. Helpfulness score (1-5): How helpful is the response for the user?
5. Brief feedback on what could be improved.

Format your response as:
Accuracy: [score]
Completeness: [score]
Clarity: [score]
Helpfulness: [score]
Feedback: [your feedback]"""

            messages = [{"role": "user", "content": user_message}]
            response = self.chat_completion(messages, system_prompt)

            # Parse the response to extract scores
            evaluation_text = response["choices"][0]["message"]["content"]

            # Simple parsing - in practice, you might want more sophisticated parsing
            scores = {}
            lines = evaluation_text.split("\n")

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key in ["accuracy", "completeness", "clarity", "helpfulness"]:
                        try:
                            # Extract numeric score
                            score = int(value.split()[0])
                            scores[key] = min(max(score, 1), 5)
                        except (ValueError, IndexError):
                            scores[key] = 3  # Default score if parsing fails
                    elif key == "feedback":
                        scores["feedback"] = value

            # Calculate overall score
            if len(scores) >= 4:
                scores["overall"] = (
                    sum(
                        [
                            scores.get(k, 3)
                            for k in [
                                "accuracy",
                                "completeness",
                                "clarity",
                                "helpfulness",
                            ]
                        ]
                    )
                    / 4
                )
            else:
                scores["overall"] = 3

            return scores

        except Exception as e:
            logger.error(f"Failed to validate response quality: {e}")
            return {"overall": 3, "error": str(e)}
