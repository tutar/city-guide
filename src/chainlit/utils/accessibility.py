"""
Accessibility utilities for screen reader compatibility
"""

from typing import Any


class ScreenReaderUtils:
    """Utilities for screen reader compatibility"""

    @staticmethod
    def generate_aria_label(element_type: str, content: str, context: str = "") -> str:
        """Generate appropriate aria-label for elements"""

        labels = {
            "button": f"{content} button",
            "link": f"{content} link",
            "input": f"{content} input field",
            "message": f"Message: {content}",
            "navigation": f"Navigation: {content}",
            "error": f"Error: {content}",
            "success": f"Success: {content}",
        }

        base_label = labels.get(element_type, content)

        if context:
            return f"{base_label} - {context}"

        return base_label

    @staticmethod
    def get_aria_describedby(element_id: str) -> str:
        """Generate aria-describedby value"""
        return f"{element_id}-description"

    @staticmethod
    def should_use_aria_live(content_type: str) -> str:
        """Determine appropriate aria-live value"""

        live_regions = {
            "error": "assertive",
            "alert": "assertive",
            "success": "polite",
            "status": "polite",
            "info": "polite",
            "default": "off",
        }

        return live_regions.get(content_type, "off")

    @staticmethod
    def format_content_for_screen_reader(
        content: str, content_type: str = "info"
    ) -> str:
        """Format content for better screen reader experience"""

        # Remove excessive whitespace
        content = " ".join(content.split())

        # Add semantic cues based on content type
        if content_type == "error":
            return f"Error: {content}"
        elif content_type == "success":
            return f"Success: {content}"
        elif content_type == "warning":
            return f"Warning: {content}"

        return content

    @staticmethod
    def generate_role_attribute(element_type: str) -> str:
        """Generate appropriate ARIA role"""

        roles = {
            "button": "button",
            "link": "link",
            "textbox": "textbox",
            "navigation": "navigation",
            "main": "main",
            "complementary": "complementary",
            "contentinfo": "contentinfo",
            "alert": "alert",
            "status": "status",
            "dialog": "dialog",
        }

        return roles.get(element_type, "")


class ColorContrastChecker:
    """Utility for checking color contrast ratios"""

    @staticmethod
    def calculate_contrast_ratio(foreground: str, background: str) -> float:
        """Calculate contrast ratio between two colors"""
        # Simplified implementation
        # In production, this would use proper color contrast algorithms

        # Common contrast ratios for reference
        common_contrasts = {
            ("#000000", "#FFFFFF"): 21.0,  # Black on white
            ("#333333", "#FFFFFF"): 12.6,  # Dark gray on white
            ("#666666", "#FFFFFF"): 5.7,  # Medium gray on white
            ("#999999", "#FFFFFF"): 2.9,  # Light gray on white
        }

        key = (foreground.upper(), background.upper())
        return common_contrasts.get(key, 4.5)  # Default to acceptable

    @staticmethod
    def meets_wcag_aa(contrast_ratio: float, text_size: str = "normal") -> bool:
        """Check if contrast ratio meets WCAG AA requirements"""

        if text_size == "large":
            return contrast_ratio >= 3.0
        else:
            return contrast_ratio >= 4.5

    @staticmethod
    def meets_wcag_aaa(contrast_ratio: float, text_size: str = "normal") -> bool:
        """Check if contrast ratio meets WCAG AAA requirements"""

        if text_size == "large":
            return contrast_ratio >= 4.5
        else:
            return contrast_ratio >= 7.0


class FocusManagement:
    """Utilities for focus management"""

    @staticmethod
    def get_focus_order(elements: list[dict[str, Any]]) -> list[str]:
        """Determine logical focus order for elements"""

        # Sort by visual position and importance
        sorted_elements = sorted(
            elements,
            key=lambda x: (x.get("visual_order", 999), x.get("importance", "low")),
        )

        return [elem.get("id", "") for elem in sorted_elements if elem.get("id")]

    @staticmethod
    def should_auto_focus(element_type: str, context: str = "") -> bool:
        """Determine if element should receive auto-focus"""

        auto_focus_elements = {
            "search_input": True,
            "main_input": True,
            "first_navigation": True,
            "error_message": True,
            "modal": True,
        }

        key = f"{element_type}_{context}".strip("_")
        return auto_focus_elements.get(key, False)


class AccessibilityValidator:
    """Validator for accessibility requirements"""

    @staticmethod
    def validate_element_accessibility(element: dict[str, Any]) -> dict[str, Any]:
        """Validate element against accessibility standards"""

        issues = []
        warnings = []

        # Check for required attributes
        if not element.get("aria-label") and not element.get("aria-labelledby"):
            if element.get("type") in ["button", "link", "input"]:
                issues.append("Missing aria-label or aria-labelledby")

        # Check contrast ratio
        if "color" in element and "background_color" in element:
            contrast = ColorContrastChecker.calculate_contrast_ratio(
                element["color"], element["background_color"]
            )

            if not ColorContrastChecker.meets_wcag_aa(contrast):
                issues.append(f"Insufficient color contrast: {contrast:.1f}:1")
            elif not ColorContrastChecker.meets_wcag_aaa(contrast):
                warnings.append(f"Could improve color contrast: {contrast:.1f}:1")

        # Check focus management
        if element.get("focusable", False) and not element.get("tabindex"):
            warnings.append("Consider adding tabindex for better keyboard navigation")

        return {
            "element_id": element.get("id", "unknown"),
            "issues": issues,
            "warnings": warnings,
            "passed": len(issues) == 0,
        }

    @staticmethod
    def generate_accessibility_report(elements: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate comprehensive accessibility report"""

        results = [
            AccessibilityValidator.validate_element_accessibility(elem)
            for elem in elements
        ]

        total_issues = sum(len(result["issues"]) for result in results)
        total_warnings = sum(len(result["warnings"]) for result in results)
        passed_elements = sum(1 for result in results if result["passed"])

        return {
            "total_elements": len(elements),
            "passed_elements": passed_elements,
            "total_issues": total_issues,
            "total_warnings": total_warnings,
            "compliance_score": (passed_elements / len(elements)) * 100
            if elements
            else 100,
            "detailed_results": results,
        }
