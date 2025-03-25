"""
Data models for Fast Web Search
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class SearchResult:
    """
    Represents a single search result
    """
    title: str
    url: str
    snippet: str
    timestamp: datetime
    source: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Proxy:
    """
    Represents a proxy server
    """
    host: str
    port: int
    protocol: str
    username: Optional[str] = None
    password: Optional[str] = None
    last_used: Optional[datetime] = None
    success_rate: float = 0.0

@dataclass
class ScrapeResult:
    """
    Represents a scraped webpage result
    """
    url: str
    content: str
    error: Optional[str] = None
    timestamp: datetime = datetime.now()
