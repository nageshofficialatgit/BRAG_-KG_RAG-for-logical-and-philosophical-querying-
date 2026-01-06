from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict, Any
import logging
import httpx
from uuid import uuid4
from backend.services.rag_service import RAGService
from backend.services.kg_service import KnowledgeGraphService
from backend.services.web_crawler_service import WebCrawlerService
from backend.services.image_service import ImageService
from backend.services.llm_service import LLMService
from backend.services.conversation_memory_service import ConversationMemoryService
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Global service instances
_kg_service = None
_web_crawler = None
_image_service = None
_llm_service = None
_memory_services: Dict[str, ConversationMemoryService] = {}  # session_id -> memory service

def get_rag_service(
    llm_provider: str = "ollama",
    model: Optional[str] = None,
    session_id: Optional[str] = None
) -> RAGService:
    """Get RAG service with proper dependencies including memory"""
    global _kg_service, _web_crawler, _image_service, _llm_service, _memory_services
    
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    
    if _web_crawler is None:
        _web_crawler = WebCrawlerService()
    
    if _image_service is None:
        _image_service = ImageService()
    
    # LLM service can change based on provider
    _llm_service = LLMService(provider=llm_provider, model=model)
    
    # Get or create memory service for session
    memory_service = None
    if session_id:
        if session_id not in _memory_services:
            # Create new conversation memory for this session (config-driven)
            _memory_services[session_id] = ConversationMemoryService(
                llm=_llm_service.llm,
                neo4j_graph=_kg_service.neo4j_graph,
                session_id=session_id,
                max_history=settings.MEMORY_MAX_HISTORY,
                enable_archival=settings.MEMORY_ENABLE_ARCHIVAL,
                enable_importance_scoring=settings.MEMORY_ENABLE_IMPORTANCE_SCORING
            )
        memory_service = _memory_services[session_id]
    
    return RAGService(
        kg_service=_kg_service,
        web_crawler=_web_crawler,
        image_service=_image_service,
        llm_service=_llm_service,
        memory_service=memory_service
    )

class RAGQueryRequest(BaseModel):
    question: str
    chat_history: List[Tuple[str, str]] = []
    session_id: Optional[str] = None  # Conversation session ID for memory
    llm_provider: str = settings.DEFAULT_LLM_PROVIDER  # From config
    model: Optional[str] = None  # Uses default from config if None
    include_web: bool = settings.ROUTER_DEFAULT_INCLUDE_WEB  # From config
    include_images: bool = settings.ROUTER_DEFAULT_INCLUDE_IMAGES  # From config
    sources: Optional[List[str]] = None  # Filter by specific books/sources

@router.post("/query")
async def query_rag(request: RAGQueryRequest):
    """Query the RAG system with optional conversation memory"""
    try:
        # Create session if not provided (using config prefix)
        session_id = request.session_id or f"{settings.MEMORY_SESSION_ID_PREFIX}_{uuid4().hex[:8]}"
        
        rag_service = get_rag_service(
            llm_provider=request.llm_provider,
            model=request.model,
            session_id=session_id
        )
        
        result = await rag_service.query(
            question=request.question,
            chat_history=request.chat_history,
            include_web=request.include_web,
            include_images=request.include_images,
            sources=request.sources,
            session_id=session_id
        )
        return result
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/create")
async def create_session():
    """Create a new conversation session"""
    try:
        session_id = f"{settings.MEMORY_SESSION_ID_PREFIX}_{uuid4().hex[:8]}"
        # Initialize memory service for this session
        _ = get_rag_service(session_id=session_id)
        return {
            "session_id": session_id,
            "created": True,
            "message": f"Session {session_id} created. Use this session_id in query requests to maintain conversation memory."
        }
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a conversation session"""
    try:
        if session_id not in _memory_services:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        memory = _memory_services[session_id]
        session_info = memory.get_session_info()
        health = memory._assess_memory_health()
        
        return {
            "session_id": session_id,
            "info": session_info,
            "health": health
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session info error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear/delete a conversation session"""
    try:
        if session_id not in _memory_services:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        memory = _memory_services[session_id]
        await memory.clear_history()
        
        # Keep the session but cleared
        return {
            "session_id": session_id,
            "cleared": True,
            "message": f"Session {session_id} conversation history cleared"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session clear error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str):
    """Get current conversation context for a session"""
    try:
        if session_id not in _memory_services:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        memory = _memory_services[session_id]
        context_data = await memory.get_conversation_context(
            max_tokens=settings.ROUTER_SESSION_CONTEXT_MAX_TOKENS
        )
        
        return {
            "session_id": session_id,
            "context_data": context_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session context error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_llm_providers():
    """Get available LLM providers with dynamic Ollama model detection"""
    # Try to get available Ollama models dynamically, fallback to defaults from config
    ollama_models = settings.DEFAULT_OLLAMA_FALLBACK_MODELS.copy()
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
        logger.warning(f"Could not fetch Ollama models dynamically: {e}, using defaults from config")
    
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
                "models": settings.AVAILABLE_OPENAI_MODELS
            }
        ],
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "default_model": settings.DEFAULT_OLLAMA_MODEL if settings.DEFAULT_LLM_PROVIDER == "ollama" else settings.AVAILABLE_OPENAI_MODELS[0]
    }
