"""
Simplified unit tests for AI service and Deepseek API integration
"""

from unittest.mock import Mock, patch


@patch("src.services.ai_service.settings")
@patch("src.services.ai_service.AutoTokenizer.from_pretrained")
@patch("src.services.ai_service.AutoModel.from_pretrained")
def test_ai_service_initialization(mock_model, mock_tokenizer, mock_settings):
    """Test AIService initialization with configuration"""
    # Mock settings
    mock_settings.ai.deepseek_api_key = "test-api-key"
    mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
    mock_settings.ai.max_tokens = 1000
    mock_settings.ai.temperature = 0.7
    mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

    # Mock tokenizer and model
    mock_tokenizer.return_value = Mock()
    mock_model.return_value = Mock()

    # Import AIService after mocking
    from src.services.ai_service import AIService

    # When initializing AIService
    ai_service = AIService()

    # Then service should be initialized with correct configuration
    assert ai_service.deepseek_api_key == "test-api-key"
    assert ai_service.deepseek_base_url == "https://api.deepseek.com"
    assert ai_service.max_tokens == 1000
    assert ai_service.temperature == 0.7
    assert ai_service.embedding_model_name == "Qwen/Qwen3-Embedding-0.6B"


@patch("src.services.ai_service.settings")
@patch("src.services.ai_service.AutoTokenizer.from_pretrained")
@patch("src.services.ai_service.AutoModel.from_pretrained")
@patch("src.services.ai_service.requests.post")
def test_chat_completion_success(mock_post, mock_model, mock_tokenizer, mock_settings):
    """Test successful chat completion"""
    # Mock settings
    mock_settings.ai.deepseek_api_key = "test-api-key"
    mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
    mock_settings.ai.max_tokens = 1000
    mock_settings.ai.temperature = 0.7
    mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

    # Mock tokenizer and model
    mock_tokenizer.return_value = Mock()
    mock_model.return_value = Mock()

    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 50},
        "model": "deepseek-chat",
    }
    mock_post.return_value = mock_response

    # Import AIService after mocking
    from src.services.ai_service import AIService

    # When calling chat completion
    ai_service = AIService()
    messages = [{"role": "user", "content": "Hello"}]
    result = ai_service.chat_completion(messages)

    # Then should return API response
    assert result["choices"][0]["message"]["content"] == "Test response"
    assert result["usage"]["total_tokens"] == 50


@patch("src.services.ai_service.settings")
@patch("src.services.ai_service.AutoTokenizer.from_pretrained")
@patch("src.services.ai_service.AutoModel.from_pretrained")
def test_generate_government_guidance(mock_model, mock_tokenizer, mock_settings):
    """Test government guidance generation"""
    # Mock settings
    mock_settings.ai.deepseek_api_key = "test-api-key"
    mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
    mock_settings.ai.max_tokens = 1000
    mock_settings.ai.temperature = 0.7
    mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

    # Mock tokenizer and model
    mock_tokenizer.return_value = Mock()
    mock_model.return_value = Mock()

    # Import AIService after mocking
    from src.services.ai_service import AIService

    # Mock chat completion response
    mock_response = {
        "choices": [{"message": {"content": "Government guidance response"}}],
        "usage": {"total_tokens": 100},
        "model": "deepseek-chat",
    }

    ai_service = AIService()
    with patch.object(ai_service, "chat_completion", return_value=mock_response):
        # When generating government guidance
        user_query = "How to apply for passport?"
        context_documents = [
            {
                "document_title": "Passport Requirements",
                "document_content": "Requirements content...",
            },
            {
                "document_title": "Application Process",
                "document_content": "Process content...",
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


@patch("src.services.ai_service.settings")
@patch("src.services.ai_service.AutoTokenizer.from_pretrained")
@patch("src.services.ai_service.AutoModel.from_pretrained")
def test_explain_technical_term(mock_model, mock_tokenizer, mock_settings):
    """Test technical term explanation"""
    # Mock settings
    mock_settings.ai.deepseek_api_key = "test-api-key"
    mock_settings.ai.deepseek_base_url = "https://api.deepseek.com"
    mock_settings.ai.max_tokens = 1000
    mock_settings.ai.temperature = 0.7
    mock_settings.ai.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

    # Mock tokenizer and model
    mock_tokenizer.return_value = Mock()
    mock_model.return_value = Mock()

    # Import AIService after mocking
    from src.services.ai_service import AIService

    # Mock chat completion response
    mock_response = {
        "choices": [{"message": {"content": "Technical term explanation"}}]
    }

    ai_service = AIService()
    with patch.object(ai_service, "chat_completion", return_value=mock_response):
        # When explaining technical term
        term = "Visa Application"
        context = "Applying for travel document"
        explanation = ai_service.explain_technical_term(term, context)

        # Then should return explanation
        assert explanation == "Technical term explanation"
