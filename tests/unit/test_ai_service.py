"""
Unit tests for AI service and Deepseek API integration
"""

from unittest.mock import Mock, patch

import pytest
import requests
import torch
from transformers import AutoModel, AutoTokenizer


class TestAIService:
    """Test suite for AIService and Deepseek API integration"""

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        """Mock settings for all tests"""
        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.deepseek_api_key = "test-api-key"
            mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.ai.max_tokens = 1000
            mock_settings.ai.temperature = 0.7
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"
            yield mock_settings

    def test_ai_service_initialization(self, mock_settings):
        """Test AIService initialization with configuration"""
        # Given mocked settings
        from src.services.ai_service import AIService

        # When initializing AIService
        with patch.object(AIService, "_setup_embedding_model") as mock_setup:
            ai_service = AIService()

            # Then service should be initialized with correct configuration
            assert ai_service.deepseek_api_key == "test-api-key"
            assert ai_service.deepseek_base_url == "https://api.deepseek.com"
            assert ai_service.max_tokens == 1000
            assert ai_service.temperature == 0.7
            assert ai_service.embedding_model_name == "Qwen/Qwen3-Embedding-0.6B"
            mock_setup.assert_called_once()

    def test_embedding_model_setup_success(self, mock_settings):
        """Test successful embedding model setup"""
        # Given valid model configuration
        from src.services.ai_service import AIService

        # Mock tokenizer and model with eval method
        mock_tokenizer = Mock(spec=AutoTokenizer)
        mock_model = Mock(spec=AutoModel)
        mock_model.eval = Mock()

        with patch(
            "src.services.ai_service.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ):
            with patch(
                "src.services.ai_service.AutoModel.from_pretrained",
                return_value=mock_model,
            ):
                # When setting up embedding model
                ai_service = AIService()

                # Then model should be loaded and set to evaluation mode
                assert ai_service.tokenizer == mock_tokenizer
                assert ai_service.embedding_model == mock_model
                mock_model.eval.assert_called_once()

    def test_embedding_model_setup_failure(self):
        """Test embedding model setup failure"""
        # Given invalid model configuration
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.embedding_model = "invalid-model"

            # Mock model loading failure
            with patch(
                "src.services.ai_service.AutoTokenizer.from_pretrained",
                side_effect=Exception("Model not found"),
            ):
                # When setting up embedding model fails
                with pytest.raises(Exception) as exc_info:
                    AIService()

                # Then should raise exception
                assert "Model not found" in str(exc_info.value)

    def test_generate_embedding_success(self, mock_settings):
        """Test successful embedding generation"""
        # Given AIService with mocked embedding model
        from src.services.ai_service import AIService

        # Mock tokenizer and model
        mock_tokenizer = Mock(spec=AutoTokenizer)
        mock_model = Mock(spec=AutoModel)
        mock_model.eval = Mock()
        mock_outputs = Mock()

        # Setup mock behavior - create a proper mock that can handle **inputs
        # We need to make the mock model callable and return mock_outputs when called
        mock_model.return_value = mock_outputs
        mock_outputs.last_hidden_state = Mock()
        mock_outputs.last_hidden_state.mean.return_value = Mock()
        mock_outputs.last_hidden_state.mean.return_value.squeeze.return_value = (
            torch.tensor([0.1, 0.2, 0.3])
        )

        # Mock the tokenizer to return a proper dictionary
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs

        with patch(
            "src.services.ai_service.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ):
            with patch(
                "src.services.ai_service.AutoModel.from_pretrained",
                return_value=mock_model,
            ):
                ai_service = AIService()

                # When generating embedding
                text = "Test text for embedding"
                embedding = ai_service.generate_embedding(text)

                # Then should return embedding vector
                assert len(embedding) == 3
                assert abs(embedding[0] - 0.1) < 0.001
                assert abs(embedding[1] - 0.2) < 0.001
                assert abs(embedding[2] - 0.3) < 0.001
                # The tokenizer should have been called with the text
                assert mock_tokenizer.called

    def test_generate_embedding_failure(self):
        """Test embedding generation failure"""
        # Given AIService with mocked embedding model
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

            # Mock tokenizer and model
            mock_tokenizer = Mock(spec=AutoTokenizer)
            mock_model = Mock(spec=AutoModel)
            mock_model.eval = Mock()

            with patch(
                "src.services.ai_service.AutoTokenizer.from_pretrained",
                return_value=mock_tokenizer,
            ):
                with patch(
                    "src.services.ai_service.AutoModel.from_pretrained",
                    return_value=mock_model,
                ):
                    ai_service = AIService()

                    # Mock embedding generation failure
                    mock_tokenizer.side_effect = Exception("Tokenization failed")

                    # When generating embedding fails
                    with pytest.raises(Exception) as exc_info:
                        ai_service.generate_embedding("test text")

                    # Then should raise exception
                    assert "Tokenization failed" in str(exc_info.value)

    @patch("src.services.ai_service.requests.post")
    def test_chat_completion_success(self, mock_post):
        """Test successful chat completion"""
        # Given AIService with configuration
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.deepseek_api_key = "test-api-key"
            mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.ai.max_tokens = 1000
            mock_settings.ai.temperature = 0.7
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

            with patch.object(AIService, "_setup_embedding_model"):
                ai_service = AIService()

                # Mock successful API response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Test response"}}],
                    "usage": {"total_tokens": 50},
                    "model": "deepseek-chat",
                }
                mock_post.return_value = mock_response

                # When calling chat completion
                messages = [{"role": "user", "content": "Hello"}]
                result = ai_service.chat_completion(messages)

                # Then should return API response
                assert result["choices"][0]["message"]["content"] == "Test response"
                assert result["usage"]["total_tokens"] == 50

                # Verify API call
                mock_post.assert_called_once_with(
                    "https://api.deepseek.com/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "max_tokens": 1000,
                        "temperature": 0.7,
                        "stream": False,
                    },
                    headers={
                        "Authorization": "Bearer test-api-key",
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )

    @patch("src.services.ai_service.requests.post")
    def test_chat_completion_with_system_prompt(self, mock_post):
        """Test chat completion with system prompt"""
        # Given AIService with configuration
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.deepseek_api_key = "test-api-key"
            mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.ai.max_tokens = 1000
            mock_settings.ai.temperature = 0.7
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

            with patch.object(AIService, "_setup_embedding_model"):
                ai_service = AIService()

                # Mock successful API response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Test response"}}],
                    "usage": {"total_tokens": 50},
                }
                mock_post.return_value = mock_response

                # When calling chat completion with system prompt
                messages = [{"role": "user", "content": "Hello"}]
                system_prompt = "You are a helpful assistant."
                ai_service.chat_completion(messages, system_prompt)

                # Then system prompt should be added to messages
                expected_messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"},
                ]

                call_args = mock_post.call_args
                assert call_args[1]["json"]["messages"] == expected_messages

    @patch("src.services.ai_service.requests.post")
    def test_chat_completion_api_error(self, mock_post):
        """Test chat completion with API error"""
        # Given AIService with configuration
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.deepseek_api_key = "test-api-key"
            mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.ai.max_tokens = 1000
            mock_settings.ai.temperature = 0.7
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

            with patch.object(AIService, "_setup_embedding_model"):
                ai_service = AIService()

                # Mock API error response
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.text = "Bad request"
                mock_post.return_value = mock_response

                # When calling chat completion with API error
                messages = [{"role": "user", "content": "Hello"}]
                with pytest.raises(Exception) as exc_info:
                    ai_service.chat_completion(messages)

                # Then should raise exception
                assert "API request failed: 400" in str(exc_info.value)

    @patch("src.services.ai_service.requests.post")
    def test_chat_completion_timeout(self, mock_post):
        """Test chat completion timeout"""
        # Given AIService with configuration
        from src.services.ai_service import AIService

        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.ai.deepseek_api_key = "test-api-key"
            mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.ai.max_tokens = 1000
            mock_settings.ai.temperature = 0.7
            mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

            with patch.object(AIService, "_setup_embedding_model"):
                ai_service = AIService()

                # Mock timeout
                mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

                # When calling chat completion with timeout
                messages = [{"role": "user", "content": "Hello"}]
                with pytest.raises(requests.exceptions.Timeout) as exc_info:
                    ai_service.chat_completion(messages)

                # Then should raise timeout exception
                assert "Request timed out" in str(exc_info.value)

    def test_generate_government_guidance(self, mock_settings):
        """Test government guidance generation"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response
            mock_response = {
                "choices": [{"message": {"content": "Government guidance response"}}],
                "usage": {"total_tokens": 100},
                "model": "deepseek-chat",
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When generating government guidance
                user_query = "How to apply for passport?"
                context_documents = [
                    {
                        "title": "Passport Requirements",
                        "content": "Requirements content...",
                    },
                    {
                        "title": "Application Process",
                        "content": "Process content...",
                    },
                ]
                conversation_history = [
                    {"role": "user", "content": "Previous question"},
                    {"role": "assistant", "content": "Previous answer"},
                ]

                result = ai_service.generate_government_guidance(
                    user_query, context_documents, conversation_history
                )

                # Then should return formatted guidance
                assert result["response"] == "Government guidance response"
                assert result["usage"]["total_tokens"] == 100
                assert result["model"] == "deepseek-chat"
                assert result["context_documents_used"] == 2

    def test_explain_technical_term(self, mock_settings):
        """Test technical term explanation"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response
            mock_response = {
                "choices": [{"message": {"content": "Technical term explanation"}}]
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When explaining technical term
                term = "Visa Application"
                context = "Applying for travel document"
                explanation = ai_service.explain_technical_term(term, context)

                # Then should return explanation
                assert explanation == "Technical term explanation"

    def test_generate_navigation_suggestions(self, mock_settings):
        """Test navigation suggestions generation"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response with bullet points
            mock_response = {
                "choices": [
                    {
                        "message": {
                            "content": """
- Check passport requirements
- Make online appointment
- Visit service location
- Submit required documents
                """
                        }
                    }
                ]
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When generating navigation suggestions
                current_context = "User wants to apply for passport"
                available_services = ["Passport", "Visa", "ID Card"]
                suggestions = ai_service.generate_navigation_suggestions(
                    current_context, available_services
                )

                # Then should return parsed suggestions
                assert len(suggestions) == 4
                assert suggestions[0]["label"] == "Check passport requirements"
                assert suggestions[0]["action_type"] == "related"
                assert suggestions[1]["label"] == "Make online appointment"

    def test_generate_navigation_suggestions_with_numbered_list(self, mock_settings):
        """Test navigation suggestions with numbered list"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response with numbered list
            mock_response = {
                "choices": [
                    {
                        "message": {
                            "content": """
1. Check passport requirements
2. Make online appointment
3. Visit service location
                """
                        }
                    }
                ]
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When generating navigation suggestions
                suggestions = ai_service.generate_navigation_suggestions(
                    "test context", ["test service"]
                )

                # Then should return parsed suggestions without numbers
                assert len(suggestions) == 3
                assert suggestions[0]["label"] == "Check passport requirements"
                assert suggestions[1]["label"] == "Make online appointment"

    def test_validate_response_quality_success(self, mock_settings):
        """Test response quality validation"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response with scores
            mock_response = {
                "choices": [
                    {
                        "message": {
                            "content": """
Accuracy: 4
Completeness: 5
Clarity: 4
Helpfulness: 5
Feedback: Good response overall
                """
                        }
                    }
                ]
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When validating response quality
                user_query = "How to apply for passport?"
                assistant_response = "Step by step guidance..."
                scores = ai_service.validate_response_quality(
                    user_query, assistant_response
                )

                # Then should return parsed scores
                assert scores["accuracy"] == 4
                assert scores["completeness"] == 5
                assert scores["clarity"] == 4
                assert scores["helpfulness"] == 5
                assert scores["feedback"] == "Good response overall"
                assert scores["overall"] == 4.5  # (4+5+4+5)/4

    def test_validate_response_quality_parsing_fallback(self, mock_settings):
        """Test response quality validation with parsing fallback"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion response with invalid format
            mock_response = {
                "choices": [{"message": {"content": "Invalid format response"}}]
            }

            with patch.object(
                ai_service, "chat_completion", return_value=mock_response
            ):
                # When validating response quality with invalid format
                scores = ai_service.validate_response_quality(
                    "test query", "test response"
                )

                # Then should return default scores
                assert scores["overall"] == 3

    def test_validate_response_quality_error_handling(self, mock_settings):
        """Test response quality validation error handling"""
        # Given AIService with mocked chat completion
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock chat completion failure
            with patch.object(
                ai_service, "chat_completion", side_effect=Exception("API error")
            ):
                # When validating response quality fails
                scores = ai_service.validate_response_quality(
                    "test query", "test response"
                )

                # Then should return default scores with error
                assert scores["overall"] == 3
                assert "error" in scores
                assert "API error" in scores["error"]

    @patch("src.services.ai_service.requests.post")
    def test_chat_completion_with_custom_parameters(self, mock_post, mock_settings):
        """Test chat completion with custom max_tokens and temperature"""
        # Given AIService with configuration
        from src.services.ai_service import AIService

        with patch.object(AIService, "_setup_embedding_model"):
            ai_service = AIService()

            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 50},
            }
            mock_post.return_value = mock_response

            # When calling chat completion with custom parameters
            messages = [{"role": "user", "content": "Hello"}]
            ai_service.chat_completion(messages, max_tokens=500, temperature=0.5)

            # Then custom parameters should be used
            call_args = mock_post.call_args
            assert call_args[1]["json"]["max_tokens"] == 500
            assert call_args[1]["json"]["temperature"] == 0.5
