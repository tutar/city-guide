"""
Navigation generator for City Guide Smart Assistant
"""

import logging
import uuid
from typing import Any, Optional

from src.services.ai_service import AIService
from src.services.data_service import DataService

# Configure logging
logger = logging.getLogger(__name__)


class NavigationGenerator:
    """Service for generating dynamic navigation options based on conversation context"""

    def __init__(self):
        self.ai_service = AIService()
        self.data_service = DataService()

    def generate_dynamic_navigation_options(
        self,
        conversation_context: dict[str, Any],
        search_results: Optional[list] = None,
        max_options: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate dynamic navigation options based on conversation context and search results"""
        try:
            current_service_category_id = conversation_context.get(
                "current_service_category_id"
            )
            current_query = conversation_context.get("current_query", "")

            navigation_options = []

            # Get static navigation options from database if service category is known
            if current_service_category_id:
                try:
                    service_category_id = uuid.UUID(current_service_category_id)
                    with self.data_service as data_service:
                        static_options = (
                            data_service.get_navigation_options_by_category(
                                service_category_id
                            )
                        )

                        # Convert static options to navigation format
                        for option in static_options:
                            navigation_options.append(
                                {
                                    "label": option.label,
                                    "action_type": option.action_type,
                                    "target_url": option.target_url,
                                    "description": option.description,
                                    "priority": option.priority,
                                    "source": "static",
                                }
                            )

                except (ValueError, Exception) as e:
                    logger.warning(f"Failed to get static navigation options: {e}")

            # Generate dynamic options based on search results
            if search_results:
                dynamic_options = self._generate_options_from_search_results(
                    search_results, current_query
                )
                navigation_options.extend(dynamic_options)

            # Generate AI-suggested options
            if current_query:
                ai_options = self._generate_ai_suggested_options(
                    current_query, conversation_context
                )
                navigation_options.extend(ai_options)

            # Remove duplicates and sort by priority
            unique_options = self._deduplicate_and_sort_options(navigation_options)

            # Limit to max options
            final_options = unique_options[:max_options]

            logger.info(f"Generated {len(final_options)} navigation options")
            return final_options

        except Exception as e:
            logger.error(f"Failed to generate navigation options: {e}")
            return []

    def _generate_options_from_search_results(
        self, search_results: list, current_query: str
    ) -> list[dict[str, Any]]:
        """Generate navigation options from search results"""
        options = []

        for result in search_results:
            # Extract document type from result
            document_type = result.get("document_type", "")
            similarity_score = result.get("similarity_score", 0)

            # Generate options based on document type
            if document_type == "requirements":
                options.append(
                    {
                        "label": "Material Requirements",
                        "action_type": "requirements",
                        "description": "View required documents and materials",
                        "priority": self._calculate_priority(similarity_score, 1),
                        "source": "search",
                        "confidence": similarity_score,
                    }
                )

            elif document_type == "procedures":
                options.append(
                    {
                        "label": "Application Process",
                        "action_type": "explain",
                        "description": "Step-by-step application guide",
                        "priority": self._calculate_priority(similarity_score, 2),
                        "source": "search",
                        "confidence": similarity_score,
                    }
                )

            elif document_type == "locations":
                options.append(
                    {
                        "label": "Service Locations",
                        "action_type": "location",
                        "description": "Find nearby service locations",
                        "priority": self._calculate_priority(similarity_score, 3),
                        "source": "search",
                        "confidence": similarity_score,
                    }
                )

            elif document_type == "faqs":
                options.append(
                    {
                        "label": "Common Questions",
                        "action_type": "explain",
                        "description": "Frequently asked questions",
                        "priority": self._calculate_priority(similarity_score, 4),
                        "source": "search",
                        "confidence": similarity_score,
                    }
                )

        return options

    def _generate_ai_suggested_options(
        self, current_query: str, conversation_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate AI-suggested navigation options"""
        try:
            # Get available services for context
            available_services = []
            with self.data_service as data_service:
                services = data_service.get_active_service_categories()
                available_services = [service.name for service in services]

            # Generate suggestions using AI service
            ai_suggestions = self.ai_service.generate_navigation_suggestions(
                current_context=current_query, available_services=available_services
            )

            # Convert AI suggestions to navigation format
            options = []
            for suggestion in ai_suggestions:
                options.append(
                    {
                        "label": suggestion.get("label", ""),
                        "action_type": suggestion.get("action_type", "related"),
                        "description": "AI-suggested next step",
                        "priority": 5,  # Lower priority for AI suggestions
                        "source": "ai",
                        "confidence": 0.7,  # Default confidence for AI suggestions
                    }
                )

            return options

        except Exception as e:
            logger.warning(f"Failed to generate AI suggestions: {e}")
            return []

    def _calculate_priority(self, similarity_score: float, base_priority: int) -> int:
        """Calculate priority based on similarity score and base priority"""
        # Higher similarity scores get higher priority (lower number)
        priority_adjustment = int((1 - similarity_score) * 3)  # 0-3 adjustment
        return max(1, base_priority - priority_adjustment)

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
        unique_options.sort(key=lambda x: x["priority"])

        return unique_options

    def filter_navigation_options(
        self,
        options: list[dict[str, Any]],
        action_types: Optional[list[str]] = None,
        min_confidence: float = 0.0,
        max_options: int = 5,
    ) -> list[dict[str, Any]]:
        """Filter navigation options based on criteria"""
        filtered_options = []

        for option in options:
            # Filter by action type
            if action_types and option["action_type"] not in action_types:
                continue

            # Filter by confidence
            confidence = option.get("confidence", 1.0)
            if confidence < min_confidence:
                continue

            filtered_options.append(option)

        # Sort by priority and limit
        filtered_options.sort(key=lambda x: x["priority"])
        return filtered_options[:max_options]

    def get_navigation_context(
        self, conversation_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Get context information for navigation generation"""
        context = {
            "current_service_category_id": conversation_context.get(
                "current_service_category_id"
            ),
            "current_query": conversation_context.get("current_query", ""),
            "user_preferences": conversation_context.get("user_preferences", {}),
            "conversation_stage": self._determine_conversation_stage(
                conversation_context
            ),
        }

        return context

    def _determine_conversation_stage(
        self, conversation_context: dict[str, Any]
    ) -> str:
        """Determine the current stage of the conversation"""
        current_query = conversation_context.get("current_query", "").lower()

        # Basic conversation stage detection
        if any(word in current_query for word in ["how", "what", "where", "when"]):
            return "information_gathering"
        elif any(word in current_query for word in ["apply", "submit", "register"]):
            return "application_phase"
        elif any(
            word in current_query for word in ["requirement", "document", "material"]
        ):
            return "requirements_phase"
        elif any(word in current_query for word in ["appointment", "schedule", "book"]):
            return "appointment_phase"
        elif any(word in current_query for word in ["location", "address", "where"]):
            return "location_phase"
        else:
            return "general_inquiry"
