from typing import List, Dict, Any, Optional
import httpx
import logging
import re
import json
from backend.config import settings
from backend.constants import APIEndpoints, DEFAULT_HEADERS
import base64

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.enabled = settings.ENABLE_IMAGE_SEARCH
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            **DEFAULT_HEADERS
        }
    
    async def search_images(
        self,
        query: str,
        num_results: int = 5,
        providers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for images using multiple providers"""
        if not self.enabled:
            return []
        
        providers = providers or ["duckduckgo", "unsplash", "pexels"]
        all_results = []
        seen_urls = set()
        
        # Try providers in order until we have enough results
        for provider in providers:
            if len(all_results) >= num_results:
                break
            
            try:
                if provider == "duckduckgo":
                    results = await self._duckduckgo_image_search(query, num_results)
                elif provider == "unsplash":
                    results = await self._unsplash_search(query, num_results)
                elif provider == "pexels":
                    results = await self._pexels_search(query, num_results)
                elif provider == "bing":
                    results = await self._bing_image_search(query, num_results)
                else:
                    continue
                
                # Deduplicate and add results
                for result in results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
                        if len(all_results) >= num_results:
                            break
            except Exception as e:
                logger.warning(f"Error with {provider} image search: {e}")
                continue
        
        return all_results[:num_results]
    
    async def _duckduckgo_image_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search DuckDuckGo for images with proper VQD token extraction"""
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
                # Step 1: Get VQD token
                vqd = await self._get_ddg_vqd(client, query)
                if not vqd:
                    logger.warning("Could not get VQD token for DuckDuckGo images")
                    return []
                
                # Step 2: Search images using API
                url = APIEndpoints.DUCKDUCKGO_IMAGES
                params = {
                    "q": query,
                    "vqd": vqd,
                    "o": "json",
                    "p": "1",
                    "s": "0"
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results = []
                        
                        for item in data.get("results", [])[:num_results]:
                            results.append({
                                "url": item.get("image", ""),
                                "thumbnail": item.get("thumbnail", item.get("image", "")),
                                "title": item.get("title", query),
                                "width": item.get("width"),
                                "height": item.get("height"),
                                "source": "duckduckgo",
                                "source_url": item.get("url", "")
                            })
                        
                        return results
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse DuckDuckGo image JSON")
                
                # Fallback: Try HTML scraping
                return await self._duckduckgo_image_html_search(query, num_results)
        except Exception as e:
            logger.error(f"DuckDuckGo image search error: {str(e)}")
            return []
    
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
                vqd_match = re.search(r'vqd=([\d-]+)', response.text)
                if vqd_match:
                    return vqd_match.group(1)
        except Exception as e:
            logger.warning(f"Error getting VQD: {e}")
        return None
    
    async def _duckduckgo_image_html_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback HTML scraping for DuckDuckGo images"""
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
                url = APIEndpoints.DUCKDUCKGO_BASE
                params = {"q": query, "iax": "images", "ia": "images"}
                response = await client.get(url, params=params)
                
                # This is a simplified fallback - actual implementation would parse HTML
                return []
        except Exception:
            return []
    
    async def _unsplash_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search Unsplash for images (requires API key)"""
        try:
            api_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
            if not api_key:
                logger.debug("Unsplash API key not configured")
                return []
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = APIEndpoints.UNSPLASH_SEARCH
                headers = {
                    "Authorization": f"Client-ID {api_key}"
                }
                params = {
                    "query": query,
                    "per_page": min(num_results, 30),
                    "orientation": "landscape"
                }
                
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("results", [])[:num_results]:
                        results.append({
                            "url": item["urls"].get("regular", item["urls"].get("full", "")),
                            "thumbnail": item["urls"].get("thumb", item["urls"].get("small", "")),
                            "title": item.get("description", query),
                            "width": item.get("width"),
                            "height": item.get("height"),
                            "source": "unsplash",
                            "author": item.get("user", {}).get("name", ""),
                            "author_url": item.get("user", {}).get("links", {}).get("html", ""),
                            "source_url": item.get("links", {}).get("html", "")
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Unsplash search error: {str(e)}")
        return []
    
    async def _pexels_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search Pexels for images (requires API key)"""
        try:
            api_key = getattr(settings, 'PEXELS_API_KEY', None)
            if not api_key:
                logger.debug("Pexels API key not configured")
                return []
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = APIEndpoints.PEXELS_SEARCH
                headers = {
                    "Authorization": api_key
                }
                params = {
                    "query": query,
                    "per_page": min(num_results, 15),
                    "orientation": "landscape"
                }
                
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("photos", [])[:num_results]:
                        results.append({
                            "url": item.get("src", {}).get("large", item.get("src", {}).get("original", "")),
                            "thumbnail": item.get("src", {}).get("medium", item.get("src", {}).get("small", "")),
                            "title": query,
                            "width": item.get("width"),
                            "height": item.get("height"),
                            "source": "pexels",
                            "author": item.get("photographer", ""),
                            "author_url": item.get("photographer_url", ""),
                            "source_url": item.get("url", "")
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Pexels search error: {str(e)}")
        return []
    
    async def _bing_image_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Search Bing for images (no API key required, but rate limited)"""
        try:
            api_key = getattr(settings, 'BING_SEARCH_API_KEY', None)
            
            if api_key:
                # Use Bing Image Search API
                return await self._bing_api_search(query, num_results, api_key)
            else:
                # Fallback to HTML scraping (less reliable)
                return await self._bing_html_image_search(query, num_results)
        except Exception as e:
            logger.error(f"Bing image search error: {str(e)}")
            return []
    
    async def _bing_api_search(
        self,
        query: str,
        num_results: int,
        api_key: str
    ) -> List[Dict[str, Any]]:
        """Search Bing using official API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = APIEndpoints.BING_IMAGE_API
                headers = {
                    "Ocp-Apim-Subscription-Key": api_key
                }
                params = {
                    "q": query,
                    "count": min(num_results, 35),
                    "imageType": "Photo",
                    "safeSearch": "Moderate"
                }
                
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("value", [])[:num_results]:
                        results.append({
                            "url": item.get("contentUrl", ""),
                            "thumbnail": item.get("thumbnailUrl", item.get("contentUrl", "")),
                            "title": item.get("name", query),
                            "width": item.get("width"),
                            "height": item.get("height"),
                            "source": "bing",
                            "source_url": item.get("hostPageUrl", "")
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Bing API search error: {str(e)}")
        return []
    
    async def _bing_html_image_search(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback HTML scraping for Bing images (less reliable)"""
        # This would require HTML parsing - simplified for now
        return []
    
    async def get_philosopher_images(
        self,
        philosopher_name: str,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get images for a specific philosopher with optimized query"""
        query = f"{philosopher_name} philosopher portrait"
        return await self.search_images(query, num_results=num_results)
    
    async def get_concept_images(
        self,
        concept: str,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get images for a philosophical concept"""
        query = f"{concept} philosophy concept"
        return await self.search_images(query, num_results=num_results)
