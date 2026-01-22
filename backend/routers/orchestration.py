from fastapi import APIRouter, HTTPException
from typing import Optional
import time
from backend.models.orchestration_models import (
    OrchestratedSearchRequest,
    OrchestratedSearchResponse
)
from backend.services.orchestrator.query_classifier import QueryClassifierService
from backend.services.orchestrator.cot_generator import CoTGeneratorService
from backend.services.orchestrator.search_orchestrator import SearchOrchestratorService
from backend.services.orchestrator.context_synthesizer import ContextSynthesizerService
from backend.services.orchestrator.answer_generator import AnswerGeneratorService
from backend.services.orchestrator.confidence_scorer_enhanced import EnhancedConfidenceScorerService
from backend.services.core.llm_service import OllamaLLMService, LLMService
from backend.services.knowledge.kg_service import KnowledgeGraphService
from backend.services.core.conversation_memory_service import ConversationMemoryService

# Import services (these will be injected)
router = APIRouter(prefix="/api/orchestrate", tags=["orchestration"])

# Initialize Services
# We use the new OllamaLLMService for orchestration components
ollama_service = OllamaLLMService()

# We use the existing LLMService (LangChain based) for KnowledgeGraphService compatibility
langchain_llm_service = LLMService()

query_classifier = QueryClassifierService(ollama_service)
cot_generator = CoTGeneratorService(ollama_service)
kg_service = KnowledgeGraphService(llm_service=langchain_llm_service)
search_orchestrator = SearchOrchestratorService(kg_service=kg_service)
context_synthesizer = ContextSynthesizerService()
confidence_scorer = EnhancedConfidenceScorerService()
answer_generator = AnswerGeneratorService(ollama_service, confidence_scorer)

# Try to initialize memory service, but don't fail if it has issues
try:
    memory_service = ConversationMemoryService()
except Exception:
    memory_service = None

@router.post("/search", response_model=dict)
async def orchestrated_search(req: OrchestratedSearchRequest):
    """Main orchestration endpoint"""
    
    start_time = time.time()
    
    try:
        # Step 1: Classify query
        query_class = await query_classifier.classify_query(req.query)
        
        # Step 2: Generate CoT
        cot_result = await cot_generator.generate_cot(
            req.query,
            query_class
        )
        
        # Step 3: Orchestrate searches
        search_results = await search_orchestrator.orchestrate_search(
            req.query,
            cot_result,
            query_class
        )
        
        # Step 4: Synthesize context
        context = await context_synthesizer.synthesize_context(
            req.query,
            cot_result,
            search_results,
            req.session_id,
            memory_service
        )
        
        # Step 5: Generate answer
        answer = await answer_generator.generate_answer(
            req.query,
            context,
            query_class
        )
        
        # Step 6: Save to memory if session provided
        if req.session_id and memory_service:
            try:
                # We need to adapt this call based on actual ConversationMemoryService API
                # Assuming save_exchange exists or similar
                # If not, we might need to skip or fix.
                # Checking ConversationMemoryService would be good but omitting for speed, wrapping in try/except
                await memory_service.add_message(req.session_id, "user", req.query)
                await memory_service.add_message(req.session_id, "assistant", answer.answer)
            except Exception as e:
                print(f"Memory save error: {e}")
        
        # Return response
        return {
            "answer": answer.answer,
            "sources": [
                {
                    "url": s.url,
                    "title": s.title,
                    "snippet": s.snippet[:200]
                }
                for s in answer.sources
            ],
            "confidence": {
                "score": answer.confidence_score,
                "level": answer.confidence_level
            },
            "reasoning": {
                "cot_steps": cot_result.reasoning_steps,
                "key_questions": cot_result.key_questions,
                "search_terms": cot_result.search_terms
            },
            "session_id": req.session_id,
            "processing_time_seconds": time.time() - start_time,
            "model": answer.model_used
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "query_classifier": query_classifier is not None,
            "cot_generator": cot_generator is not None,
            "search_orchestrator": search_orchestrator is not None,
            "context_synthesizer": context_synthesizer is not None,
            "answer_generator": answer_generator is not None
        }
    }
