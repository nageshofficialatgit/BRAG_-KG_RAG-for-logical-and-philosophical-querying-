from typing import List, Dict, Optional
from backend.models.orchestration_models import (
    GeneratedAnswer, SynthesizedContext, QueryClassification,
    SearchResult, ConfidenceScore
)
from backend.services.core.llm_service import OllamaLLMService
import re

class AnswerGeneratorService:
    """Generates final answers with citations"""
    
    def __init__(
        self,
        llm_service: OllamaLLMService,
        confidence_scorer = None
    ):
        self.llm = llm_service
        self.confidence_scorer = confidence_scorer
    
    async def generate_answer(
        self,
        query: str,
        context: SynthesizedContext,
        query_class: QueryClassification
    ) -> GeneratedAnswer:
        """Generate answer using context"""
        
        prompt = f"""{context.full_context}

USER QUERY: {query}

ANSWER FORMAT:
1. Direct answer to the query (2-3 sentences)
2. Supporting details with citations [1], [2], etc.
3. Key insights
4. Confidence: [High/Medium/Low]

Generate the answer:"""
        
        answer_text = await self.llm.generate(
            prompt,
            temperature=query_class.temperature,
            max_tokens=1000
        )
        
        # Parse citations
        citations = self._extract_citations(answer_text)
        
        # Map citations to sources
        cited_sources = self._map_citations_to_sources(
            citations,
            context.source_map,
            context.search_results
        )
        
        # Calculate confidence
        confidence_score = 0.7
        if self.confidence_scorer:
            try:
                conf = await self.confidence_scorer.score_answer(
                    query=query,
                    answer=answer_text,
                    sources=context.search_results,
                    cot_steps=context.cot_steps
                )
                confidence_score = conf.overall_score
            except Exception as e:
                pass
        
        return GeneratedAnswer(
            answer=answer_text,
            sources=cited_sources,
            confidence_score=confidence_score,
            confidence_level="high" if confidence_score > 0.8 else "medium" if confidence_score > 0.6 else "low",
            model_used="ollama",
            reasoning_transparency={
                "cot_steps": context.cot_steps,
                "sources_used": len(cited_sources)
            }
        )
    
    def _extract_citations(self, text: str) -> List[int]:
        """Extract citation numbers from answer"""
        citations = re.findall(r'\[(\d+)\]', text)
        return [int(c) for c in citations]
    
    def _map_citations_to_sources(
        self,
        citations: List[int],
        source_map: Dict[int, str],
        search_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Map citations to actual sources"""
        
        sources = []
        for cite in set(citations):
            if cite in source_map:
                # Find the result matching this source
                for result in search_results:
                    if result.url == source_map[cite]:
                        sources.append(result)
                        break
        
        return sources
