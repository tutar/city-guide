"""
Navigation generator for City Guide Smart Assistant
"""

import logging
import uuid
from typing import Any

from src.services.ai_service import AIService
from src.services.data_service import DataService

# Configure logging
logger = logging.getLogger(__name__)


class NavigationGenerator:
    """Service for generating dynamic navigation options based on conversation context"""

    def __init__(self, ai_service: AIService | None = None):
        self.ai_service = ai_service or AIService()
        self.data_service = DataService()

    def generate_dynamic_navigation_options(
        self,
        conversation_context: dict[str, Any],
        search_results: list | None = None,
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

            # Generate stage-specific options
            conversation_stage = self._determine_conversation_stage(
                conversation_context
            )
            stage_options = self.generate_stage_specific_options(
                conversation_stage, current_service_category_id
            )
            navigation_options.extend(stage_options)

            # Remove duplicates and sort by priority
            unique_options = self._deduplicate_and_sort_options(navigation_options)

            # Limit to max options
            final_options = unique_options[:max_options]

            logger.info(
                f"Generated {len(final_options)} navigation options for stage: {conversation_stage}"
            )
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
        action_types: list[str] | None = None,
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

    def generate_stage_specific_options(
        self, conversation_stage: str, service_category_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Generate navigation options specific to the conversation stage"""
        stage_options = {
            "information_gathering": [
                {
                    "label": "Requirements Overview",
                    "action_type": "requirements",
                    "description": "View all required documents and materials",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Application Process",
                    "action_type": "explain",
                    "description": "Step-by-step application guide",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Common Questions",
                    "action_type": "explain",
                    "description": "Frequently asked questions",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "requirements_phase": [
                {
                    "label": "Document Checklist",
                    "action_type": "requirements",
                    "description": "Complete list of required documents",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Document Templates",
                    "action_type": "download",
                    "description": "Download official forms and templates",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Photo Requirements",
                    "action_type": "explain",
                    "description": "Detailed photo specifications",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "application_phase": [
                {
                    "label": "Online Application",
                    "action_type": "appointment",
                    "description": "Start online application process",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "In-Person Application",
                    "action_type": "location",
                    "description": "Find nearest service location",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Application Tips",
                    "action_type": "explain",
                    "description": "Helpful tips for successful application",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "appointment_phase": [
                {
                    "label": "Book Appointment",
                    "action_type": "appointment",
                    "description": "Schedule your appointment online",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Appointment Locations",
                    "action_type": "location",
                    "description": "Find appointment service centers",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Appointment Preparation",
                    "action_type": "requirements",
                    "description": "What to bring to your appointment",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "location_phase": [
                {
                    "label": "Find Nearest Location",
                    "action_type": "location",
                    "description": "Locate nearby service centers",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Operating Hours",
                    "action_type": "explain",
                    "description": "Check service center hours",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Contact Information",
                    "action_type": "contact",
                    "description": "Get phone numbers and email",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "status_check": [
                {
                    "label": "Check Application Status",
                    "action_type": "status",
                    "description": "Track your application progress",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Processing Times",
                    "action_type": "explain",
                    "description": "Expected processing duration",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Contact Support",
                    "action_type": "contact",
                    "description": "Get help with status inquiries",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "cost_inquiry": [
                {
                    "label": "Fee Structure",
                    "action_type": "explain",
                    "description": "Detailed cost breakdown",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Payment Methods",
                    "action_type": "explain",
                    "description": "Accepted payment options",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Fee Waivers",
                    "action_type": "explain",
                    "description": "Eligibility for fee reductions",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
            "troubleshooting": [
                {
                    "label": "Common Issues",
                    "action_type": "explain",
                    "description": "Solutions to frequent problems",
                    "priority": 1,
                    "source": "stage_specific",
                },
                {
                    "label": "Technical Support",
                    "action_type": "contact",
                    "description": "Get technical assistance",
                    "priority": 2,
                    "source": "stage_specific",
                },
                {
                    "label": "Alternative Methods",
                    "action_type": "explain",
                    "description": "Other ways to complete your task",
                    "priority": 3,
                    "source": "stage_specific",
                },
            ],
        }

        # Return options for the specific stage, or empty list if stage not recognized
        return stage_options.get(conversation_stage, [])

    def _determine_conversation_stage(
        self, conversation_context: dict[str, Any]
    ) -> str:
        """Determine the current stage of the conversation with enhanced detection"""
        current_query = conversation_context.get("current_query", "").lower()
        conversation_history = conversation_context.get("conversation_history", [])

        # Enhanced conversation stage detection with context awareness
        query_lower = current_query.lower()

        # Check for specific patterns in the conversation
        if any(
            word in query_lower
            for word in ["how", "what", "where", "when", "explain", "tell me about"]
        ):
            return "information_gathering"
        elif any(
            word in query_lower
            for word in [
                "apply",
                "submit",
                "register",
                "start application",
                "begin process",
            ]
        ):
            return "application_phase"
        elif any(
            word in query_lower
            for word in [
                "requirement",
                "document",
                "material",
                "need to bring",
                "required",
            ]
        ):
            return "requirements_phase"
        elif any(
            word in query_lower
            for word in [
                "appointment",
                "schedule",
                "book",
                "make appointment",
                "reserve",
            ]
        ):
            return "appointment_phase"
        elif any(
            word in query_lower
            for word in ["location", "address", "where", "nearest", "service center"]
        ):
            return "location_phase"
        elif any(
            word in query_lower
            for word in ["status", "check", "track", "progress", "update"]
        ):
            return "status_check"
        elif any(
            word in query_lower
            for word in ["cost", "fee", "price", "how much", "payment"]
        ):
            return "cost_inquiry"
        elif any(
            word in query_lower
            for word in ["problem", "issue", "error", "trouble", "help with"]
        ):
            return "troubleshooting"
        else:
            # Check conversation history for context
            recent_messages = (
                conversation_history[-3:]
                if len(conversation_history) >= 3
                else conversation_history
            )
            for msg in recent_messages:
                content = msg.get("content", "").lower()
                if any(
                    word in content for word in ["requirement", "document", "material"]
                ):
                    return "requirements_phase"
                elif any(word in content for word in ["appointment", "schedule"]):
                    return "appointment_phase"
                elif any(word in content for word in ["location", "address"]):
                    return "location_phase"

            return "general_inquiry"
