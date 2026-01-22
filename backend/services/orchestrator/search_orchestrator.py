import asyncio
from typing import List, Dict, Optional
import os
from langchain_community.utilities import SearxSearchWrapper
from backend.models.orchestration_models import (
    SearchResult, CoTResult, QueryClassification
)
from backend.services.knowledge.kg_service import KnowledgeGraphService
from backend.services.core.llm_service import OllamaLLMService

class SearchOrchestratorService:
    """Orchestrates searches across multiple sources with iterative refinement"""
    
    def __init__(
        self,
        kg_service: Optional[KnowledgeGraphService] = None,
        llm_service: Optional[OllamaLLMService] = None
    ):
        self.kg_service = kg_service
        self.llm_service = llm_service
        self.searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888")
        # Initialize LangChain wrapper
        try:
            self.searx = SearxSearchWrapper(searx_host=self.searxng_url)
        except Exception as e:
            print(f"Warning: SearxSearchWrapper initialization failed: {e}")
            self.searx = None
    
    async def orchestrate_search(
        self,
        query: str,
        cot_result: CoTResult,
        query_class: QueryClassification
    ) -> Dict:
        """Run parallel searches"""
        
        # Create tasks for parallel execution
        tasks = []
        
        # Task 1: SearxNG web search (if needed)
        if query_class.requires_web:
            tasks.append(
                self.searxng_search(cot_result.search_terms)
            )
        else:
            tasks.append(self._empty_search())
        
        # Task 2: Local knowledge search (if available)
        if self.kg_service:
            tasks.append(
                self.local_knowledge_search(cot_result.key_questions)
            )
        else:
            tasks.append(self._empty_search())
        
        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        web_results = results[0] if not isinstance(results[0], Exception) else []
        local_results = results[1] if not isinstance(results[1], Exception) else []
        
        return {
            "web_results": web_results,
            "local_results": local_results,
            "combined": web_results + local_results
        }
    
    async def _empty_search(self) -> List[SearchResult]:
        return []

    async def searxng_search(self, search_terms: List[str], retry_count: int = 0) -> List[SearchResult]:
        """Query SearxNG for web results with iterative refinement"""
        
        if not self.searx:
            return []
            
        results = []
        processed_urls = set()
        
        # Using loop instead of gather to manage rate limits/connection easier
        for term in search_terms[:4]:  # Top 4 terms
            try:
                # Runs in thread pool because langchain wrapper is sync usually
                search_results = await asyncio.to_thread(
                    self.searx.results, 
                    term, 
                    num_results=3
                )
                
                for res in search_results:
                    url = res.get("link", "")
                    if url in processed_urls:
                        continue
                        
                    processed_urls.add(url)
                    results.append(SearchResult(
                        title=res.get("title", ""),
                        url=url,
                        snippet=res.get("snippet", ""),
                        source=self._extract_domain(url),
                        freshness_score=0.8  # Assume moderate freshness
                    ))
            except Exception as e:
                print(f"SearxNG search error for '{term}': {e}")
                continue
        
        # Iterative Refinement Check
        if len(results) < 2 and retry_count < 1 and self.llm_service:
            print("Low search results, refining terms...")
            new_terms = await self._refine_search_terms(search_terms)
            if new_terms:
                more_results = await self.searxng_search(new_terms, retry_count + 1)
                results.extend(more_results)
        
        return results
    
    async def _refine_search_terms(self, original_terms: List[str]) -> List[str]:
        """Generate better search terms if initial ones failed"""
        try:
            prompt = f"""
The following search terms yielded few results:
{", ".join(original_terms)}

Generate 3 alternative, more specific or broader search terms to find relevant information.
Return ONLY the terms as a comma-separated list.
"""
            response = await self.llm_service.generate(prompt, temperature=0.7)
            return [t.strip() for t in response.split(',') if t.strip()]
        except Exception:
            return []
    
    async def local_knowledge_search(self, key_questions: List[str]) -> List[SearchResult]:
        """Query local Neo4j graph"""
        
        if not self.kg_service:
            return []
        
        results = []
        
        for question in key_questions:
            try:
                # Try to find relevant entities in graph
                graph_results = await self.kg_service.search_entities(question)
                
                for result in graph_results:
                    results.append(SearchResult(
                        title=result.get("name", ""),
                        url=f"local://graph/{result.get('id', '')}",
                        snippet=result.get("description", ""),
                        source="local_knowledge_graph",
                        freshness_score=1.0  # Local = always fresh
                    ))
            
            except Exception as e:
                print(f"Local search error: {e}")
                continue
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace("www.", "")
        except:
            return "unknown"
