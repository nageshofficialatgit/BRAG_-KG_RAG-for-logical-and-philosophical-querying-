from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse, quote_plus
from backend.config import settings
import asyncio
import re
import json
from datetime import datetime
from backend.services.robots_parser import RobotsParser, RateLimiter
from backend.services.philosophy_search_enhancer import PhilosophySearchEnhancer
from backend.constants import APIEndpoints, DEFAULT_HEADERS, USER_AGENT
from backend.config import settings

logger = logging.getLogger(__name__)

class WebCrawlerService:
    def __init__(self, respect_robots: bool = None):
        self.timeout = settings.CRAWL_TIMEOUT
        self.max_results = settings.MAX_SEARCH_RESULTS
        self.respect_robots = respect_robots if respect_robots is not None else settings.RESPECT_ROBOTS_TXT
        self.user_agent = settings.USER_AGENT
        
        self.headers = {
            "User-Agent": self.user_agent,
            **DEFAULT_HEADERS
        }
        
        # Initialize robots.txt parser and rate limiter
        if self.respect_robots:
            self.robots_parser = RobotsParser(user_agent=self.user_agent)
            self.rate_limiter = RateLimiter()
        else:
            self.robots_parser = None
            self.rate_limiter = None
        
        # Initialize philosophy search enhancer
        self.philosophy_enhancer = PhilosophySearchEnhancer()
    
    async def search_web(
        self,
        query: str,
        num_results: int = None,
        search_engines: Optional[List[str]] = None,
        prioritize_philosophy: bool = True,
        min_quality_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search the web using multiple search engines with philosophy-specific enhancement"""
        num_results = num_results or self.max_results
        search_engines = search_engines or ["duckduckgo", "bing"]
        
        # Enhance queries for better philosophy results
        enhanced_queries = self.philosophy_enhancer.enhance_query(query)
        
        # Get direct philosophy source links first
        philosophy_sources = self.philosophy_enhancer.get_philosophy_specific_sources(query)
        
        all_results = []
        seen_urls = set()
        
        # Add philosophy-specific sources
        for source in philosophy_sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(source)
        
        # Search using multiple engines with enhanced queries
        tasks = []
        from backend.constants import SearchConfig
        query_multiplier = SearchConfig.QUERY_MULTIPLIER
        max_query_variations = 2  # Use top 2 enhanced queries
        
        for enhanced_query in enhanced_queries[:max_query_variations]:
            if "duckduckgo" in search_engines:
                tasks.append(self._duckduckgo_search(enhanced_query, num_results * query_multiplier))
            if "bing" in search_engines:
                tasks.append(self._bing_search(enhanced_query, num_results * query_multiplier))
            if "serper" in search_engines and hasattr(settings, 'SERPER_API_KEY'):
                tasks.append(self._serper_search(enhanced_query, num_results * query_multiplier))
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate and deduplicate results
        for results in results_list:
            if isinstance(results, Exception):
                logger.error(f"Search error: {results}")
                continue
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)
        
        # Filter and rank by quality
        filtered_results = self.philosophy_enhancer.filter_and_rank_results(
            all_results,
            min_quality_score=min_quality_score,
            prioritize_philosophy=prioritize_philosophy
        )
        
        return filtered_results[:num_results]
    
    async def _duckduckgo_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo with improved scraping"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # Get VQD token first
                vqd = await self._get_ddg_vqd(client, query)
                if not vqd:
                    # Fallback to HTML search
                    return await self._duckduckgo_html_search(query, num_results)
                
                # Use DuckDuckGo API
                url = APIEndpoints.DUCKDUCKGO_LINKS
                params = {
                    "q": query,
                    "vqd": vqd,
                    "o": "json",
                    "p": "1",
                    "s": "0"
                }
                
                response = await client.get(url, params=params)
                results = []
                
                if response.status_code == 200:
                    try:
                        # DuckDuckGo returns JavaScript, need to extract JSON
                        text = response.text
                        # Extract JSON from JavaScript response
                        json_match = re.search(r'DDG\.pageLayout\.load\("d",(\[.*?\]),', text)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            for item in data[:num_results]:
                                if isinstance(item, dict):
                                    results.append({
                                        "title": item.get("t", ""),
                                        "snippet": item.get("a", ""),
                                        "url": item.get("u", ""),
                                        "source": "duckduckgo"
                                    })
                    except Exception as e:
                        logger.warning(f"Error parsing DuckDuckGo JSON: {e}")
                
                # Fallback to HTML if API doesn't work
                if not results:
                    return await self._duckduckgo_html_search(query, num_results)
                
                return results[:num_results]
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return await self._duckduckgo_html_search(query, num_results)
    
    async def _get_ddg_vqd(self, client: httpx.AsyncClient, query: str) -> Optional[str]:
        """Get VQD token from DuckDuckGo"""
        try:
            url = APIEndpoints.DUCKDUCKGO_BASE
            params = {"q": query}
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                # Extract VQD from response
                vqd_match = re.search(r'vqd="([^"]+)"', response.text)
                if vqd_match:
                    return vqd_match.group(1)
                # Alternative pattern
                vqd_match = re.search(r'vqd=([\d-]+)', response.text)
                if vqd_match:
                    return vqd_match.group(1)
        except Exception as e:
            logger.warning(f"Error getting VQD: {e}")
        return None
    
    async def _duckduckgo_html_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback HTML scraping for DuckDuckGo"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                url = APIEndpoints.DUCKDUCKGO_HTML
                params = {"q": query}
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    
                    # Find result links - updated selectors
                    result_divs = soup.find_all('div', class_='result')[:num_results]
                    
                    for div in result_divs:
                        link = div.find('a', class_='result__a')
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        url = link.get('href', '')
                        
                        # Get snippet
                        snippet_elem = div.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if title and url:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "url": url,
                                "source": "duckduckgo_html"
                            })
                    
                    return results
        except Exception as e:
            logger.error(f"DuckDuckGo HTML search error: {str(e)}")
        return []
    
    async def _bing_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search using Bing (no API key required)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                url = APIEndpoints.BING_SEARCH
                params = {
                    "q": query,
                    "count": min(num_results, 20),
                    "first": 1
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    
                    # Find search results
                    result_items = soup.find_all('li', class_='b_algo')[:num_results]
                    
                    for item in result_items:
                        title_elem = item.find('h2')
                        if not title_elem:
                            continue
                        
                        link = title_elem.find('a')
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        url = link.get('href', '')
                        
                        # Get snippet
                        snippet_elem = item.find('p')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if title and url:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "url": url,
                                "source": "bing"
                            })
                    
                    return results
        except Exception as e:
            logger.error(f"Bing search error: {str(e)}")
        return []
    
    async def _serper_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search using Serper API (requires API key)"""
        try:
            api_key = getattr(settings, 'SERPER_API_KEY', None)
            if not api_key:
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = APIEndpoints.SERPER_SEARCH
                headers = {
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": query,
                    "num": num_results
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("organic", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "url": item.get("link", ""),
                            "source": "serper"
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Serper search error: {str(e)}")
        return []
    
    async def fetch_page_content(
        self,
        url: str,
        max_length: int = 10000,
        check_robots: bool = True
    ) -> Dict[str, Any]:
        """Fetch and extract content from a web page with improved extraction and robots.txt compliance"""
        try:
            # Check robots.txt if enabled
            if self.respect_robots and check_robots and self.robots_parser:
                can_fetch = await self.robots_parser.can_fetch(url, self.user_agent)
                if not can_fetch:
                    logger.info(f"Blocked by robots.txt: {url}")
                    return {
                        "url": url,
                        "success": False,
                        "error": "Blocked by robots.txt",
                        "blocked_by_robots": True
                    }
                
                # Get crawl delay and wait if needed
                crawl_delay = await self.robots_parser.get_crawl_delay(url, self.user_agent)
                if self.rate_limiter:
                    await self.rate_limiter.wait_if_needed(url, crawl_delay)
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "footer", "header", 
                                        "aside", "iframe", "noscript", "meta"]):
                        element.decompose()
                    
                    # Extract main content using multiple strategies
                    content = self._extract_main_content(soup)
                    
                    # Get metadata
                    title = self._extract_title(soup)
                    description = self._extract_description(soup)
                    author = self._extract_author(soup)
                    published_date = self._extract_published_date(soup)
                    
                    # Clean and limit content
                    content = self._clean_text(content)
                    if len(content) > max_length:
                        content = content[:max_length] + "..."
                    
                    return {
                        "url": url,
                        "title": title,
                        "description": description,
                        "author": author,
                        "published_date": published_date,
                        "content": content,
                        "word_count": len(content.split()),
                        "success": True,
                        "fetched_at": datetime.utcnow().isoformat(),
                        "robots_respected": self.respect_robots and check_robots
                    }
        except httpx.TimeoutException:
            return {
                "url": url,
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using multiple strategies"""
        # Strategy 1: Look for article tag
        article = soup.find('article')
        if article:
            return article.get_text(separator=' ', strip=True)
        
        # Strategy 2: Look for main tag
        main = soup.find('main')
        if main:
            return main.get_text(separator=' ', strip=True)
        
        # Strategy 3: Look for common content classes
        content_selectors = [
            'div.content',
            'div.post-content',
            'div.entry-content',
            'div.article-content',
            'div.main-content',
            'div[role="main"]'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                return content_div.get_text(separator=' ', strip=True)
        
        # Strategy 4: Get all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Fallback: Get all text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        # Try title tag
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        # Try h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information"""
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content']
        
        # Try Open Graph author
        og_author = soup.find('meta', property='article:author')
        if og_author and og_author.get('content'):
            return og_author['content']
        
        # Try JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'author' in data:
                    author = data['author']
                    if isinstance(author, dict):
                        return author.get('name', '')
                    return str(author)
            except:
                pass
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published date"""
        # Try meta date
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date and meta_date.get('content'):
            return meta_date['content']
        
        # Try time tag
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            return time_tag['datetime']
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    async def search_and_summarize(
        self,
        query: str,
        llm_service,
        num_results: int = None,
        fetch_full_content: bool = False,
        respect_robots: bool = True,
        prioritize_philosophy: bool = True
    ) -> Dict[str, Any]:
        """Search web and summarize results using LLM with improved context, robots.txt compliance, and philosophy-specific enhancement"""
        results = await self.search_web(
            query,
            num_results=num_results,
            prioritize_philosophy=prioritize_philosophy,
            min_quality_score=0.0  # Filter out very low quality results
        )
        
        if not results:
            return {
                "query": query,
                "summary": "No results found",
                "sources": []
            }
        
        # Optionally fetch full content for better summarization
        # Filter out URLs blocked by robots.txt if enabled
        if fetch_full_content:
            # Check robots.txt for all URLs first
            valid_urls = []
            if self.respect_robots and respect_robots and self.robots_parser:
                for result in results[:3]:
                    can_fetch = await self.robots_parser.can_fetch(result['url'], self.user_agent)
                    if can_fetch:
                        valid_urls.append(result)
                    else:
                        logger.info(f"Skipping {result['url']} - blocked by robots.txt")
            else:
                valid_urls = results[:3]
            
            fetch_tasks = [self.fetch_page_content(r['url'], check_robots=respect_robots) for r in valid_urls]
            fetched_pages = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            
            # Use full content if available
            for i, page in enumerate(fetched_pages):
                if isinstance(page, dict) and page.get('success') and i < len(results):
                    results[i]['full_content'] = page.get('content', '')[:2000]
        
        # Combine snippets and content
        combined_text = "\n\n".join([
            f"Title: {r['title']}\n"
            f"Snippet: {r.get('snippet', r.get('full_content', ''))}\n"
            f"URL: {r['url']}\n"
            f"Source: {r.get('source', 'unknown')}"
            for r in results
        ])
        
        # Enhanced summarization prompt
        prompt = f"""You are a research assistant. Summarize the following search results about: {query}

Search Results:
{combined_text}

Provide a comprehensive, well-structured summary that:
1. Directly answers the query
2. Synthesizes information from multiple sources
3. Highlights key points and insights
4. Notes any conflicting information
5. Cites sources when making specific claims

Summary:"""
        
        try:
            summary = await llm_service.ainvoke(prompt)
        except Exception as e:
            logger.error(f"Error summarizing: {str(e)}")
            # Fallback: create a simple summary
            summary = f"Found {len(results)} results about '{query}'. " + \
                     " ".join([r.get('snippet', '')[:100] for r in results[:3]])
        
        return {
            "query": query,
            "summary": summary,
            "sources": results,
            "num_results": len(results)
        }
