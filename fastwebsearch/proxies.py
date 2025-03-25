"""
Proxy management for Fast Web Search
"""

import random
import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from .models import Proxy

class ProxyManager:
    """
    Manages proxy rotation and health checking
    """
    
    def __init__(self, proxies: List[Proxy], verify_timeout: float = 5.0):
        self.proxies = proxies
        self.working_proxies = proxies.copy()
        self.verify_timeout = verify_timeout
        self.proxy_stats: Dict[Proxy, Dict] = {}
        for proxy in proxies:
            self.proxy_stats[proxy] = {
                "success_count": 0,
                "fail_count": 0,
                "avg_response_time": 0.0,
                "last_used": None,
                "last_verified": None
            }
        
    async def verify_proxy(self, proxy: Proxy) -> bool:
        """
        Verify if a proxy is working by making a test request
        
        Args:
            proxy: The proxy to verify
            
        Returns:
            bool: True if proxy is working, False otherwise
        """
        proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            
        try:
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.google.com",
                    proxy=proxy_url,
                    timeout=self.verify_timeout
                ) as response:
                    if response.status == 200:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        # Update proxy stats
                        stats = self.proxy_stats[proxy]
                        stats["success_count"] += 1
                        stats["avg_response_time"] = (
                            (stats["avg_response_time"] * (stats["success_count"] - 1) + response_time)
                            / stats["success_count"]
                        )
                        stats["last_verified"] = datetime.now()
                        return True
        except Exception as e:
            stats = self.proxy_stats[proxy]
            stats["fail_count"] += 1
            return False
            
        return False
        
    async def get_proxy(self) -> Optional[Proxy]:
        """
        Get a working proxy from the pool
        
        Returns:
            A proxy object or None if no working proxies available
        """
        if not self.working_proxies:
            return None
            
        # Sort proxies by success rate and response time
        sorted_proxies = sorted(
            self.working_proxies,
            key=lambda p: (
                self.proxy_stats[p]["success_count"] / (self.proxy_stats[p]["success_count"] + self.proxy_stats[p]["fail_count"] + 1),
                -self.proxy_stats[p]["avg_response_time"]  # Negative for descending order
            ),
            reverse=True
        )
        
        # Try the best proxies first
        for proxy in sorted_proxies[:3]:  # Try top 3 proxies
            if await self.verify_proxy(proxy):
                proxy.last_used = datetime.now()
                return proxy
                
        # If no working proxies found, try to verify all proxies
        tasks = [self.verify_proxy(proxy) for proxy in self.working_proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update working proxies list
        self.working_proxies = [
            proxy for proxy, is_working in zip(self.working_proxies, results)
            if isinstance(is_working, bool) and is_working
        ]
        
        if self.working_proxies:
            proxy = self.working_proxies[0]
            proxy.last_used = datetime.now()
            return proxy
            
        return None
        
    async def mark_proxy_failed(self, proxy: Proxy):
        """
        Mark a proxy as failed and adjust its success rate
        
        Args:
            proxy: The failed proxy
        """
        stats = self.proxy_stats[proxy]
        stats["fail_count"] += 1
        success_rate = stats["success_count"] / (stats["success_count"] + stats["fail_count"])
        
        if success_rate < 0.5:
            self.working_proxies.remove(proxy)
            
    async def mark_proxy_success(self, proxy: Proxy):
        """
        Mark a proxy as successful and adjust its success rate
        
        Args:
            proxy: The successful proxy
        """
        stats = self.proxy_stats[proxy]
        stats["success_count"] += 1
