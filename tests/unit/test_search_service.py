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

    def test_add_external_url_handling_valid_url(self):
        """Test handling valid external URLs"""
        # Test with government URL
        url = "https://hongkong.gov.hk/appointment"
        result = self.search_service.add_external_url_handling(url)

        assert result["url"] == url
        assert result["is_government_url"] is True
        assert result["requires_validation"] is False
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
        assert result["is_government_url"] is False
        assert result["requires_validation"] is True
