"""
Search results component with source attribution for official government information
"""

import chainlit as cl
from typing import List, Dict, Any, Optional


class SearchResultsComponent:
    """Component for displaying search results with source attribution"""

    def __init__(self):
        self.search_history = []

    async def display_search_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        show_source_attribution: bool = True
    ) -> cl.Message:
        """Display search results with source attribution"""
        if not results:
            return await self._display_no_results_message(query)

        # Create message content with formatted results
        content = self._format_search_results(results, query, show_source_attribution)

        # Create message with metadata
        message_metadata = {
            "role": "search-results",
            "query": query,
            "result_count": len(results),
            "has_source_attribution": show_source_attribution
        }

        message = cl.Message(
            content=content,
            author="Search",
            metadata=message_metadata
        )

        await message.send()

        # Store in search history
        self.search_history.append({
            "query": query,
            "results": results,
            "timestamp": cl.Message.timestamp,
            "result_count": len(results)
        })

        return message

    def _format_search_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        show_source_attribution: bool
    ) -> str:
        """Format search results with source attribution"""
        content = f"## Search Results for: '{query}'\n\n"

        for i, result in enumerate(results[:5], 1):  # Show top 5 results
            content += f"### {i}. {result.get('document_title', 'Unknown')}\n\n"

            # Add document content snippet
            if result.get('document_content'):
                snippet = self._extract_snippet(result['document_content'], query)
                content += f"{snippet}\n\n"

            # Add source attribution
            if show_source_attribution:
                source_info = self._format_source_attribution(result)
                content += f"{source_info}\n\n"

            # Add relevance score if available
            if result.get('similarity_score'):
                score_percent = int(result['similarity_score'] * 100)
                content += f"**Relevance:** {score_percent}%\n\n"

            content += "---\n\n"

        return content

    def _extract_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract relevant snippet from content"""
        # Simple snippet extraction - highlight query terms
        content_lower = content.lower()
        query_lower = query.lower()

        # Find first occurrence of query
        query_start = content_lower.find(query_lower)

        if query_start == -1:
            # If query not found, take first part of content
            snippet = content[:max_length]
            if len(content) > max_length:
                snippet += "..."
            return snippet

        # Extract context around query
        start = max(0, query_start - 50)
        end = min(len(content), query_start + len(query) + 150)

        snippet = content[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _format_source_attribution(self, result: Dict[str, Any]) -> str:
        """Format source attribution information"""
        source_url = result.get('source_url', '')
        metadata = result.get('metadata', {})

        attribution_parts = []

        # Add source type
        source_type = metadata.get('source_type', 'government')
        if source_type == 'government':
            attribution_parts.append("**Source:** Official Government Website")
        elif source_type == 'documentation':
            attribution_parts.append("**Source:** Official Documentation")
        else:
            attribution_parts.append("**Source:** Information Portal")

        # Add verification status
        is_verified = metadata.get('is_verified', False)
        if is_verified:
            attribution_parts.append("**Status:** ✅ Verified")
        else:
            attribution_parts.append("**Status:** ⚠️ Unverified")

        # Add last updated date if available
        last_updated = metadata.get('last_updated')
        if last_updated:
            attribution_parts.append(f"**Last Updated:** {last_updated}")

        # Add source URL if available
        if source_url:
            # Extract domain for display
            domain = self._extract_domain(source_url)
            if domain:
                attribution_parts.append(f"**Website:** {domain}")

        return " | ".join(attribution_parts)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc if parsed.netloc else url
        except:
            return url

    async def _display_no_results_message(self, query: str) -> cl.Message:
        """Display message when no results found"""
        content = f"""## No Results Found

I couldn't find any information about "{query}" in our government service database.

**Suggestions:**
- Check your spelling
- Try different keywords
- Contact the relevant government department directly
- Visit the official government website for the most up-to-date information

**Official Sources:**
- [Hong Kong Immigration Department](https://www.immd.gov.hk)
- [Macau Government Services](https://www.gov.mo)
"""

        message = cl.Message(
            content=content,
            author="Search"
        )

        await message.send()
        return message

    async def display_step_by_step_guidance(
        self,
        steps: List[Dict[str, Any]],
        service_name: str
    ) -> cl.Message:
        """Display step-by-step guidance for government services"""
        content = f"## Step-by-Step Guide: {service_name}\n\n"

        for i, step in enumerate(steps, 1):
            content += f"### Step {i}: {step.get('title', 'Unknown')}\n\n"

            # Add description
            if step.get('description'):
                content += f"{step['description']}\n\n"

            # Add requirements if available
            if step.get('requirements'):
                content += "**Requirements:**\n"
                for req in step['requirements']:
                    content += f"- {req}\n"
                content += "\n"

            # Add estimated time if available
            if step.get('estimated_time'):
                content += f"**Estimated Time:** {step['estimated_time']}\n\n"

            # Add cost if available
            if step.get('cost'):
                content += f"**Cost:** {step['cost']}\n\n"

            # Add source attribution for the step
            if step.get('source_url'):
                source_info = self._format_source_attribution(step)
                content += f"{source_info}\n\n"

            content += "---\n\n"

        # Add overall tips
        content += "**Tips:**\n"
        content += "- Have all required documents ready before starting\n"
        content += "- Check official websites for the most current information\n"
        content += "- Contact the relevant department if you have questions\n"

        message = cl.Message(
            content=content,
            author="Guidance"
        )

        await message.send()
        return message

    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history"""
        return self.search_history[-limit:]

    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics"""
        if not self.search_history:
            return {
                "total_searches": 0,
                "average_results": 0,
                "success_rate": 0
            }

        total_searches = len(self.search_history)
        total_results = sum(search["result_count"] for search in self.search_history)
        successful_searches = sum(1 for search in self.search_history if search["result_count"] > 0)

        return {
            "total_searches": total_searches,
            "average_results": total_results / total_searches if total_searches > 0 else 0,
            "success_rate": (successful_searches / total_searches) * 100 if total_searches > 0 else 0,
            "recent_queries": [search["query"] for search in self.search_history[-5:]]
        }


# Global search results component instance
search_results = SearchResultsComponent()