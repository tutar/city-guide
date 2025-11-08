"""
Validation utilities for City Guide Smart Assistant
"""

import logging
import re
from typing import Any
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)


class URLValidator:
    """Validator for external URLs and appointment systems"""

    @staticmethod
    def validate_external_url(url: str) -> dict[str, Any]:
        """Validate external URL for appointment systems and other external services"""
        try:
            # Basic URL format validation
            if not url.startswith(("http://", "https://")):
                return {
                    "valid": False,
                    "error": "URL must start with http:// or https://",
                    "suggestion": "Please provide a valid URL starting with http:// or https://",
                }

            # Parse URL
            parsed = urlparse(url)

            # Check for empty hostname
            if not parsed.hostname:
                return {
                    "valid": False,
                    "error": "Invalid URL format - missing hostname",
                    "suggestion": "Please provide a complete URL with domain name",
                }

            # Validate government service URLs
            government_domains = [
                "gov.cn",
                "sz.gov.cn",
                "hongkong.gov.hk",
                "macau.gov.mo",
                "immd.gov.hk",
                "dsedt.gov.mo",
                "gov.hk",
                "gov.mo",
            ]

            is_government_url = any(
                domain in parsed.hostname.lower() for domain in government_domains
            )

            # Check for common appointment system patterns
            appointment_keywords = [
                "appointment",
                "booking",
                "reservation",
                "schedule",
                "apply",
            ]
            has_appointment_pattern = any(
                keyword in url.lower() for keyword in appointment_keywords
            )

            # Security checks
            security_issues = []
            if parsed.scheme == "http":
                security_issues.append(
                    "HTTP protocol is not secure - consider using HTTPS"
                )

            # Check for suspicious patterns
            suspicious_patterns = [
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP addresses
                r"localhost",
                r"127\.0\.0\.1",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, url):
                    security_issues.append(
                        f"URL contains suspicious pattern: {pattern}"
                    )

            return {
                "valid": True,
                "url": url,
                "is_government_url": is_government_url,
                "has_appointment_pattern": has_appointment_pattern,
                "security_issues": security_issues,
                "domain": parsed.hostname,
                "protocol": parsed.scheme,
            }

        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            return {
                "valid": False,
                "error": f"URL validation error: {str(e)}",
                "suggestion": "Please check the URL format and try again",
            }

    @staticmethod
    def validate_appointment_url(url: str) -> dict[str, Any]:
        """Special validation for appointment system URLs"""
        try:
            # First do basic URL validation
            basic_validation = URLValidator.validate_external_url(url)
            if not basic_validation["valid"]:
                return basic_validation

            # Additional appointment-specific checks
            appointment_indicators = {
                "secure_form": any(
                    pattern in url.lower() for pattern in ["form", "apply", "submit"]
                ),
                "calendar": any(
                    pattern in url.lower()
                    for pattern in ["calendar", "schedule", "timeslot"]
                ),
                "confirmation": any(
                    pattern in url.lower()
                    for pattern in ["confirm", "success", "thank"]
                ),
                "login_required": any(
                    pattern in url.lower() for pattern in ["login", "signin", "auth"]
                ),
                "appointment": any(
                    pattern in url.lower()
                    for pattern in ["appointment", "booking", "reservation"]
                ),
            }

            # Check for required appointment features
            has_appointment_features = (
                appointment_indicators["secure_form"]
                or appointment_indicators["calendar"]
                or appointment_indicators["confirmation"]
                or appointment_indicators["appointment"]
            )

            if not has_appointment_features:
                return {
                    "valid": False,
                    "error": "URL does not appear to be an appointment system",
                    "suggestion": "Please provide a URL that includes appointment, booking, or application features",
                }

            # Enhanced validation result
            validation_result = basic_validation
            validation_result["appointment_indicators"] = appointment_indicators
            validation_result["is_appointment_system"] = True

            return validation_result

        except Exception as e:
            logger.error(f"Appointment URL validation failed: {e}")
            return {
                "valid": False,
                "error": f"Appointment URL validation error: {str(e)}",
                "suggestion": "Please verify this is a valid appointment system URL",
            }


class NavigationOptionValidator:
    """Validator for navigation options"""

    @staticmethod
    def validate_navigation_option(option: dict[str, Any]) -> dict[str, Any]:
        """Validate navigation option structure and content"""
        try:
            issues = []
            warnings = []

            # Required fields
            required_fields = ["label", "action_type"]
            for field in required_fields:
                if field not in option:
                    issues.append(f"Missing required field: {field}")

            # Validate label
            if "label" in option:
                label = option["label"]
                if not label or not label.strip():
                    issues.append("Label cannot be empty")
                elif len(label) > 100:
                    warnings.append(
                        "Label is very long - consider shortening for better user experience"
                    )

            # Validate action type
            valid_action_types = ["explain", "navigate", "external", "search", "help"]
            if (
                "action_type" in option
                and option["action_type"] not in valid_action_types
            ):
                issues.append(
                    f"Invalid action_type: {option['action_type']}. Must be one of: {valid_action_types}"
                )

            # Validate URL if provided
            if "target_url" in option and option["target_url"]:
                url_validation = URLValidator.validate_external_url(
                    option["target_url"]
                )
                if not url_validation["valid"]:
                    issues.append(f"Invalid target URL: {url_validation['error']}")
                elif url_validation["security_issues"]:
                    warnings.extend(url_validation["security_issues"])

            # Validate priority
            if "priority" in option:
                priority = option["priority"]
                if not isinstance(priority, int):
                    issues.append("Priority must be an integer")
                elif priority < 1 or priority > 10:
                    warnings.append(
                        "Priority should be between 1 and 10 (1 = highest priority)"
                    )

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "suggestions": [
                    "Ensure labels are clear and concise",
                    "Use appropriate action types for the context",
                    "Validate all external URLs before use",
                ],
            }

        except Exception as e:
            logger.error(f"Navigation option validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": ["Please check the navigation option structure"],
            }


class ServiceCategoryValidator:
    """Validator for service categories"""

    @staticmethod
    def validate_service_category(category: dict[str, Any]) -> dict[str, Any]:
        """Validate service category structure and content"""
        try:
            issues = []
            warnings = []

            # Required fields
            required_fields = ["name"]
            for field in required_fields:
                if field not in category:
                    issues.append(f"Missing required field: {field}")

            # Validate name
            if "name" in category:
                name = category["name"]
                if not name or not name.strip():
                    issues.append("Name cannot be empty")
                elif len(name) > 255:
                    issues.append("Name exceeds maximum length of 255 characters")

            # Validate description
            if "description" in category and category["description"]:
                description = category["description"]
                if len(description) > 1000:
                    warnings.append(
                        "Description is very long - consider summarizing for better user experience"
                    )

            # Validate official source URL
            if "official_source_url" in category and category["official_source_url"]:
                url_validation = URLValidator.validate_external_url(
                    category["official_source_url"]
                )
                if not url_validation["valid"]:
                    issues.append(
                        f"Invalid official source URL: {url_validation['error']}"
                    )
                elif not url_validation["is_government_url"]:
                    warnings.append(
                        "Official source URL is not from a recognized government domain"
                    )

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "suggestions": [
                    "Use clear, descriptive names for service categories",
                    "Provide official government sources when available",
                    "Keep descriptions concise and informative",
                ],
            }

        except Exception as e:
            logger.error(f"Service category validation failed: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": ["Please check the service category structure"],
            }


# Utility functions for common validation tasks


def validate_and_sanitize_input(
    input_text: str, max_length: int = 1000
) -> dict[str, Any]:
    """Validate and sanitize user input"""
    try:
        if not input_text or not input_text.strip():
            return {"valid": False, "sanitized": "", "error": "Input cannot be empty"}

        # Trim whitespace
        sanitized = input_text.strip()

        # Check length
        if len(sanitized) > max_length:
            return {
                "valid": False,
                "sanitized": sanitized[:max_length],
                "error": f"Input exceeds maximum length of {max_length} characters",
            }

        # Check for potentially harmful patterns
        harmful_patterns = [
            r"<script[^>]*>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"on\w+\s*=",  # Event handlers
            r"data:text/html",  # Data URLs
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return {
                    "valid": False,
                    "sanitized": re.sub(pattern, "", sanitized, flags=re.IGNORECASE),
                    "error": "Input contains potentially harmful content",
                }

        return {"valid": True, "sanitized": sanitized, "length": len(sanitized)}

    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        return {"valid": False, "sanitized": "", "error": f"Validation error: {str(e)}"}
