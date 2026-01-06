from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.services.web_crawler_service import WebCrawlerService
from backend.services.llm_service import LLMService

router = APIRouter()

def get_web_crawler():
    return WebCrawlerService()

class SearchRequest(BaseModel):
    query: str
    num_results: int = 5
    search_engines: Optional[List[str]] = None  # ["duckduckgo", "bing", "serper"]
    prioritize_philosophy: bool = True  # Prioritize philosophy-specific sources
    min_quality_score: float = 0.0  # Minimum quality score (0-20+)

class FetchRequest(BaseModel):
    url: str
    max_length: int = 10000
    check_robots: bool = True  # Check robots.txt before fetching

class SummarizeRequest(BaseModel):
    query: str
    num_results: int = 5
    llm_provider: str = "ollama"
    model: Optional[str] = None
    fetch_full_content: bool = False  # Fetch full page content for better summarization
    respect_robots: bool = True  # Respect robots.txt when fetching content
    prioritize_philosophy: bool = True  # Prioritize philosophy-specific sources

@router.post("/search")
async def search_web(
    request: SearchRequest,
    crawler: WebCrawlerService = Depends(get_web_crawler)
):
    """Search the web for information using multiple search engines"""
    try:
        results = await crawler.search_web(
            query=request.query,
            num_results=request.num_results,
            search_engines=request.search_engines,
            prioritize_philosophy=request.prioritize_philosophy,
            min_quality_score=request.min_quality_score
        )
        return {
            "results": results,
            "count": len(results),
            "query": request.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch")
async def fetch_page(
    request: FetchRequest,
    crawler: WebCrawlerService = Depends(get_web_crawler)
):
    """Fetch and extract content from a web page with improved extraction"""
    try:
        result = await crawler.fetch_page_content(
            request.url,
            max_length=request.max_length,
            check_robots=request.check_robots
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def search_and_summarize(
    request: SummarizeRequest,
    crawler: WebCrawlerService = Depends(get_web_crawler)
):
    """Search web and summarize results"""
    try:
        llm_service = LLMService(
            provider=request.llm_provider,
            model=request.model
        )
        result = await crawler.search_and_summarize(
            query=request.query,
            llm_service=llm_service,
            num_results=request.num_results,
            fetch_full_content=request.fetch_full_content,
            respect_robots=request.respect_robots,
            prioritize_philosophy=request.prioritize_philosophy
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
