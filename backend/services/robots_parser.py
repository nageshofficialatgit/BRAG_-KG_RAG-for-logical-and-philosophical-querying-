"""
Robots.txt parser and compliance checker for respectful web crawling
"""
import httpx
import re
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Set
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class RobotsParser:
    """Parse and check robots.txt compliance"""
    
    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=24)  # Cache robots.txt for 24 hours
    
    async def can_fetch(
        self,
        url: str,
        user_agent: Optional[str] = None
    ) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        user_agent = user_agent or self.user_agent
        
        # Get robots.txt rules
        rules = await self._get_robots_txt(robots_url)
        
        if not rules:
            # If we can't fetch robots.txt, be conservative and allow
            return True
        
        # Check if path is allowed
        path = parsed.path or "/"
        return self._is_path_allowed(path, rules, user_agent)
    
    async def get_crawl_delay(
        self,
        url: str,
        user_agent: Optional[str] = None
    ) -> float:
        """Get crawl delay in seconds for the URL"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        user_agent = user_agent or self.user_agent
        
        rules = await self._get_robots_txt(robots_url)
        if not rules:
            return 1.0  # Default delay
        
        return rules.get("crawl_delay", {}).get(user_agent, rules.get("crawl_delay", {}).get("*", 1.0))
    
    async def get_sitemaps(self, url: str) -> List[str]:
        """Get sitemap URLs from robots.txt"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        rules = await self._get_robots_txt(robots_url)
        if not rules:
            return []
        
        return rules.get("sitemaps", [])
    
    async def _get_robots_txt(self, robots_url: str) -> Optional[Dict]:
        """Fetch and parse robots.txt"""
        # Check cache
        if robots_url in self.cache:
            cached = self.cache[robots_url]
            if datetime.now() - cached["timestamp"] < self.cache_ttl:
                return cached["rules"]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(robots_url)
                
                if response.status_code == 200:
                    rules = self._parse_robots_txt(response.text)
                    self.cache[robots_url] = {
                        "rules": rules,
                        "timestamp": datetime.now()
                    }
                    return rules
                elif response.status_code == 404:
                    # No robots.txt means all allowed
                    return {"allow": [], "disallow": [], "crawl_delay": {}, "sitemaps": []}
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt from {robots_url}: {e}")
            # If we can't fetch, be conservative
            return None
        
        return None
    
    def _parse_robots_txt(self, content: str) -> Dict:
        """Parse robots.txt content"""
        rules = {
            "allow": {},      # {user_agent: [paths]}
            "disallow": {},   # {user_agent: [paths]}
            "crawl_delay": {}, # {user_agent: delay}
            "sitemaps": []
        }
        
        current_user_agent = None
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse directive
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                
                if directive == 'user-agent':
                    current_user_agent = value.lower()
                    if current_user_agent not in rules["allow"]:
                        rules["allow"][current_user_agent] = []
                        rules["disallow"][current_user_agent] = []
                
                elif directive == 'allow' and current_user_agent:
                    if current_user_agent in rules["allow"]:
                        rules["allow"][current_user_agent].append(value)
                
                elif directive == 'disallow' and current_user_agent:
                    if current_user_agent in rules["disallow"]:
                        rules["disallow"][current_user_agent].append(value)
                
                elif directive == 'crawl-delay' and current_user_agent:
                    try:
                        delay = float(value)
                        rules["crawl_delay"][current_user_agent] = delay
                    except ValueError:
                        pass
                
                elif directive == 'sitemap':
                    rules["sitemaps"].append(value)
        
        return rules
    
    def _is_path_allowed(self, path: str, rules: Dict, user_agent: str) -> bool:
        """Check if a path is allowed for the user agent"""
        # Check specific user agent first
        if user_agent in rules["disallow"] or user_agent in rules["allow"]:
            disallow_patterns = rules["disallow"].get(user_agent, [])
            allow_patterns = rules["allow"].get(user_agent, [])
        else:
            # Fall back to wildcard
            disallow_patterns = rules["disallow"].get("*", [])
            allow_patterns = rules["allow"].get("*", [])
        
        # If no rules for this user agent, allow
        if not disallow_patterns and not allow_patterns:
            return True
        
        # Check disallow patterns first (more restrictive)
        for pattern in disallow_patterns:
            if pattern == "/":
                # Disallow all
                return False
            if self._matches_pattern(path, pattern):
                # Check if there's an allow that overrides
                for allow_pattern in allow_patterns:
                    if self._matches_pattern(path, allow_pattern):
                        return True
                return False
        
        # Check allow patterns
        if allow_patterns:
            for pattern in allow_patterns:
                if self._matches_pattern(path, pattern):
                    return True
            # If we have allow patterns but none match, disallow
            return False
        
        # No disallow matched, so allow
        return True
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches robots.txt pattern"""
        # Convert robots.txt pattern to regex
        # * matches any sequence of characters
        # $ matches end of string
        regex_pattern = pattern.replace('*', '.*').replace('$', '$')
        
        # Anchor to start of path
        if not regex_pattern.startswith('^'):
            regex_pattern = '^' + regex_pattern
        
        # Add end anchor if pattern ends with $
        if not regex_pattern.endswith('$'):
            regex_pattern = regex_pattern + '.*'
        
        try:
            return bool(re.match(regex_pattern, path))
        except re.error:
            # If regex fails, do simple string matching
            return pattern in path

class RateLimiter:
    """Rate limiter to respect crawl delays"""
    
    def __init__(self):
        self.delays: Dict[str, datetime] = {}
        self.default_delay = 1.0  # Default 1 second between requests
    
    async def wait_if_needed(self, url: str, delay: float):
        """Wait if needed based on crawl delay"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain in self.delays:
            last_request = self.delays[domain]
            time_since = (datetime.now() - last_request).total_seconds()
            if time_since < delay:
                wait_time = delay - time_since
                await asyncio.sleep(wait_time)
        
        self.delays[domain] = datetime.now()
