from typing import Dict, List, Optional, Any
from backend.models.orchestration_models import (
    SynthesizedContext, CoTResult, SearchResult, CoTStep
)

class ContextSynthesizerService:
    """Combines multiple context sources"""
    
    async def synthesize_context(
        self,
        query: str,
        cot_result: CoTResult,
        search_results: Dict[str, Any],
        session_id: Optional[str] = None,
        memory_service = None
    ) -> SynthesizedContext:
        """Synthesize all contexts into one"""
        
        # Format CoT steps
        reasoning_text = self._format_cot(cot_result)
        
        # Format search results
        web_results = search_results.get("web_results", [])
        local_results = search_results.get("local_results", [])
        
        search_text, source_map = self._format_search_results(
            web_results + local_results
        )
        
        # Load conversation context if session provided
        conversation_text = ""
        if session_id and memory_service:
            try:
                # Assuming memory_service has get_session_context method
                # Adjust method name if existing service differs
                history = await memory_service.get_session_context(session_id, limit=3)
                conversation_text = self._format_conversation(history)
            except Exception:
                pass
        
        # Combine everything
        full_context = f"""
## REASONING STEPS (Chain-of-Thought):
{reasoning_text}

## SEARCH RESULTS:
{search_text}

## CONVERSATION CONTEXT:
{conversation_text if conversation_text else "[No previous conversation]"}

## INSTRUCTIONS:
- Use reasoning steps to guide your answer
- Cite sources using [1], [2], etc.
- Be accurate and cite well
- Show confidence level
"""
        
        all_results = web_results + local_results
        
        return SynthesizedContext(
            full_context=full_context,
            source_map=source_map,
            cot_steps=[s.reasoning for s in cot_result.reasoning_steps],
            search_results=all_results,
            local_knowledge={}
        )
    
    def _format_cot(self, cot_result: CoTResult) -> str:
        """Format CoT steps as text"""
        text = ""
        for step in cot_result.reasoning_steps:
            text += f"**Step {step.step_number}:** {step.reasoning}\n\n"
        return text
    
    def _format_search_results(
        self, 
        results: List[SearchResult]
    ) -> tuple:
        """Format search results with citations"""
        
        text = ""
        source_map = {}
        
        for i, result in enumerate(results[:5], 1):  # Top 5 results
            text += f"[{i}] **{result.title}**\n"
            text += f"Source: {result.source}\n"
            text += f"Content: {result.snippet[:200]}...\n\n"
            source_map[i] = result.url
        
        return text, source_map
    
    def _format_conversation(self, history: List[Dict]) -> str:
        """Format conversation history"""
        text = ""
        for exchange in history[-3:]:  # Last 3 exchanges
            text += f"Q: {exchange.get('query', '')}\n"
            text += f"A: {exchange.get('answer', '')[:100]}...\n\n"
        return text
