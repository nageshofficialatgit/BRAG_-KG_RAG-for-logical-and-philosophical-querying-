from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict, Any
import logging
import httpx
from backend.services.rag_service import RAGService
from backend.services.kg_service import KnowledgeGraphService
from backend.services.web_crawler_service import WebCrawlerService
from backend.services.image_service import ImageService
from backend.services.llm_service import LLMService
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Global service instances (in production, use dependency injection properly)
_kg_service = None
_web_crawler = None
_image_service = None
_llm_service = None

def get_rag_service(
    llm_provider: str = "ollama",
    model: Optional[str] = None
) -> RAGService:
    """Get RAG service with proper dependencies"""
    global _kg_service, _web_crawler, _image_service, _llm_service
    
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    
    if _web_crawler is None:
        _web_crawler = WebCrawlerService()
    
    if _image_service is None:
        _image_service = ImageService()
    
    # LLM service can change based on provider
    _llm_service = LLMService(provider=llm_provider, model=model)
    
    return RAGService(
        kg_service=_kg_service,
        web_crawler=_web_crawler,
        image_service=_image_service,
        llm_service=_llm_service
    )

class RAGQueryRequest(BaseModel):
    question: str
    chat_history: List[Tuple[str, str]] = []
    llm_provider: str = "ollama"
    model: Optional[str] = None
    include_web: bool = True
    include_images: bool = True
    sources: Optional[List[str]] = None  # Filter by specific books/sources

@router.post("/query")
async def query_rag(request: RAGQueryRequest):
    """Query the RAG system"""
    try:
        rag_service = get_rag_service(
            llm_provider=request.llm_provider,
            model=request.model
        )
        result = await rag_service.query(
            question=request.question,
            chat_history=request.chat_history,
            include_web=request.include_web,
            include_images=request.include_images,
            sources=request.sources
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_llm_providers():
    """Get available LLM providers with dynamic Ollama model detection"""
    # Try to get available Ollama models dynamically
    ollama_models = ["gemma3:4b", "llama3.2", "llama3", "mistral", "phi3", "gemma2:2b"]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                ollama_models = [model.get("name", "") for model in data.get("models", [])]
                logger.info(f"Detected Ollama models: {ollama_models}")
    except Exception as e:
        logger.warning(f"Could not fetch Ollama models dynamically: {e}, using defaults")
    
    return {
        "providers": [
            {
                "name": "ollama",
                "description": "Local Ollama models",
                "models": ollama_models,
                "default": settings.DEFAULT_OLLAMA_MODEL
            },
            {
                "name": "openai",
                "description": "OpenAI API",
                "models": ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
            }
        ],
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "default_model": settings.DEFAULT_OLLAMA_MODEL if settings.DEFAULT_LLM_PROVIDER == "ollama" else None
    }
