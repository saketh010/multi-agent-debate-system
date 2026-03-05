"""
Tavily Search Tool Module

Provides evidence retrieval functionality using the Tavily Search API.
Used by debate agents to gather supporting evidence for arguments.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("Warning: tavily-python not installed. Using mock search results.")


class TavilySearchTool:
    """
    Wrapper for Tavily Search API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily search client.
        
        Args:
            api_key: Tavily API key (default: from environment)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if TAVILY_AVAILABLE and self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for information using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
        
        Returns:
            List of search results with title, url, and content
        """
        if not self.enabled:
            return self._mock_search(query, max_results)
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            
            return results
            
        except Exception as e:
            print(f"Tavily search error: {e}")
            return self._mock_search(query, max_results)
    
    def _mock_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Return mock search results when Tavily is unavailable.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of mock results
        """
        return [
            {
                "title": f"Result for: {query}",
                "url": "https://example.com",
                "content": f"Mock content related to {query}. This is placeholder data used when Tavily API is not available.",
                "score": 0.8
            }
        ]


# Global search tool instance
_search_tool: Optional[TavilySearchTool] = None


def get_search_tool() -> TavilySearchTool:
    """
    Get or create global search tool instance.
    
    Returns:
        TavilySearchTool instance
    """
    global _search_tool
    if _search_tool is None:
        _search_tool = TavilySearchTool()
    return _search_tool


def search_evidence(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to search for evidence.
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        List of search results
    """
    tool = get_search_tool()
    return tool.search(query, max_results)


def evidence_retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for evidence retrieval phase.
    
    Each agent searches for evidence related to the debate topic.
    
    Args:
        state: Current debate state
    
    Returns:
        Dict with evidence items
    """
    topic = state["topic"]
    active_agents = state.get("active_agents", ["architect", "performance", "security"])
    
    evidence_items = []
    
    # Search queries tailored to each agent's perspective
    search_queries = {
        "architect": f"{topic} architecture scalability design patterns",
        "performance": f"{topic} performance benchmarks optimization latency",
        "security": f"{topic} security vulnerabilities best practices"
    }
    
    tool = get_search_tool()
    
    for agent in active_agents:
        query = search_queries.get(agent, topic)
        results = tool.search(query, max_results=3)
        
        for result in results:
            evidence_items.append({
                "agent": agent,
                "query": query,
                "title": result["title"],
                "url": result["url"],
                "summary": result["content"][:500],  # Truncate for brevity
                "score": result.get("score", 0.0)
            })
    
    return {
        "evidence": evidence_items,
        "current_phase": "debate"
    }
