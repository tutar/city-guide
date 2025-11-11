"""
Relevance visualization component for Chainlit frontend.

This component provides rich visualizations for source relevance explanations,
including relevance scores, confidence levels, and comparative analysis.
"""

import logging
from typing import Any, Dict, List, Optional

import chainlit as cl

logger = logging.getLogger(__name__)


class RelevanceVisualizationComponent:
    """Component for visualizing source relevance explanations."""

    def __init__(self):
        self.lucide_icons = {
            "relevance": "star",
            "confidence": "shield",
            "comparison": "bar-chart-3",
            "details": "info",
            "factors": "list",
            "access": "check-circle",
            "high": "trending-up",
            "medium": "minus",
            "low": "trending-down",
        }

    async def display_relevance_summary(
        self,
        explanations: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display a summary of source relevance.

        Args:
            explanations: List of relevance explanations
            statistics: Relevance statistics
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            if not explanations:
                await cl.Message(
                    content="No relevance information available.",
                    author="Source Relevance",
                ).send()
                return

            # Create summary message
            total_sources = len(explanations)
            avg_relevance = statistics.get("average_relevance", 0.0)
            top_source = statistics.get("top_source")

            message_content = f"""
## 🔍 Source Relevance Summary

**Overview:** {total_sources} document sources analyzed
**Average Relevance:** {avg_relevance:.1%}
**Top Source:** {top_source['title'] if top_source else 'N/A'} ({top_source['relevance_score']:.1%} if top_source else 'N/A')

### Top Relevant Sources
"""

            # Add top 5 sources
            top_sources = explanations[:5]
            for i, exp in enumerate(top_sources):
                score = exp["relevance_score"]
                confidence = exp["confidence_level"]
                title = exp["title"]
                accessible = exp["accessibility"]

                # Create relevance indicator
                if score >= 0.8:
                    indicator = "🟢"
                elif score >= 0.6:
                    indicator = "🟡"
                elif score >= 0.4:
                    indicator = "🟠"
                else:
                    indicator = "🔴"

                # Create accessibility indicator
                access_indicator = "✅" if accessible else "❌"

                message_content += (
                    f"\n{indicator} **{title}** {access_indicator}\n"
                    f"   • **Relevance:** {score:.1%}\n"
                    f"   • **Confidence:** {confidence.replace('_', ' ').title()}\n"
                )

            if len(explanations) > 5:
                message_content += f"\n*... and {len(explanations) - 5} more sources*"

            # Create actions
            actions = self._create_relevance_actions(explanations, message_id)

            await cl.Message(
                content=message_content,
                actions=actions,
                author="Source Relevance",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed relevance summary for {total_sources} sources "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display relevance summary: {e}")
            await self._display_fallback_relevance(explanations, user_session_id)

    async def display_detailed_relevance(
        self,
        explanation: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display detailed relevance information for a single document.

        Args:
            explanation: Single document relevance explanation
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            document_id = explanation["document_id"]
            title = explanation["title"]
            score = explanation["relevance_score"]
            confidence = explanation["confidence_level"]
            explanation_text = explanation["explanation"]
            factors = explanation["relevance_factors"]
            accessible = explanation["accessibility"]

            # Create relevance indicator
            if score >= 0.8:
                score_emoji = "⭐"
                score_text = "Highly Relevant"
            elif score >= 0.6:
                score_emoji = "✅"
                score_text = "Quite Relevant"
            elif score >= 0.4:
                score_emoji = "🔄"
                score_text = "Somewhat Relevant"
            else:
                score_emoji = "📄"
                score_text = "Supplementary"

            # Create confidence indicator
            confidence_emoji = {
                "high": "🟢",
                "medium": "🟡",
                "low": "🟠",
                "very_low": "🔴",
            }.get(confidence, "⚪")

            message_content = f"""
## 📊 Detailed Relevance Analysis

### {title}

**Overall Relevance:** {score_emoji} {score_text} ({score:.1%})
**Confidence Level:** {confidence_emoji} {confidence.replace('_', ' ').title()}
**Accessibility:** {'✅ Available' if accessible else '❌ Unavailable'}

### Explanation
{explanation_text}

### Relevance Factors
"""

            # Add relevance factors
            for factor_name, factor_data in factors.items():
                factor_score = factor_data["score"]
                factor_explanation = factor_data["explanation"]

                # Factor score indicator
                if factor_score >= 0.7:
                    factor_indicator = "🟢"
                elif factor_score >= 0.4:
                    factor_indicator = "🟡"
                else:
                    factor_indicator = "🔴"

                message_content += (
                    f"\n{factor_indicator} **{factor_name.replace('_', ' ').title()}**\n"
                    f"   • **Score:** {factor_score:.1%}\n"
                    f"   • **Details:** {factor_explanation}\n"
                )

                # Add specific factors if available
                specific_factors = factor_data.get("factors", [])
                if specific_factors:
                    for specific_factor in specific_factors[:3]:  # Show top 3
                        message_content += f"     - {specific_factor}\n"

            # Create actions
            actions = self._create_detailed_actions(document_id, message_id)

            await cl.Message(
                content=message_content,
                actions=actions,
                author="Source Relevance",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed detailed relevance for {document_id} "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display detailed relevance: {e}")
            await self._display_fallback_detailed(explanation, user_session_id)

    async def display_relevance_comparison(
        self,
        explanations: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        user_session_id: str,
        message_id: Optional[str] = None,
    ) -> None:
        """
        Display relevance comparison between multiple documents.

        Args:
            explanations: List of relevance explanations
            statistics: Relevance statistics
            user_session_id: User session identifier
            message_id: Optional message ID for context
        """
        try:
            if len(explanations) < 2:
                await cl.Message(
                    content="Need at least 2 documents for comparison.",
                    author="Source Relevance",
                ).send()
                return

            # Sort by relevance score
            sorted_explanations = sorted(
                explanations, key=lambda x: x["relevance_score"], reverse=True
            )

            message_content = """
## 📈 Source Relevance Comparison

### Ranking by Relevance
"""

            # Create comparison table
            for i, exp in enumerate(sorted_explanations):
                rank = i + 1
                title = exp["title"]
                score = exp["relevance_score"]
                confidence = exp["confidence_level"]
                accessible = exp["accessibility"]

                # Rank indicator
                if rank == 1:
                    rank_emoji = "🥇"
                elif rank == 2:
                    rank_emoji = "🥈"
                elif rank == 3:
                    rank_emoji = "🥉"
                else:
                    rank_emoji = f"{rank}."

                # Score bar visualization
                bar_length = int(score * 20)  # Scale to 20 characters
                bar = "█" * bar_length + "░" * (20 - bar_length)

                message_content += (
                    f"\n{rank_emoji} **{title}**\n"
                    f"   {bar} {score:.1%}\n"
                    f"   • Confidence: {confidence.replace('_', ' ').title()}\n"
                    f"   • Access: {'✅' if accessible else '❌'}\n"
                )

            # Add statistics
            avg_relevance = statistics.get("average_relevance", 0.0)
            score_dist = statistics.get("score_distribution", {})

            message_content += f"\n### Statistics\n"
            message_content += f"**Average Relevance:** {avg_relevance:.1%}\n"
            message_content += f"**Score Distribution:**\n"
            message_content += f"  • High (≥80%): {score_dist.get('high', 0)}\n"
            message_content += f"  • Medium (60-79%): {score_dist.get('medium', 0)}\n"
            message_content += f"  • Low (40-59%): {score_dist.get('low', 0)}\n"
            message_content += f"  • Very Low (<40%): {score_dist.get('very_low', 0)}\n"

            # Create comparison actions
            actions = self._create_comparison_actions(sorted_explanations, message_id)

            await cl.Message(
                content=message_content,
                actions=actions,
                author="Source Relevance",
                parent_id=user_session_id,
            ).send()

            logger.info(
                f"Displayed relevance comparison for {len(explanations)} sources "
                f"(session: {user_session_id})"
            )

        except Exception as e:
            logger.error(f"Failed to display relevance comparison: {e}")
            await self._display_fallback_comparison(explanations, user_session_id)

    def _create_relevance_actions(
        self, explanations: List[Dict[str, Any]], message_id: Optional[str] = None
    ) -> List[cl.Action]:
        """Create actions for relevance summary."""
        actions = []

        # Comparison action
        if len(explanations) >= 2:
            comparison_action = cl.Action(
                name=f"relevance_comparison_{message_id or 'default'}",
                payload={
                    "action_type": "relevance_comparison",
                    "document_ids": [exp["document_id"] for exp in explanations],
                },
                icon=self.lucide_icons["comparison"],
                label="Compare Sources",
                tooltip="Compare relevance across all sources",
            )
            actions.append(comparison_action)

        # Detailed view for top source
        if explanations:
            top_source = explanations[0]
            details_action = cl.Action(
                name=f"relevance_details_{top_source['document_id']}_{message_id or 'default'}",
                payload={
                    "action_type": "relevance_details",
                    "document_id": top_source["document_id"],
                },
                icon=self.lucide_icons["details"],
                label="Top Source Details",
                tooltip="Show detailed relevance for top source",
            )
            actions.append(details_action)

        return actions

    def _create_detailed_actions(
        self, document_id: str, message_id: Optional[str] = None
    ) -> List[cl.Action]:
        """Create actions for detailed relevance view."""
        return [
            cl.Action(
                name=f"doc_preview_{document_id}_{message_id or 'default'}",
                payload={"action_type": "preview", "document_id": document_id},
                icon=self.lucide_icons["access"],
                label="Document Preview",
                tooltip="Show document preview",
            ),
            cl.Action(
                name=f"factors_{document_id}_{message_id or 'default'}",
                payload={
                    "action_type": "relevance_factors",
                    "document_id": document_id,
                },
                icon=self.lucide_icons["factors"],
                label="Factor Details",
                tooltip="Show detailed relevance factors",
            ),
        ]

    def _create_comparison_actions(
        self, explanations: List[Dict[str, Any]], message_id: Optional[str] = None
    ) -> List[cl.Action]:
        """Create actions for relevance comparison."""
        actions = []

        # Individual source details
        for exp in explanations[:3]:  # Top 3 sources
            details_action = cl.Action(
                name=f"comparison_details_{exp['document_id']}_{message_id or 'default'}",
                payload={
                    "action_type": "relevance_details",
                    "document_id": exp["document_id"],
                },
                icon=self.lucide_icons["details"],
                label=f"Details: {exp['title'][:15]}{'...' if len(exp['title']) > 15 else ''}",
                tooltip=f"Show details for {exp['title']}",
            )
            actions.append(details_action)

        return actions

    async def _display_fallback_relevance(
        self, explanations: List[Dict[str, Any]], user_session_id: str
    ) -> None:
        """Display fallback relevance message."""
        try:
            if not explanations:
                await cl.Message(
                    content="No relevance information available.",
                    author="Source Relevance",
                ).send()
                return

            simple_content = "## Source Relevance\n\n"
            for exp in explanations[:3]:
                simple_content += f"• {exp['title']}: {exp['relevance_score']:.1%}\n"

            await cl.Message(
                content=simple_content,
                author="Source Relevance",
                parent_id=user_session_id,
            ).send()

        except Exception as e:
            logger.error(f"Failed to display fallback relevance: {e}")
            await cl.Message(
                content="Source relevance information", author="Source Relevance"
            ).send()

    async def _display_fallback_detailed(
        self, explanation: Dict[str, Any], user_session_id: str
    ) -> None:
        """Display fallback detailed relevance."""
        try:
            content = f"""
## Relevance: {explanation['title']}

Score: {explanation['relevance_score']:.1%}
Confidence: {explanation['confidence_level']}

{explanation['explanation']}
"""
            await cl.Message(
                content=content, author="Source Relevance", parent_id=user_session_id
            ).send()

        except Exception as e:
            logger.error(f"Failed to display fallback detailed: {e}")
            await cl.Message(
                content="Detailed relevance information", author="Source Relevance"
            ).send()

    async def _display_fallback_comparison(
        self, explanations: List[Dict[str, Any]], user_session_id: str
    ) -> None:
        """Display fallback comparison."""
        try:
            content = "## Source Comparison\n\n"
            for exp in explanations:
                content += f"• {exp['title']}: {exp['relevance_score']:.1%}\n"

            await cl.Message(
                content=content, author="Source Relevance", parent_id=user_session_id
            ).send()

        except Exception as e:
            logger.error(f"Failed to display fallback comparison: {e}")
            await cl.Message(
                content="Source comparison information", author="Source Relevance"
            ).send()


# Global component instance
relevance_visualization = RelevanceVisualizationComponent()
