"""
Unit tests for SearchService navigation functionality
"""

import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.models.embeddings import SearchResult
from src.services.search_service import SearchService


class TestSearchServiceNavigation:
    """Test navigation-related functionality in SearchService"""

    def setup_method(self):
        """Set up test fixtures"""
        # Mock all services to avoid external dependencies
        self.mock_embedding_service = MagicMock()
        self.mock_ai_service = MagicMock()
        self.mock_bm25_service = MagicMock()

        # Patch all service initializations
        with patch(
            "src.services.search_service.EmbeddingService",
            return_value=self.mock_embedding_service,
        ), patch(
            "src.services.search_service.AIService", return_value=self.mock_ai_service
        ), patch(
            "src.services.search_service.BM25Service",
            return_value=self.mock_bm25_service,
        ):
            self.search_service = SearchService()

    @patch("src.services.search_service.DataService")
    @patch("src.services.search_service.AIService")
    def test_generate_dynamic_navigation_options_with_search_results(
        self, mock_ai_service, mock_data_service
    ):
        """Test generating navigation options from search results"""
        # Mock search results
        search_results = [
            SearchResult(
                document_id=uuid.uuid4(),
                document_title="Hong Kong Passport Requirements",
                document_content="",
                source_url="https://immd.gov.hk/passport",
                similarity_score=0.95,
                metadata={"category": "passport"},
            ),
            SearchResult(
                document_id=uuid.uuid4(),
                document_title="Passport Application Process",
                document_content="",
                source_url="https://immd.gov.hk/apply",
                similarity_score=0.88,
                metadata={"category": "application"},
            ),
        ]

        # Mock conversation context
        conversation_context = {
            "current_query": "passport requirements",
            "current_service_category_id": None,
        }

        # Mock AI service to return empty suggestions
        mock_ai_service.return_value.generate_navigation_suggestions.return_value = []

        # Generate navigation options
        navigation_options = self.search_service.generate_dynamic_navigation_options(
            conversation_context, search_results
        )

        # Verify results
        assert len(navigation_options) == 2  # One for each search result
        assert (
            navigation_options[0]["label"]
            == "Learn more about Hong Kong Passport Requirements"
        )
        assert navigation_options[0]["action_type"] == "explain"
        assert navigation_options[0]["target_url"] == "https://immd.gov.hk/passport"

    @patch("src.services.search_service.DataService")
    @patch("src.services.search_service.AIService")
    def test_generate_navigation_options_with_service_category(
        self, mock_ai_service, mock_data_service
    ):
        """Test generating navigation options with service category"""
        # Mock conversation context with service category
        conversation_context = {
            "current_query": "passport",
            "current_service_category_id": "category-uuid",
        }

        # Mock data service to return category options
        mock_data_service_instance = Mock()
        mock_data_service.return_value.__enter__.return_value = (
            mock_data_service_instance
        )

        mock_navigation_options = [
            Mock(
                label="Check Requirements",
                action_type="navigate",
                target_url="https://immd.gov.hk/requirements",
                description="Check passport requirements",
                priority=1,
            ),
            Mock(
                label="Make Appointment",
                action_type="external",
                target_url="https://immd.gov.hk/appointment",
                description="Schedule passport appointment",
                priority=2,
            ),
        ]
        mock_data_service_instance.get_navigation_options_by_category.return_value = (
            mock_navigation_options
        )

        # Mock AI service
        mock_ai_service.return_value.generate_navigation_suggestions.return_value = []

        # Generate navigation options
        navigation_options = self.search_service.generate_dynamic_navigation_options(
            conversation_context, []
        )

        # Verify results
        assert len(navigation_options) == 2
        assert navigation_options[0]["label"] == "Check Requirements"
        assert navigation_options[0]["action_type"] == "navigate"
        assert navigation_options[1]["label"] == "Make Appointment"
        assert navigation_options[1]["action_type"] == "external"

    def test_generate_navigation_options_with_ai_suggestions(self):
        """Test generating navigation options with AI suggestions"""
        # Mock conversation context
        conversation_context = {
            "current_query": "passport renewal",
            "current_service_category_id": None,
        }

        # Mock AI service to return suggestions
        mock_ai_suggestions = [
            {
                "label": "Check Renewal Eligibility",
                "action_type": "explain",
                "priority": 3,
            },
            {"label": "Find Renewal Centers", "action_type": "navigate", "priority": 3},
        ]
        self.mock_ai_service.generate_navigation_suggestions.return_value = (
            mock_ai_suggestions
        )

        # Generate navigation options
        navigation_options = self.search_service.generate_dynamic_navigation_options(
            conversation_context, []
        )

        # Verify AI suggestions are included
        assert len(navigation_options) == 2
        assert navigation_options[0]["label"] == "Check Renewal Eligibility"
        assert navigation_options[1]["label"] == "Find Renewal Centers"

    def test_filter_navigation_options_by_category(self):
        """Test filtering navigation options by service category"""
        # Mock navigation options
        navigation_options = [
            {"label": "Option 1", "action_type": "explain", "priority": 5},
            {"label": "Option 2", "action_type": "navigate", "priority": 3},
        ]

        # Filter options (currently returns all options)
        filtered_options = self.search_service.filter_navigation_options_by_category(
            navigation_options, "category-uuid"
        )

        # Verify all options are returned (placeholder implementation)
        assert len(filtered_options) == 2
        assert filtered_options == navigation_options

    def test_add_external_url_handling_valid_url(self):
        """Test handling valid external URLs"""
        # Test with government URL
        url = "https://hongkong.gov.hk/appointment"
        result = self.search_service.add_external_url_handling(url)

        assert result["url"] == url
        assert result["is_government_url"] == True
        assert result["requires_validation"] == False
        assert result["handling_type"] == "external_redirect"

    def test_add_external_url_handling_invalid_url(self):
        """Test handling invalid external URLs"""
        # Test with invalid URL
        url = "invalid-url"

        with pytest.raises(ValueError, match="Invalid URL format"):
            self.search_service.add_external_url_handling(url)

    def test_add_external_url_handling_non_government_url(self):
        """Test handling non-government external URLs"""
        # Test with non-government URL
        url = "https://example.com/appointment"
        result = self.search_service.add_external_url_handling(url)

        assert result["url"] == url
        assert result["is_government_url"] == False
        assert result["requires_validation"] == True

    def test_navigation_option_priority_ordering(self):
        """Test that navigation options are sorted by priority"""
        # Mock conversation context and search results
        conversation_context = {
            "current_query": "test",
            "current_service_category_id": None,
        }

        search_results = [
            SearchResult(
                document_id=uuid.uuid4(),
                document_title="High Priority",
                document_content="",
                source_url="https://example.com/high",
                similarity_score=0.95,
                metadata={"priority": 1},
            ),
            SearchResult(
                document_id=uuid.uuid4(),
                document_title="Low Priority",
                document_content="",
                source_url="https://example.com/low",
                similarity_score=0.88,
                metadata={"priority": 5},
            ),
        ]

        # Generate navigation options
        navigation_options = self.search_service.generate_dynamic_navigation_options(
            conversation_context, search_results
        )

        # Verify options are sorted by priority (lower number = higher priority)
        priorities = [option.get("priority", 5) for option in navigation_options]
        assert priorities == sorted(priorities)

    @patch("src.services.search_service.DataService")
    @patch("src.services.search_service.AIService")
    def test_empty_navigation_options_on_error(
        self, mock_ai_service, mock_data_service
    ):
        """Test that empty list is returned on error"""
        # Mock conversation context
        conversation_context = {
            "current_query": "test",
            "current_service_category_id": "category-uuid",
        }

        # Mock data service to raise exception
        mock_data_service_instance = Mock()
        mock_data_service.return_value.__enter__.return_value = (
            mock_data_service_instance
        )
        mock_data_service_instance.get_navigation_options_by_category.side_effect = (
            Exception("Database error")
        )

        # Mock AI service to raise exception
        mock_ai_service.return_value.generate_navigation_suggestions.side_effect = (
            Exception("AI error")
        )

        # Generate navigation options
        navigation_options = self.search_service.generate_dynamic_navigation_options(
            conversation_context, []
        )

        # Verify empty list is returned on error
        assert navigation_options == []
