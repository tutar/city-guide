"""
Unit tests for Chainlit components
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.chainlit.components.chat_interface import AccessibleChatInterface
from src.chainlit.components.search_results import SearchResultsComponent


class TestSearchResultsComponent:
    """Test search results component functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.search_component = SearchResultsComponent()

    def test_format_source_attribution_government_source(self):
        """Test formatting source attribution for government sources"""
        result = {
            "source_url": "https://immd.gov.hk/passport",
            "metadata": {
                "source_type": "government",
                "is_verified": True,
                "last_updated": "2024-01-15",
            },
        }

        attribution = self.search_component._format_source_attribution(result)

        assert "Official Government Website" in attribution
        assert "✅ Verified" in attribution
        assert "Last Updated:** 2024-01-15" in attribution

    def test_format_source_attribution_unverified_source(self):
        """Test formatting source attribution for unverified sources"""
        result = {
            "source_url": "https://example.com/info",
            "metadata": {"source_type": "information", "is_verified": False},
        }

        attribution = self.search_component._format_source_attribution(result)

        assert "Information Portal" in attribution
        assert "⚠️ Unverified" in attribution

    def test_extract_snippet_with_query_match(self):
        """Test snippet extraction when query matches content"""
        content = "This is a long text about passport requirements for Hong Kong residents. The requirements include valid identification and proof of address."
        query = "passport requirements"

        snippet = self.search_component._extract_snippet(content, query)

        assert "passport requirements" in snippet.lower()
        assert len(snippet) <= 200 + 3  # Account for ellipsis

    def test_extract_snippet_no_query_match(self):
        """Test snippet extraction when query doesn't match content"""
        content = "This is a long text about visa applications for foreign nationals."
        query = "passport"

        snippet = self.search_component._extract_snippet(content, query)

        assert snippet.startswith("This is a long text")
        assert len(snippet) <= 200 + 3

    def test_extract_domain_valid_url(self):
        """Test domain extraction from valid URL"""
        url = "https://immd.gov.hk/passport/requirements"
        domain = self.search_component._extract_domain(url)

        assert domain == "immd.gov.hk"

    def test_extract_domain_invalid_url(self):
        """Test domain extraction from invalid URL"""
        url = "not-a-valid-url"
        domain = self.search_component._extract_domain(url)

        # When URL parsing fails, it returns the original URL
        assert domain == "not-a-valid-url"

    @pytest.mark.asyncio
    @patch("src.chainlit.components.search_results.cl.Message")
    async def test_display_step_by_step_guidance(self, mock_message):
        """Test displaying step-by-step guidance"""
        steps = [
            {
                "title": "Check Eligibility",
                "description": "Verify you meet the basic requirements for passport application.",
                "requirements": ["Valid identification", "Proof of address"],
                "estimated_time": "5 minutes",
                "cost": "Free",
                "source_url": "https://immd.gov.hk/eligibility",
            },
            {
                "title": "Gather Documents",
                "description": "Collect all required documents for the application.",
                "requirements": ["Passport photos", "Application form"],
                "estimated_time": "30 minutes",
                "cost": "HK$370",
                "source_url": "https://immd.gov.hk/documents",
            },
        ]

        # Mock the async send method
        mock_message_instance = AsyncMock()
        mock_message.return_value = mock_message_instance

        await self.search_component.display_step_by_step_guidance(
            steps, "Hong Kong Passport"
        )

        # Verify message was created
        assert mock_message.called
        message_content = mock_message.call_args[1]["content"]

        assert "Step-by-Step Guide: Hong Kong Passport" in message_content
        assert "Check Eligibility" in message_content
        assert "Gather Documents" in message_content
        assert "immd.gov.hk" in message_content

    def test_get_search_analytics_empty_history(self):
        """Test search analytics with empty history"""
        analytics = self.search_component.get_search_analytics()

        assert analytics["total_searches"] == 0
        assert analytics["average_results"] == 0
        assert analytics["success_rate"] == 0

    def test_get_search_analytics_with_history(self):
        """Test search analytics with search history"""
        # Add some search history
        self.search_component.search_history = [
            {"query": "passport", "result_count": 5},
            {"query": "visa", "result_count": 3},
            {"query": "unknown", "result_count": 0},
        ]

        analytics = self.search_component.get_search_analytics()

        assert analytics["total_searches"] == 3
        assert analytics["average_results"] == (5 + 3 + 0) / 3
        assert analytics["success_rate"] == (2 / 3) * 100  # 2 out of 3 had results
        assert "passport" in analytics["recent_queries"]


class TestAccessibleChatInterface:
    """Test accessible chat interface functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.chat_interface = AccessibleChatInterface()

    def test_format_content_for_accessibility_short_message(self):
        """Test formatting short messages for accessibility"""
        content = "Hello, how can I help you?"
        author = "Assistant"

        formatted = self.chat_interface._format_content_for_accessibility(
            content, author
        )

        assert formatted == "**Assistant:** Hello, how can I help you?"

    def test_format_content_for_accessibility_long_message(self):
        """Test formatting long messages for accessibility"""
        content = "This is a very long message that contains multiple lines of text and should be formatted with proper structure for better screen reader experience."
        author = "Assistant"

        formatted = self.chat_interface._format_content_for_accessibility(
            content, author
        )

        assert formatted.startswith("**Assistant:**\n\n")
        assert content in formatted

    def test_get_accessibility_report(self):
        """Test generating accessibility report"""
        # Add some message history
        self.chat_interface.message_history = [
            {"content": "Hello", "author": "User", "type": "info"},
            {"content": "Hi there", "author": "Assistant", "type": "info"},
            {"content": "Error occurred", "author": "System", "type": "error"},
        ]

        report = self.chat_interface.get_accessibility_report()

        assert report["total_messages"] == 3
        assert report["message_types"]["info"] == 2
        assert report["message_types"]["error"] == 1
        assert "Screen reader announcements" in report["accessibility_features"]

    @pytest.mark.asyncio
    @patch("src.chainlit.components.chat_interface.search_results")
    async def test_display_step_by_step_guidance(self, mock_search_results):
        """Test displaying step-by-step guidance through chat interface"""
        steps = [
            {
                "title": "Test Step",
                "description": "Test description",
                "source_url": "https://example.com",
            }
        ]

        mock_message = AsyncMock()
        mock_search_results.display_step_by_step_guidance = AsyncMock(
            return_value=mock_message
        )

        result = await self.chat_interface.display_step_by_step_guidance(
            steps, "Test Service"
        )

        # Verify search results component was called
        mock_search_results.display_step_by_step_guidance.assert_called_once_with(
            steps, "Test Service"
        )
        assert result == mock_message

    @pytest.mark.asyncio
    @patch("src.chainlit.components.chat_interface.search_results")
    @patch(
        "src.chainlit.components.chat_interface.AccessibleChatInterface.update_aria_live_region"
    )
    async def test_display_search_results(self, mock_update_aria, mock_search_results):
        """Test displaying search results through chat interface"""
        results = [
            {
                "title": "Test Result",
                "content": "Test content",
                "source_url": "https://example.com",
            }
        ]

        mock_message = AsyncMock()
        mock_search_results.display_search_results = AsyncMock(
            return_value=mock_message
        )

        result = await self.chat_interface.display_search_results(
            results, "test query", True
        )

        # Verify search results component was called
        mock_search_results.display_search_results.assert_called_once_with(
            results, "test query", True
        )
        # Verify aria-live region was updated
        mock_update_aria.assert_called_once()
        assert result == mock_message

    def test_should_use_aria_live_different_message_types(self):
        """Test determining appropriate aria-live values for different message types"""
        # This would test the ScreenReaderUtils.should_use_aria_live method
        # if it were accessible from the chat interface
        pass
