"""
Navigation service for City Guide Smart Assistant
"""

import logging
import uuid
from typing import Any

from src.services.data_service import DataService
from src.services.navigation_generator import NavigationGenerator

# Configure logging
logger = logging.getLogger(__name__)


class NavigationService:
    """Service for managing navigation options and filtering by service category"""

    def __init__(self):
        self.data_service = DataService()
        self.navigation_generator = NavigationGenerator()

    def get_navigation_options_by_category(
        self,
        service_category_id: uuid.UUID,
        conversation_context: dict[str, Any] | None = None,
        search_results: list | None = None,
    ) -> list[dict[str, Any]]:
        """Get navigation options filtered by service category with dynamic generation"""
        try:
            navigation_options = []

            # Get static navigation options from database
            with self.data_service as data_service:
                static_options = data_service.get_navigation_options_by_category(
                    service_category_id
                )

                # Convert to navigation format
                for option in static_options:
                    if option.is_active:
                        navigation_options.append(
                            {
                                "label": option.label,
                                "action_type": option.action_type,
                                "target_url": option.target_url,
                                "description": option.description,
                                "priority": option.priority,
                                "source": "static",
                                "service_category_id": str(service_category_id),
                            }
                        )

            # Generate dynamic options if conversation context is provided
            if conversation_context:
                dynamic_options = (
                    self.navigation_generator.generate_dynamic_navigation_options(
                        conversation_context=conversation_context,
                        search_results=search_results,
                    )
                )
                navigation_options.extend(dynamic_options)

            # Sort by priority and remove duplicates
            navigation_options = self._deduplicate_and_sort_options(navigation_options)

            logger.info(
                f"Retrieved {len(navigation_options)} navigation options for service {service_category_id}"
            )
            return navigation_options

        except Exception as e:
            logger.error(f"Failed to get navigation options by category: {e}")
            return []

    def filter_navigation_options(
        self,
        options: list[dict[str, Any]],
        action_types: list[str] | None = None,
        min_priority: int = 1,
        max_priority: int = 10,
        include_external: bool = True,
    ) -> list[dict[str, Any]]:
        """Filter navigation options based on various criteria"""
        filtered_options = []

        for option in options:
            # Filter by action type
            if action_types and option["action_type"] not in action_types:
                continue

            # Filter by priority
            priority = option.get("priority", 5)
            if not (min_priority <= priority <= max_priority):
                continue

            # Filter external URLs if requested
            if not include_external and option.get("target_url"):
                continue

            filtered_options.append(option)

        # Sort by priority
        filtered_options.sort(key=lambda x: x.get("priority", 5))

        return filtered_options

    def get_action_type_options(self, action_type: str) -> list[dict[str, Any]]:
        """Get navigation options by action type across all services"""
        try:
            options = []

            with self.data_service as data_service:
                # Get all active navigation options
                all_options = data_service.get_all_active_navigation_options()

                # Filter by action type
                for option in all_options:
                    if option.action_type == action_type and option.is_active:
                        options.append(
                            {
                                "label": option.label,
                                "action_type": option.action_type,
                                "target_url": option.target_url,
                                "description": option.description,
                                "priority": option.priority,
                                "service_category_id": str(option.service_category_id),
                                "source": "static",
                            }
                        )

            # Sort by priority
            options.sort(key=lambda x: x["priority"])

            logger.info(
                f"Retrieved {len(options)} options for action type: {action_type}"
            )
            return options

        except Exception as e:
            logger.error(f"Failed to get options by action type: {e}")
            return []

    def update_navigation_option_priority(
        self, option_id: uuid.UUID, new_priority: int
    ) -> bool:
        """Update the priority of a navigation option"""
        try:
            with self.data_service as data_service:
                success = data_service.update_navigation_option_priority(
                    option_id, new_priority
                )

                if success:
                    logger.info(
                        f"Updated priority for navigation option {option_id} to {new_priority}"
                    )
                else:
                    logger.warning(
                        f"Failed to update priority for navigation option {option_id}"
                    )

                return success

        except Exception as e:
            logger.error(f"Failed to update navigation option priority: {e}")
            return False

    def create_navigation_option(
        self,
        service_category_id: uuid.UUID,
        label: str,
        action_type: str,
        description: str,
        priority: int = 5,
        target_url: str | None = None,
    ) -> dict[str, Any] | None:
        """Create a new navigation option"""
        try:
            with self.data_service as data_service:
                # Create navigation option
                option = data_service.create_navigation_option(
                    service_category_id=service_category_id,
                    label=label,
                    action_type=action_type,
                    description=description,
                    priority=priority,
                    target_url=target_url,
                )

                if option:
                    navigation_option = {
                        "id": str(option.id),
                        "label": option.label,
                        "action_type": option.action_type,
                        "target_url": option.target_url,
                        "description": option.description,
                        "priority": option.priority,
                        "service_category_id": str(option.service_category_id),
                        "is_active": option.is_active,
                        "source": "static",
                    }

                    logger.info(f"Created new navigation option: {option.id}")
                    return navigation_option

            return None

        except Exception as e:
            logger.error(f"Failed to create navigation option: {e}")
            return None

    def deactivate_navigation_option(self, option_id: uuid.UUID) -> bool:
        """Deactivate a navigation option"""
        try:
            with self.data_service as data_service:
                success = data_service.deactivate_navigation_option(option_id)

                if success:
                    logger.info(f"Deactivated navigation option: {option_id}")
                else:
                    logger.warning(
                        f"Failed to deactivate navigation option: {option_id}"
                    )

                return success

        except Exception as e:
            logger.error(f"Failed to deactivate navigation option: {e}")
            return False

    def get_navigation_statistics(self) -> dict[str, Any]:
        """Get statistics about navigation options"""
        try:
            with self.data_service as data_service:
                # Get all navigation options
                all_options = data_service.get_all_active_navigation_options()

                # Calculate statistics
                stats = {
                    "total_options": len(all_options),
                    "active_options": len([o for o in all_options if o.is_active]),
                    "options_by_action_type": {},
                    "options_by_service": {},
                    "average_priority": 0,
                    "options_with_urls": 0,
                }

                # Count by action type
                action_type_counts = {}
                service_counts = {}
                total_priority = 0
                urls_count = 0

                for option in all_options:
                    # Action type counts
                    action_type = option.action_type
                    action_type_counts[action_type] = (
                        action_type_counts.get(action_type, 0) + 1
                    )

                    # Service counts
                    service_id = str(option.service_category_id)
                    service_counts[service_id] = service_counts.get(service_id, 0) + 1

                    # Priority sum
                    total_priority += option.priority

                    # URL count
                    if option.target_url:
                        urls_count += 1

                stats["options_by_action_type"] = action_type_counts
                stats["options_by_service"] = service_counts
                stats["average_priority"] = (
                    total_priority / len(all_options) if all_options else 0
                )
                stats["options_with_urls"] = urls_count

                return stats

        except Exception as e:
            logger.error(f"Failed to get navigation statistics: {e}")
            return {}

    def _deduplicate_and_sort_options(
        self, options: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicate options and sort by priority"""
        # Remove duplicates based on label and action_type
        seen = set()
        unique_options = []

        for option in options:
            key = (option["label"], option["action_type"])
            if key not in seen:
                seen.add(key)
                unique_options.append(option)

        # Sort by priority (lower number = higher priority)
        unique_options.sort(key=lambda x: x.get("priority", 5))

        return unique_options

    def validate_navigation_option(self, option: dict[str, Any]) -> dict[str, Any]:
        """Validate a navigation option"""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # Check required fields
        required_fields = ["label", "action_type"]
        for field in required_fields:
            if field not in option or not option[field]:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")

        # Validate action type
        valid_action_types = [
            "explain",
            "requirements",
            "appointment",
            "location",
            "related",
        ]
        if "action_type" in option and option["action_type"] not in valid_action_types:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Invalid action type: {option['action_type']}. Must be one of: {valid_action_types}"
            )

        # Validate priority
        if "priority" in option:
            priority = option["priority"]
            if not isinstance(priority, int) or priority < 1 or priority > 10:
                validation_result["warnings"].append(
                    "Priority should be an integer between 1 and 10"
                )

        # Validate URL if present
        if "target_url" in option and option["target_url"]:
            from src.utils.validation import URLValidator

            url_validation = URLValidator.validate_external_url(option["target_url"])
            if not url_validation["valid"]:
                validation_result["warnings"].append(
                    f"URL validation warning: {url_validation['error']}"
                )

        return validation_result
