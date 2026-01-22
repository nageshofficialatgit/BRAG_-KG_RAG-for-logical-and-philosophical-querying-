# QUICK START IMPLEMENTATION GUIDE
## Perplexica-Inspired CoT + Orchestration System

---

## 1. PROJECT STRUCTURE

```
perplexica-cot-extension/
├── backend/
│   ├── services/
│   │   ├── query_classifier.py          ← NEW
│   │   ├── cot_generator.py              ← NEW
│   │   ├── search_orchestrator.py        ← NEW
│   │   ├── context_synthesizer.py        ← NEW
│   │   ├── answer_generator.py           ← NEW (extends llm_service)
│   │   ├── confidence_scorer_enhanced.py ← NEW (extends existing)
│   │   ├── local_knowledge_search.py     ← NEW
│   │   └── ...existing services...
│   ├── routers/
│   │   ├── orchestration.py              ← NEW (main endpoint)
│   │   └── ...existing routers...
│   ├── models/
│   │   ├── orchestration_models.py       ← NEW (Pydantic models)
│   │   └── ...existing models...
│   ├── config.py                         ← EXTEND
│   └── main.py                           ← EXTEND (add new router)
├── docker-compose.yml                    ← UPDATE (add Ollama, SearxNG)
├── .env.example                          ← UPDATE
└── requirements.txt                      ← UPDATE
```

---

## 2. NEW FILES TO CREATE (In Priority Order)

### 2.1: `backend/models/orchestration_models.py`
```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

class QueryType(str, Enum):
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    META = "meta"

class FocusMode(str, Enum):
    SPEED = "speed"
    BALANCED = "balanced"
    QUALITY = "quality"

class QueryClassification(BaseModel):
    """Output of query classifier"""
    query_type: QueryType
    requires_web: bool
    local_knowledge_confidence: float  # 0-1
    temperature: float
    focus_mode: FocusMode
    reasoning_depth: int  # 1-3

class CoTStep(BaseModel):
    """Single reasoning step"""
    step_number: int
    reasoning: str
    importance: str  # high, medium, low

class CoTResult(BaseModel):
    """Output of CoT generator"""
    reasoning_steps: List[CoTStep]
    key_questions: List[str]
    search_terms: List[str]
    overall_logic_quality: float  # 0-1

class SearchResult(BaseModel):
    """Single search result"""
    title: str
    url: str
    snippet: str
    source: str
    freshness_score: float  # 0-1 (1=very recent)
    relevance_score: Optional[float] = None

class SynthesizedContext(BaseModel):
    """Combined context from all sources"""
    full_context: str  # Formatted for LLM consumption
    source_map: Dict[int, str]  # Citation number to URL
    cot_steps: List[str]
    search_results: List[SearchResult]
    local_knowledge: Dict[str, str]

class GeneratedAnswer(BaseModel):
    """Final answer with metadata"""
    answer: str
    sources: List[SearchResult]
    confidence_score: float
    confidence_level: str  # high, medium, low
    model_used: str
    reasoning_transparency: Dict

class ConfidenceFactor(BaseModel):
    source_quality: float
    context_alignment: float
    citation_coverage: float
    reasoning_consistency: float

class ConfidenceScore(BaseModel):
    overall_score: float  # 0-1
    level: str  # high, medium, low
    factors: ConfidenceFactor
    should_regenerate: bool
    regeneration_reason: Optional[str] = None

class OrchestratedSearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    focus_mode: FocusMode = FocusMode.BALANCED
    include_web: bool = True
    include_local: bool = True
    include_widgets: bool = True

class OrchestratedSearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    confidence: ConfidenceScore
    reasoning_transparency: Dict
    session_id: Optional[str] = None
    processing_time_seconds: float
    model_used: str
```

### 2.2: `backend/services/query_classifier.py`
```python
import os
from typing import Optional
from backend.models.orchestration_models import (
    QueryClassification, QueryType, FocusMode
)
from backend.services.llm_service import OllamaLLMService

class QueryClassifierService:
    """Classifies queries into types"""
    
    def __init__(self, llm_service: OllamaLLMService):
        self.llm = llm_service
    
    async def classify_query(self, query: str) -> QueryClassification:
        """Classify query and return configuration"""
        
        prompt = f"""
Classify this query into exactly ONE category:

Query: "{query}"

CATEGORIES:
1. FACTUAL - Questions about facts, dates, definitions
   Examples: "What is X?", "When did Y happen?", "How many Z?"
   
2. ANALYTICAL - Questions requiring analysis, comparison, reasoning
   Examples: "How does X work?", "Why did Y happen?", "Compare X and Y"
   
3. CREATIVE - Questions requiring generation, brainstorming
   Examples: "Generate an idea for...", "Write a poem about...", "Design..."
   
4. META - Questions about system, capabilities, or instructions
   Examples: "Can you do X?", "How do you work?", "What can you help with?"

Also determine:
- Does this need current/real-time information? (true/false)
- Can we answer well with local knowledge only? (0-100%)
- What focus mode is appropriate? (speed | balanced | quality)

RESPOND IN THIS EXACT FORMAT:
CATEGORY: [factual|analytical|creative|meta]
REQUIRES_WEB: [true|false]
LOCAL_CONFIDENCE: [0-100]
FOCUS_MODE: [speed|balanced|quality]
TEMPERATURE: [0.2|0.5|0.8]
REASONING_DEPTH: [1|2|3]

Query classification:
"""
        
        response = await self.llm.generate(
            prompt,
            temperature=0.3,  # Low temp for consistent classification
            max_tokens=100
        )
        
        return self._parse_classification(response, query)
    
    def _parse_classification(self, response: str, query: str) -> QueryClassification:
        """Parse LLM response into QueryClassification"""
        
        lines = response.strip().split('\n')
        data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip().lower()
        
        # Map to enums
        query_type_map = {
            'factual': QueryType.FACTUAL,
            'analytical': QueryType.ANALYTICAL,
            'creative': QueryType.CREATIVE,
            'meta': QueryType.META
        }
        
        focus_mode_map = {
            'speed': FocusMode.SPEED,
            'balanced': FocusMode.BALANCED,
            'quality': FocusMode.QUALITY
        }
        
        return QueryClassification(
            query_type=query_type_map.get(
                data.get('category', 'analytical'),
                QueryType.ANALYTICAL
            ),
            requires_web=data.get('requires_web', 'true').lower() == 'true',
            local_knowledge_confidence=int(data.get('local_confidence', '50')) / 100.0,
            temperature=float(data.get('temperature', '0.5')),
            focus_mode=focus_mode_map.get(
                data.get('focus_mode', 'balanced'),
                FocusMode.BALANCED
            ),
            reasoning_depth=int(data.get('reasoning_depth', '2'))
        )
```

### 2.3: `backend/services/cot_generator.py`
```python
from typing import List
import json
from backend.models.orchestration_models import (
    CoTResult, CoTStep, QueryClassification
)
from backend.services.llm_service import OllamaLLMService

class CoTGeneratorService:
    """Generates Chain-of-Thought reasoning steps"""
    
    def __init__(self, llm_service: OllamaLLMService):
        self.llm = llm_service
    
    async def generate_cot(
        self, 
        query: str, 
        query_class: QueryClassification
    ) -> CoTResult:
        """Generate step-by-step reasoning"""
        
        prompt = f"""
Let's analyze this query step-by-step.

Query: "{query}"
Query Type: {query_class.query_type.value}
Reasoning Depth: {query_class.reasoning_depth}

TASK: Break down the query into logical reasoning steps.

RESPOND IN THIS EXACT FORMAT:

STEP 1: [First reasoning step - what's the core question?]
STEP 2: [Second reasoning step - what do we need to know?]
STEP 3: [Third reasoning step - in what order?]
{"STEP 4: [Fourth reasoning step - additional insight?]" if query_class.reasoning_depth > 2 else ""}

KEY_QUESTIONS:
- [Specific question 1?]
- [Specific question 2?]
- [Specific question 3?]

SEARCH_TERMS:
- [Search term 1]
- [Search term 2]
- [Search term 3]

LOGIC_QUALITY: [0-100]

Let's reason through this:
"""
        
        response = await self.llm.generate(
            prompt,
            temperature=0.4,  # Slightly creative for reasoning
            max_tokens=500
        )
        
        return self._parse_cot_response(response)
    
    def _parse_cot_response(self, response: str) -> CoTResult:
        """Parse CoT response into structured format"""
        
        steps = []
        key_questions = []
        search_terms = []
        logic_quality = 0.7
        
        lines = response.strip().split('\n')
        current_section = None
        step_count = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('STEP'):
                step_count += 1
                reasoning = line.split(':', 1)[1].strip() if ':' in line else ''
                steps.append(CoTStep(
                    step_number=step_count,
                    reasoning=reasoning,
                    importance='high' if step_count == 1 else 'medium'
                ))
            
            elif line.startswith('KEY_QUESTIONS'):
                current_section = 'questions'
            
            elif line.startswith('SEARCH_TERMS'):
                current_section = 'search'
            
            elif line.startswith('LOGIC_QUALITY'):
                logic_quality = int(line.split(':')[1].strip()) / 100.0
            
            elif current_section == 'questions' and line.startswith('-'):
                key_questions.append(line.lstrip('-').strip())
            
            elif current_section == 'search' and line.startswith('-'):
                search_terms.append(line.lstrip('-').strip())
        
        return CoTResult(
            reasoning_steps=steps,
            key_questions=key_questions,
            search_terms=search_terms[:5],  # Top 5 search terms
            overall_logic_quality=logic_quality
        )
```

### 2.4: `backend/services/search_orchestrator.py`
```python
import asyncio
import aiohttp
from typing import List, Dict, Optional
import os
from backend.models.orchestration_models import (
    SearchResult, CoTResult, QueryClassification, OrchestratedResults
)
from backend.services.kg_service import KnowledgeGraphService

class SearchOrchestratorService:
    """Orchestrates searches across multiple sources"""
    
    def __init__(
        self,
        kg_service: Optional[KnowledgeGraphService] = None
    ):
        self.kg_service = kg_service
        self.searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888")
    
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
            tasks.append(asyncio.sleep(0))  # Placeholder
        
        # Task 2: Local knowledge search (if available)
        if self.kg_service:
            tasks.append(
                self.local_knowledge_search(cot_result.key_questions)
            )
        else:
            tasks.append(asyncio.sleep(0))
        
        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        web_results = results[0] if not isinstance(results[0], Exception) else []
        local_results = results[1] if not isinstance(results[1], Exception) else []
        
        return {
            "web_results": web_results,
            "local_results": local_results,
            "combined": web_results + local_results
        }
    
    async def searxng_search(self, search_terms: List[str]) -> List[SearchResult]:
        """Query SearxNG for web results"""
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for term in search_terms[:3]:  # Top 3 search terms
                try:
                    params = {
                        "q": term,
                        "format": "json",
                        "language": "en",
                        "pageno": 1
                    }
                    
                    async with session.get(
                        f"{self.searxng_url}/search",
                        params=params,
                        timeout=10
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for result in data.get("results", [])[:5]:
                                results.append(SearchResult(
                                    title=result.get("title", ""),
                                    url=result.get("url", ""),
                                    snippet=result.get("content", ""),
                                    source=self._extract_domain(result.get("url", "")),
                                    freshness_score=0.8  # Assume recent from SearxNG
                                ))
                
                except Exception as e:
                    print(f"SearxNG search error for '{term}': {e}")
                    continue
        
        return results
    
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
```

### 2.5: `backend/services/context_synthesizer.py`
```python
from typing import Dict, List, Optional
from backend.models.orchestration_models import (
    SynthesizedContext, CoTResult, SearchResult, CoTStep
)

class ContextSynthesizerService:
    """Combines multiple context sources"""
    
    async def synthesize_context(
        self,
        query: str,
        cot_result: CoTResult,
        search_results: Dict,
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
                history = await memory_service.get_session_context(session_id, limit=3)
                conversation_text = self._format_conversation(history)
            except:
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
```

### 2.6: `backend/services/answer_generator.py`
```python
from backend.models.orchestration_models import (
    GeneratedAnswer, SynthesizedContext, QueryClassification,
    SearchResult, ConfidenceScore
)
from backend.services.llm_service import OllamaLLMService
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
            except:
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
```

### 2.7: `backend/routers/orchestration.py`
```python
from fastapi import APIRouter, HTTPException
from typing import Optional
import time
from backend.models.orchestration_models import (
    OrchestratedSearchRequest,
    OrchestratedSearchResponse
)

# Import services (these will be injected)
router = APIRouter(prefix="/api/orchestrate", tags=["orchestration"])

# These will be initialized in main.py
query_classifier = None
cot_generator = None
search_orchestrator = None
context_synthesizer = None
answer_generator = None
confidence_scorer = None
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
                await memory_service.save_exchange(
                    session_id=req.session_id,
                    query=req.query,
                    answer=answer.answer,
                    cot_steps=cot_result.reasoning_steps
                )
            except:
                pass
        
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
```

### 2.8: Update `backend/main.py`
```python
# Add to existing main.py

from backend.services.query_classifier import QueryClassifierService
from backend.services.cot_generator import CoTGeneratorService
from backend.services.search_orchestrator import SearchOrchestratorService
from backend.services.context_synthesizer import ContextSynthesizerService
from backend.services.answer_generator import AnswerGeneratorService
from backend.routers import orchestration

# Initialize services
llm_service = OllamaLLMService()  # Existing
kg_service = KnowledgeGraphService()  # Existing

query_classifier = QueryClassifierService(llm_service)
cot_generator = CoTGeneratorService(llm_service)
search_orchestrator = SearchOrchestratorService(kg_service)
context_synthesizer = ContextSynthesizerService()
answer_generator = AnswerGeneratorService(llm_service)

# Inject into router
orchestration.query_classifier = query_classifier
orchestration.cot_generator = cot_generator
orchestration.search_orchestrator = search_orchestrator
orchestration.context_synthesizer = context_synthesizer
orchestration.answer_generator = answer_generator
orchestration.memory_service = memory_service  # Existing

# Add router
app.include_router(orchestration.router)
```

### 2.9: Update `requirements.txt`
```
aiohttp>=3.8.0
asyncio  # Usually included with Python 3.7+
```

### 2.10: Update `.env.example`
```env
# ===== NEW: ORCHESTRATION =====
ENABLE_COT=true
ENABLE_ORCHESTRATION=true
DEFAULT_FOCUS_MODE=balanced

# ===== NEW: OLLAMA (Local LLM) =====
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_OLLAMA_MODEL=gemma3:4b

# ===== NEW: SEARXNG (Web Search) =====
SEARXNG_URL=http://localhost:8888

# ===== EXISTING: Neo4j =====
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

---

## 3. SETUP INSTRUCTIONS

### Step 1: Start Local Services
```bash
# Terminal 1: Ollama (LLM)
ollama serve

# Terminal 2: Start model (in new terminal)
ollama pull gemma3:4b

# Terminal 3: SearxNG (Docker)
docker run -d -p 8888:8888 searxng/searxng

# Terminal 4: Neo4j (Docker)
docker run -d -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Terminal 5: Backend
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Step 2: Test Endpoints
```bash
# Test orchestration endpoint
curl -X POST http://localhost:8000/api/orchestrate/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "focus_mode": "balanced"
  }'

# Test health
curl http://localhost:8000/api/orchestrate/health
```

---

## 4. EXPECTED OUTPUT

### Sample Response:
```json
{
  "answer": "Machine learning is a subset of artificial intelligence... [full answer with citations]",
  "sources": [
    {
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "title": "Machine learning - Wikipedia",
      "snippet": "Machine learning (ML) is an umbrella term for solving problems for which development of algorithms by human programmers was impractical..."
    },
    {
      "url": "https://www.ibm.com/cloud/learn/machine-learning",
      "title": "What is Machine Learning?",
      "snippet": "Machine learning is a branch of artificial intelligence (AI) that relies on a system's ability to..."
    }
  ],
  "confidence": {
    "score": 0.82,
    "level": "high"
  },
  "reasoning": {
    "cot_steps": [
      "Step 1: Understand what machine learning is",
      "Step 2: Identify key characteristics",
      "Step 3: Distinguish from related concepts"
    ],
    "key_questions": [
      "What is the definition of machine learning?",
      "How does it differ from traditional programming?",
      "What are common applications?"
    ],
    "search_terms": ["machine learning definition", "how machine learning works"]
  },
  "processing_time_seconds": 4.23,
  "model": "ollama"
}
```

---

## 5. TESTING CHECKLIST

- [ ] Ollama running and responding
- [ ] SearxNG returning web results
- [ ] Neo4j connection working
- [ ] Query classifier categorizing correctly
- [ ] CoT generator producing steps
- [ ] SearxNG integration returning results
- [ ] Context synthesis combining sources
- [ ] Answer generation producing citations
- [ ] End-to-end flow completes in <15 seconds
- [ ] Confidence scores between 0-1

---

## 6. NEXT STEPS (After MVP)

1. **Self-Consistency**: Generate answer 3x, vote on best
2. **Multi-Agent**: Separate Researcher, Analyzer, Critic agents
3. **Adaptive Temperature**: Adjust based on query uncertainty
4. **Response Improvement**: Auto-regenerate if confidence < 0.6
5. **Widget System**: Add weather, stocks, calculations, etc.

