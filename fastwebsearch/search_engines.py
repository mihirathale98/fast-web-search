"""
Search engine implementations for Fast Web Search
"""

from abc import ABC, abstractmethod
import aiohttp
import json
from typing import List, Optional, Dict
from datetime import datetime
from .models import SearchResult, Proxy

class SearchEngine(ABC):
    """
    Abstract base class for search engines
    """
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        proxy: Optional[Proxy] = None
    ) -> List[SearchResult]:
        """
        Perform a search query
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            proxy: Optional proxy to use
            
        Returns:
            List of search results
        """
        pass

class BraveSearchEngine(SearchEngine):
    """
    Brave search engine implementation
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self._session = None
        
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            
    async def search(
        self,
        query: str,
        max_results: int = 10,
        proxy: Optional[Proxy] = None
    ) -> List[SearchResult]:
        """
        Perform a search using Brave Search API
        """
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": max_results,
            "search_lang": "en",
            "result_filter": "web",
            "text_format": "plain"
        }
        
        proxy_url = None
        if proxy:
            proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                
        try:
            async with self.session.get(
                self.base_url,
                headers=headers,
                params=params,
                proxy=proxy_url,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # Debug print
                    print(f"\nAPI Response for '{query}':")
                    print(json.dumps(data, indent=2))
                    
                    web_results = data.get("web", {}).get("results", [])
                    if not web_results:
                        print(f"No results found for query: {query}")
                        return []
                        
                    for web_result in web_results:
                        try:
                            result = SearchResult(
                                title=web_result.get("title", ""),
                                url=web_result.get("url", ""),
                                snippet=web_result.get("description", ""),
                                timestamp=datetime.now(),
                                source="brave",
                                metadata={
                                    "age": web_result.get("age", ""),
                                    "language": web_result.get("language", ""),
                                    "family_friendly": web_result.get("family_friendly", False)
                                }
                            )
                            results.append(result)
                        except Exception as e:
                            print(f"Error processing result for query '{query}': {e}")
                            continue
                            
                    return results
                else:
                    error_text = await response.text()
                    print(f"API Error for query '{query}': Status {response.status}")
                    print(f"Response: {error_text}")
                    raise aiohttp.ClientError(f"Brave API error: {response.status} - {error_text}")
        except Exception as e:
            print(f"Exception during search for '{query}': {str(e)}")
            raise aiohttp.ClientError(f"Failed to search with Brave: {str(e)}")
