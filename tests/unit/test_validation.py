"""
Unit tests for validation utilities
"""

import pytest
from src.utils.validation import (
    URLValidator,
    NavigationOptionValidator,
    ServiceCategoryValidator,
    validate_and_sanitize_input
)


class TestURLValidator:
    """Test URL validation functionality"""

    def test_validate_external_url_valid_government_url(self):
        """Test validation of valid government URL"""
        url = "https://immd.gov.hk/passport"
        result = URLValidator.validate_external_url(url)

        assert result["valid"] == True
        assert result["url"] == url
        assert result["is_government_url"] == True
        assert result["domain"] == "immd.gov.hk"
        assert result["protocol"] == "https"

    def test_validate_external_url_valid_non_government_url(self):
        """Test validation of valid non-government URL"""
        url = "https://example.com/appointment"
        result = URLValidator.validate_external_url(url)

        assert result["valid"] == True
        assert result["url"] == url
        assert result["is_government_url"] == False
        assert result["domain"] == "example.com"

    def test_validate_external_url_invalid_format(self):
        """Test validation of invalid URL format"""
        url = "not-a-url"
        result = URLValidator.validate_external_url(url)

        assert result["valid"] == False
        assert "URL must start with http:// or https://" in result["error"]

    def test_validate_external_url_missing_hostname(self):
        """Test validation of URL with missing hostname"""
        url = "https://"
        result = URLValidator.validate_external_url(url)

        assert result["valid"] == False
        assert "missing hostname" in result["error"]

    def test_validate_external_url_http_security_warning(self):
        """Test security warning for HTTP URLs"""
        url = "http://example.com"
        result = URLValidator.validate_external_url(url)

        assert result["valid"] == True
        assert "HTTP protocol is not secure" in result["security_issues"][0]

    def test_validate_appointment_url_valid(self):
        """Test validation of valid appointment URL"""
        url = "https://immd.gov.hk/appointment/schedule"
        result = URLValidator.validate_appointment_url(url)

        assert result["valid"] == True
        assert result["is_appointment_system"] == True
        assert result["appointment_indicators"]["appointment"] == True

    def test_validate_appointment_url_not_appointment_system(self):
        """Test validation of URL that is not an appointment system"""
        url = "https://immd.gov.hk/about"
        result = URLValidator.validate_appointment_url(url)

        assert result["valid"] == False
        assert "does not appear to be an appointment system" in result["error"]

    def test_validate_appointment_url_invalid_format(self):
        """Test validation of invalid appointment URL format"""
        url = "invalid-url"
        result = URLValidator.validate_appointment_url(url)

        assert result["valid"] == False
        assert "URL must start with http:// or https://" in result["error"]


class TestNavigationOptionValidator:
    """Test navigation option validation"""

    def test_validate_navigation_option_valid(self):
        """Test validation of valid navigation option"""
        option = {
            "label": "Check Requirements",
            "action_type": "explain",
            "target_url": "https://immd.gov.hk/requirements",
            "priority": 1
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == True
        assert len(result["issues"]) == 0

    def test_validate_navigation_option_missing_required_fields(self):
        """Test validation of navigation option with missing required fields"""
        option = {
            "target_url": "https://example.com"
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == False
        assert "Missing required field: label" in result["issues"]
        assert "Missing required field: action_type" in result["issues"]

    def test_validate_navigation_option_invalid_action_type(self):
        """Test validation of navigation option with invalid action type"""
        option = {
            "label": "Test Option",
            "action_type": "invalid_action",
            "priority": 5
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == False
        assert "Invalid action_type" in result["issues"][0]

    def test_validate_navigation_option_invalid_url(self):
        """Test validation of navigation option with invalid URL"""
        option = {
            "label": "Test Option",
            "action_type": "external",
            "target_url": "invalid-url",
            "priority": 5
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == False
        assert "Invalid target URL" in result["issues"][0]

    def test_validate_navigation_option_long_label_warning(self):
        """Test warning for very long label"""
        long_label = "A" * 150
        option = {
            "label": long_label,
            "action_type": "explain",
            "priority": 5
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == True
        assert "Label is very long" in result["warnings"][0]

    def test_validate_navigation_option_invalid_priority(self):
        """Test warning for invalid priority value"""
        option = {
            "label": "Test Option",
            "action_type": "explain",
            "priority": 15
        }
        result = NavigationOptionValidator.validate_navigation_option(option)

        assert result["valid"] == True
        assert "Priority should be between 1 and 10" in result["warnings"][0]


class TestServiceCategoryValidator:
    """Test service category validation"""

    def test_validate_service_category_valid(self):
        """Test validation of valid service category"""
        category = {
            "name": "Hong Kong Passport Services",
            "description": "Information about Hong Kong passport applications and renewals",
            "official_source_url": "https://immd.gov.hk/passport"
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == True
        assert len(result["issues"]) == 0

    def test_validate_service_category_missing_name(self):
        """Test validation of service category with missing name"""
        category = {
            "description": "Some description",
            "official_source_url": "https://example.com"
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == False
        assert "Missing required field: name" in result["issues"]

    def test_validate_service_category_empty_name(self):
        """Test validation of service category with empty name"""
        category = {
            "name": "",
            "description": "Some description"
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == False
        assert "Name cannot be empty" in result["issues"]

    def test_validate_service_category_long_name(self):
        """Test validation of service category with very long name"""
        long_name = "A" * 300
        category = {
            "name": long_name,
            "description": "Some description"
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == False
        assert "exceeds maximum length" in result["issues"][0]

    def test_validate_service_category_non_government_url_warning(self):
        """Test warning for non-government official source URL"""
        category = {
            "name": "Test Category",
            "official_source_url": "https://example.com/info"
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == True
        assert "not from a recognized government domain" in result["warnings"][0]

    def test_validate_service_category_long_description_warning(self):
        """Test warning for very long description"""
        long_description = "A" * 1200
        category = {
            "name": "Test Category",
            "description": long_description
        }
        result = ServiceCategoryValidator.validate_service_category(category)

        assert result["valid"] == True
        assert "Description is very long" in result["warnings"][0]


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_validate_and_sanitize_input_valid(self):
        """Test validation of valid input"""
        input_text = "Hello, I need help with passport renewal"
        result = validate_and_sanitize_input(input_text)

        assert result["valid"] == True
        assert result["sanitized"] == input_text
        assert result["length"] == len(input_text)

    def test_validate_and_sanitize_input_empty(self):
        """Test validation of empty input"""
        input_text = ""
        result = validate_and_sanitize_input(input_text)

        assert result["valid"] == False
        assert "Input cannot be empty" in result["error"]

    def test_validate_and_sanitize_input_whitespace_only(self):
        """Test validation of whitespace-only input"""
        input_text = "   \n\t  "
        result = validate_and_sanitize_input(input_text)

        assert result["valid"] == False
        assert "Input cannot be empty" in result["error"]

    def test_validate_and_sanitize_input_too_long(self):
        """Test validation of input that exceeds maximum length"""
        long_input = "A" * 1500
        result = validate_and_sanitize_input(long_input, max_length=1000)

        assert result["valid"] == False
        assert "exceeds maximum length" in result["error"]
        assert len(result["sanitized"]) == 1000

    def test_validate_and_sanitize_input_harmful_content(self):
        """Test validation of input with potentially harmful content"""
        harmful_input = "Hello <script>alert('xss')</script> world"
        result = validate_and_sanitize_input(harmful_input)

        assert result["valid"] == False
        assert "potentially harmful content" in result["error"]
        assert "<script>" not in result["sanitized"]

    def test_validate_and_sanitize_input_javascript_protocol(self):
        """Test validation of input with JavaScript protocol"""
        harmful_input = "Click here: javascript:alert('xss')"
        result = validate_and_sanitize_input(harmful_input)

        assert result["valid"] == False
        assert "potentially harmful content" in result["error"]
        assert "javascript:" not in result["sanitized"]

    def test_validate_and_sanitize_input_event_handlers(self):
        """Test validation of input with event handlers"""
        harmful_input = "<img src=x onerror=alert('xss')>"
        result = validate_and_sanitize_input(harmful_input)

        assert result["valid"] == False
        assert "potentially harmful content" in result["error"]
        assert "onerror" not in result["sanitized"]