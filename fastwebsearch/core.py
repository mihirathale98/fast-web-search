"""
Core functionality for Fast Web Search
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import SearchResult
from .search_engines import SearchEngine

class FastWebSearch:
    """
    Main class for performing web searches with optimizations
    """
    
    def __init__(
        self,
        search_engine: SearchEngine,
        max_concurrent_searches: int = 5,
        rate_limit: int = 10,  # requests per second
        cache_ttl: int = 3600
    ):
        self.search_engine = search_engine
        self.max_concurrent_searches = max_concurrent_searches
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(max_concurrent_searches)
        self.last_request_time = datetime.now()
        
    async def _rate_limit(self):
        """Implement rate limiting"""
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        if time_since_last < 1.0 / self.rate_limit:
            await asyncio.sleep(1.0 / self.rate_limit - time_since_last)
        self.last_request_time = datetime.now()
        
    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Perform a web search with rate limiting
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        async with self.semaphore:
            await self._rate_limit()
            try:
                results = await self.search_engine.search(
                    query=query,
                    max_results=max_results
                )
                return results
            except Exception as e:
                print(f"Error searching for '{query}': {str(e)}")
                return []
                
    async def multi_search(
        self,
        queries: List[str],
        max_results: int = 10
    ) -> Dict[str, List[SearchResult]]:
        """
        Perform multiple searches concurrently
        
        Args:
            queries: List of search queries
            max_results: Maximum number of results per query
            
        Returns:
            Dictionary mapping queries to their results
        """
        # Create tasks for all queries
        tasks = []
        for query in queries:
            task = asyncio.create_task(self.search(query, max_results))
            tasks.append(task)
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Map results back to queries
        return dict(zip(queries, results))
