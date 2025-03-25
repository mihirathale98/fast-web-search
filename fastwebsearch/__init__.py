"""
Fast Web Search - A fast and efficient web search library
"""

__version__ = "0.1.0"

from .core import FastWebSearch
from .models import SearchResult, Proxy, ScrapeResult
from .search_engines import SearchEngine, BraveSearchEngine

__all__ = [
    "FastWebSearch",
    "SearchResult",
    "Proxy",
    "ScrapeResult",
    "SearchEngine",
    "BraveSearchEngine",
]
