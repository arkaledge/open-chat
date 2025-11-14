"""Search Service for web search integration"""

from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings


class SearchService:
    """Service for web search integration"""

    def __init__(self):
        """Initialize search service"""
        self.tavily_api_key = settings.tavily_api_key
        self.brave_api_key = settings.brave_api_key

    async def search(
        self,
        query: str,
        provider: str = "tavily",
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[Dict[str, Any]]:
        """
        Perform web search

        Args:
            query: Search query
            provider: Search provider (tavily, brave)
            max_results: Maximum number of results
            search_depth: Search depth (basic, advanced)

        Returns:
            List of search results with title, content, URL
        """
        if provider == "tavily" and self.tavily_api_key:
            return await self._tavily_search(query, max_results, search_depth)
        elif provider == "brave" and self.brave_api_key:
            return await self._brave_search(query, max_results)
        else:
            raise ValueError(f"Search provider {provider} not configured")

    async def _tavily_search(
        self,
        query: str,
        max_results: int,
        search_depth: str
    ) -> List[Dict[str, Any]]:
        """Tavily search implementation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False
                },
                timeout=30.0
            )

            result = response.json()

            # Format results
            formatted_results = []
            for item in result.get("results", []):
                formatted_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                    "source": "tavily"
                })

            # Add AI-generated answer if available
            if "answer" in result:
                formatted_results.insert(0, {
                    "title": "AI Summary",
                    "url": "",
                    "content": result["answer"],
                    "score": 1.0,
                    "source": "tavily_answer"
                })

            return formatted_results

    async def _brave_search(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Brave search implementation"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.brave_api_key
                },
                params={
                    "q": query,
                    "count": max_results
                },
                timeout=30.0
            )

            result = response.json()

            # Format results
            formatted_results = []
            for item in result.get("web", {}).get("results", []):
                formatted_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("description", ""),
                    "score": 0.0,  # Brave doesn't provide scores
                    "source": "brave"
                })

            return formatted_results

    async def search_and_format(
        self,
        query: str,
        provider: str = "tavily",
        max_results: int = 5
    ) -> str:
        """
        Search and format results for LLM context

        Args:
            query: Search query
            provider: Search provider
            max_results: Maximum results

        Returns:
            Formatted string with search results
        """
        results = await self.search(query, provider, max_results)

        if not results:
            return "No search results found."

        # Format for context injection
        formatted = "Web Search Results:\n\n"

        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   URL: {result['url']}\n"
            formatted += f"   {result['content']}\n\n"

        return formatted

    def extract_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract source citations from search results

        Args:
            results: Search results

        Returns:
            List of source citations
        """
        sources = []
        for result in results:
            if result.get("url"):  # Skip AI summaries without URLs
                sources.append({
                    "title": result["title"],
                    "url": result["url"]
                })
        return sources
