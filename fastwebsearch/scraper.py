import asyncio
import aiohttp
from urllib.parse import urlparse
import urllib.robotparser
from typing import List, Optional, Dict
from itertools import cycle
from .models import ScrapeResult, Proxy
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Cache for robots.txt parsers per domain
_robot_parsers = {}

def allowed_by_robots(url: str, user_agent: str = "fast-web-search") -> bool:
    """
    Check if the given URL is allowed to be fetched based on its robots.txt.
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    if base_url not in _robot_parsers:
        robots_url = f"{base_url}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception as e:
            # In case of failure reading robots.txt, assume allowed
            rp = None
        _robot_parsers[base_url] = rp
    rp = _robot_parsers.get(base_url)
    if rp:
        return rp.can_fetch(user_agent, url)
    return True

async def fetch(session: aiohttp.ClientSession, url: str, proxy_cycle: cycle, user_agent: str = "fast-web-search", max_retries: int = 3) -> ScrapeResult:
    """
    Asynchronously fetch the content of a URL using retries, backoff and robots.txt checking.
    """
    # Check robots.txt using a thread to avoid blocking the event loop.
    allowed = await asyncio.to_thread(allowed_by_robots, url, user_agent)
    if not allowed:
        return ScrapeResult(url=url, error="Disallowed by robots.txt")

    backoff = 1
    for attempt in range(max_retries):
        proxy = next(proxy_cycle)
        try:
            async with session.get(url, proxy=proxy, timeout=5) as response:
                text = await response.text()
                return ScrapeResult(url=url, content=text)
        except Exception as e:
            print(f"Attempt {attempt+1}: Error fetching {url} with proxy {proxy}: {e}")
            await asyncio.sleep(backoff)
            backoff *= 2  # exponential backoff
    return ScrapeResult(url=url, error="Failed after retries")

async def scrape_urls(urls: List[str], proxy_cycle: cycle, user_agent: str = "fast-web-search", max_retries: int = 3) -> List[ScrapeResult]:
    """
    Asynchronously scrape multiple URLs.
    """
    tasks = []
    connector = aiohttp.TCPConnector(limit_per_host=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for url in urls:
            tasks.append(fetch(session, url, proxy_cycle, user_agent, max_retries))
        results = await asyncio.gather(*tasks)
    return results

class WebScraper:
    """
    Handles web scraping operations with connection pooling and caching
    """
    
    def __init__(self, cache_ttl: int = 3600, max_connections: int = 10):
        self.session = None
        self.cache: Dict[str, tuple[str, datetime]] = {}
        self.cache_ttl = cache_ttl
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_page_content(
        self,
        url: str,
        proxy: Optional[Proxy] = None,
        use_cache: bool = True
    ) -> str:
        """
        Fetch and parse webpage content with caching
        
        Args:
            url: URL to fetch
            proxy: Optional proxy to use
            use_cache: Whether to use cached content
            
        Returns:
            Parsed HTML content
        """
        # Check cache first
        if use_cache and url in self.cache:
            content, timestamp = self.cache[url]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return content
                
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        proxy_url = None
        if proxy:
            proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                
        async with self.semaphore:  # Limit concurrent connections
            try:
                async with self.session.get(url, proxy=proxy_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        content = soup.get_text()
                        
                        # Cache the result
                        self.cache[url] = (content, datetime.now())
                        return content
                    else:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
            except Exception as e:
                raise aiohttp.ClientError(f"Failed to fetch {url}: {str(e)}")
                
    def clear_cache(self):
        """Clear the content cache"""
        self.cache.clear()
