# AGENT PROMPT: Perplexica-Inspired CoT Orchestration System
## Task: Implement Automated Chain-of-Thought + Search Orchestration

**Target: Google Codeium / IDE Agent Compatible Prompt**

---

## PHASE 1: UNDERSTAND THE ARCHITECTURE

### System Context
You are building a **CoT-powered search orchestration engine** similar to Perplexica & Cursor. This system:
1. Takes user queries
2. **Reasons through them step-by-step** (Chain-of-Thought)
3. **Orchestrates multiple agents** (Searcher, Reasoner, Validator)
4. **Uses SearxNG** for privacy-preserving web search
5. **Uses local Ollama models** for reasoning (no API costs, full privacy)

### Architecture Layers (Critical - Implement in this order)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. QUERY CLASSIFICATION LAYER                               │
│    ↓ Determine: Factual? Analytical? Creative? Local-only?  │
├─────────────────────────────────────────────────────────────┤
│ 2. CHAIN-OF-THOUGHT (CoT) GENERATION LAYER                  │
│    ↓ Break query into reasoning steps                       │
│    ↓ Ask LLM: "Think through the problem step-by-step"      │
├─────────────────────────────────────────────────────────────┤
│ 3. SEARCH ORCHESTRATION LAYER                               │
│    ├─ Local Knowledge (Neo4j/Graph)                         │
│    ├─ Web Search (SearxNG via API)                          │
│    └─ Tool Invocation (Widgets, calculations, etc.)         │
├─────────────────────────────────────────────────────────────┤
│ 4. CONTEXT SYNTHESIS LAYER                                  │
│    ↓ Combine: CoT steps + Search results + Local context    │
├─────────────────────────────────────────────────────────────┤
│ 5. ANSWER GENERATION LAYER                                  │
│    ↓ Generate final response with cited sources             │
├─────────────────────────────────────────────────────────────┤
│ 6. VALIDATION & IMPROVEMENT LAYER                           │
│    ↓ Score confidence, regenerate if needed                 │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE 2: IMPLEMENTATION ROADMAP

### Step 1: Query Classification Engine
**File: `backend/services/query_classifier.py`**

```python
# IMPLEMENT THIS SERVICE

class QueryClassifierService:
    """
    Classifies user queries into types to determine:
    - Which search mode to use (Speed/Balanced/Quality)
    - Whether web search is needed
    - Appropriate temperature for LLM
    - CoT reasoning depth
    """
    
    async def classify_query(self, query: str) -> QueryClass:
        """
        Returns: {
            "type": "factual|analytical|creative|meta",
            "requires_web": bool,
            "requires_local_search": bool,
            "reasoning_depth": 1-3,
            "temperature": 0.2-0.8,
            "search_mode": "speed|balanced|quality"
        }
        """
        # Implementation checklist:
        # ✓ Use Ollama model to classify (local, free)
        # ✓ Template: "Classify this query as factual/analytical/creative/meta"
        # ✓ Return structured classification
        # ✓ Cache results (same query = same classification)
        
        pass
```

**Why this matters:**
- Factual queries (dates, facts) → Low temp (0.2), need web search
- Analytical queries (analysis, comparison) → Medium temp (0.6), can use local context
- Creative queries (brainstorm) → High temp (0.8), use local LLM only
- Meta queries (system questions) → No search needed

---

### Step 2: Chain-of-Thought (CoT) Generation
**File: `backend/services/cot_generator.py`**

```python
# IMPLEMENT THIS SERVICE

class CoTGeneratorService:
    """
    Generates Chain-of-Thought reasoning steps BEFORE searching.
    
    Why CoT first?
    - Instructs the model to "think through the problem"
    - Breaks complex queries into sub-problems
    - Identifies what information is actually needed
    - Improves search query quality
    - Makes reasoning transparent
    """
    
    async def generate_cot(self, query: str, query_class: QueryClass) -> CoTResult:
        """
        Returns: {
            "reasoning_steps": ["Step 1: ...", "Step 2: ..."],
            "key_questions": ["What is X?", "How does Y relate to Z?"],
            "search_terms": ["term1", "term2", "term3"],
            "confidence_indicators": ["high", "medium", "low"]
        }
        """
        # Implementation checklist:
        # ✓ Prompt template: See PROMPTS section below
        # ✓ Use Ollama (local model)
        # ✓ Extract steps from LLM response
        # ✓ Parse into structured format
        # ✓ Generate refined search terms from reasoning
        
        cot_prompt = f"""
        Analyze this query step-by-step:
        Query: {query}
        Type: {query_class.type}
        
        REASONING STEPS:
        1. What is the core question?
        2. What sub-questions do I need to answer?
        3. What information is already known?
        4. What gaps need to be filled?
        5. In what order should I investigate?
        
        Format your response as:
        STEP 1: [reasoning]
        STEP 2: [reasoning]
        ...
        KEY QUESTIONS: [list of specific questions]
        SEARCH TERMS: [list of search keywords]
        """
        
        response = await self.ollama_service.generate(cot_prompt)
        return self.parse_cot_response(response)
```

**Key Prompts for CoT (see detailed prompts in PHASE 3):**
- Instruction: "Let's think step-by-step"
- Structure: "First... Then... Finally..."
- Validate: "Is this reasoning sound?"

---

### Step 3: Search Orchestrator Agent
**File: `backend/services/search_orchestrator.py`**

```python
# IMPLEMENT THIS SERVICE

class SearchOrchestratorAgent:
    """
    Orchestrates WHICH sources to search and HOW to search them.
    Runs searches in PARALLEL, not sequentially.
    
    Sources:
    - SearxNG (web, privacy-preserving)
    - Local Neo4j graph (knowledge base)
    - Tool widgets (weather, stocks, calculations)
    """
    
    async def orchestrate_search(
        self, 
        query: str, 
        cot_result: CoTResult,
        query_class: QueryClass
    ) -> OrchestratedResults:
        """
        Returns: {
            "web_results": [...],
            "local_results": [...],
            "widget_results": {...},
            "combined_context": str,
            "source_quality_scores": {...}
        }
        """
        
        # Implementation checklist:
        # ✓ Run searches CONCURRENTLY (asyncio.gather)
        # ✓ Search 1: SearxNG (web search)
        # ✓ Search 2: Neo4j graph queries (local knowledge)
        # ✓ Search 3: Detect and trigger widgets if needed
        # ✓ Rank results by relevance/recency
        # ✓ Remove duplicates
        # ✓ Score source quality (domain authority, freshness)
        
        tasks = [
            self.searxng_search(cot_result.search_terms),
            self.neo4j_graph_search(cot_result.key_questions),
            self.detect_and_run_widgets(query, query_class)
        ]
        
        web_results, local_results, widget_results = await asyncio.gather(*tasks)
        
        # CRITICAL: Combine and rank results
        combined = self.combine_and_rank_results(
            web_results, 
            local_results, 
            widget_results,
            cot_result
        )
        
        return combined
```

**SearxNG Integration (CRITICAL):**
```python
# IMPLEMENT THIS METHOD

async def searxng_search(self, search_terms: List[str]) -> List[SearchResult]:
    """
    Query SearxNG API for web results
    
    SearxNG Benefits:
    - Privacy: Doesn't store queries, proxies to multiple engines
    - Decentralized: Run locally or use public instance
    - Free: No API key required
    """
    
    # Implementation:
    # 1. Connect to SearxNG instance (default: http://localhost:8888)
    # 2. Send search query to /search endpoint
    # 3. Parse JSON response
    # 4. Extract: title, URL, snippet, source quality
    # 5. Deduplicate results
    
    searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888")
    
    results = []
    for term in search_terms:
        response = await self.http_client.get(
            f"{searxng_url}/search",
            params={
                "q": term,
                "format": "json",
                "pageno": 1,
                "language": "en"
            }
        )
        
        data = response.json()
        for result in data.get("results", []):
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "snippet": result.get("content"),
                "source": self.extract_domain(result.get("url")),
                "freshness": self.estimate_freshness(result.get("publishedDate"))
            })
    
    return results
```

---

### Step 4: Neo4j Local Knowledge Search
**File: `backend/services/local_knowledge_search.py`**

```python
# EXTEND EXISTING kg_service.py

class LocalKnowledgeSearchService:
    """
    Query the local Neo4j knowledge graph for:
    - Previous conversation context
    - Extracted entities and relationships
    - Philosophy concepts (from reference texts)
    - Historical information already in system
    """
    
    async def search_local_knowledge(self, key_questions: List[str]) -> List[KnowledgeResult]:
        """
        Returns structured local knowledge that complements web search
        """
        
        # Implementation checklist:
        # ✓ Parse questions to extract key entities
        # ✓ Query Neo4j for entity matches
        # ✓ Return entity context + relationships
        # ✓ Include conversation history if applicable
        # ✓ Score by relevance to current query
        
        results = []
        
        for question in key_questions:
            # Extract entities from question
            entities = await self.entity_extractor.extract(question)
            
            # Query Neo4j for each entity
            for entity in entities:
                cypher = f"""
                MATCH (n {{name: $entity}})
                OPTIONAL MATCH (n)-[r]-(related)
                RETURN n, r, related
                LIMIT 5
                """
                
                graph_results = await self.neo4j_service.query(cypher, entity=entity)
                results.extend(graph_results)
        
        return results
```

---

### Step 5: Context Synthesis Engine
**File: `backend/services/context_synthesizer.py`**

```python
# IMPLEMENT THIS SERVICE

class ContextSynthesizerService:
    """
    Combines:
    1. Chain-of-Thought reasoning steps
    2. Web search results (from SearxNG)
    3. Local knowledge (from Neo4j)
    4. Conversation history
    5. Widget results (weather, stocks, etc.)
    
    Into a single, coherent context for the LLM to use.
    """
    
    async def synthesize_context(
        self,
        query: str,
        cot_result: CoTResult,
        orchestrated_results: OrchestratedResults,
        session_id: Optional[str] = None
    ) -> SynthesizedContext:
        """
        Returns: {
            "reasoning_context": str,  # CoT steps formatted for LLM
            "search_context": str,     # Web search results formatted
            "local_context": str,      # Neo4j knowledge formatted
            "conversation_context": str,  # If session_id provided
            "widget_context": str,     # Structured widget data
            "source_mapping": {},      # URL to citation number mapping
        }
        """
        
        # Implementation checklist:
        # ✓ Format CoT steps as narrative
        # ✓ Rank search results by relevance
        # ✓ Deduplicate similar results
        # ✓ Remove low-quality sources
        # ✓ Load conversation history if session_id provided
        # ✓ Format everything as markdown for LLM consumption
        # ✓ Create source → citation number mapping
        
        # Step 1: Format reasoning
        reasoning_text = self.format_cot_for_context(cot_result)
        
        # Step 2: Format search results (top-K most relevant)
        search_text, source_map = self.format_search_results(
            orchestrated_results.web_results,
            max_results=5
        )
        
        # Step 3: Format local knowledge
        local_text = self.format_local_knowledge(
            orchestrated_results.local_results
        )
        
        # Step 4: Load conversation context if applicable
        conversation_text = ""
        if session_id:
            history = await self.memory_service.get_session_context(session_id)
            conversation_text = self.format_conversation_history(history)
        
        # Step 5: Combine everything
        full_context = f"""
## REASONING STEPS (from Chain-of-Thought):
{reasoning_text}

## RELEVANT SOURCES (Web Search Results):
{search_text}

## LOCAL KNOWLEDGE (From Knowledge Base):
{local_text}

## CONVERSATION CONTEXT:
{conversation_text}

## INSTRUCTIONS FOR ANSWERING:
- Use the reasoning steps to guide your answer
- Cite sources using [1], [2], etc. (see source mapping below)
- Prioritize recent information from web results
- Fill gaps with local knowledge
- Be transparent about confidence levels
- If information conflicts, note both perspectives

## SOURCE MAPPING:
{json.dumps(source_map, indent=2)}
"""
        
        return SynthesizedContext(
            full_context=full_context,
            source_map=source_map,
            cot_steps=cot_result.reasoning_steps,
            search_results=orchestrated_results.web_results
        )
```

---

### Step 6: Answer Generation with Ollama
**File: `backend/services/answer_generator.py`**

```python
# EXTEND EXISTING llm_service.py

class AnswerGeneratorService:
    """
    Takes synthesized context and generates the final answer.
    Uses Ollama for local inference (no API costs).
    """
    
    async def generate_answer(
        self,
        query: str,
        context: SynthesizedContext,
        query_class: QueryClass,
        temperature: float = 0.5
    ) -> GeneratedAnswer:
        """
        Returns: {
            "answer": str,  # Full answer with citations
            "sources": [{url, title, snippet}, ...],
            "confidence": float,  # 0.0-1.0
            "model_used": str,  # "ollama: model_name"
            "reasoning_transparency": {
                "steps_used": [...],
                "sources_used": [...],
                "confidence_factors": {...}
            }
        }
        """
        
        # Implementation checklist:
        # ✓ Set temperature based on query_class
        # ✓ Use Ollama local model
        # ✓ Include context in prompt
        # ✓ Ask for citations in response
        # ✓ Parse citations and verify sources
        # ✓ Score confidence of response
        # ✓ Return with reasoning transparency
        
        # Build the final prompt
        final_prompt = f"""
{context.full_context}

USER QUERY: {query}

ANSWER FORMAT:
1. Direct answer to the query
2. Supporting details with citations [1], [2], etc.
3. Confidence level: (High/Medium/Low)
4. Alternative perspectives if any
5. Limitations or caveats

Generate a comprehensive, well-structured answer:
"""
        
        # Call Ollama (local inference)
        answer = await self.ollama_service.generate(
            prompt=final_prompt,
            model=os.getenv("DEFAULT_OLLAMA_MODEL", "gemma3:4b"),
            temperature=query_class.temperature,
            top_p=0.95,
            max_tokens=1500
        )
        
        # Parse answer and extract citations
        parsed_answer = self.parse_answer_with_citations(
            answer,
            context.source_map
        )
        
        # Score confidence
        confidence = await self.confidence_scorer.score_answer(
            query=query,
            answer=parsed_answer,
            sources=context.search_results,
            cot_steps=context.cot_steps
        )
        
        return GeneratedAnswer(
            answer=parsed_answer,
            sources=context.search_results,
            confidence=confidence,
            model_used="ollama: " + os.getenv("DEFAULT_OLLAMA_MODEL"),
            reasoning_transparency={
                "steps_used": context.cot_steps,
                "sources_used": [s.url for s in context.search_results],
                "confidence_factors": confidence.factors
            }
        )
```

**Ollama Integration (CRITICAL):**
```python
# ENSURE THIS IS IN llm_service.py

class OllamaLLMService:
    """
    Local Ollama inference (no API costs, full privacy)
    """
    
    async def generate(
        self,
        prompt: str,
        model: str = "gemma3:4b",
        temperature: float = 0.5,
        top_p: float = 0.95,
        max_tokens: int = 2000
    ) -> str:
        """
        Call local Ollama model
        """
        
        # Implementation:
        # 1. Ensure Ollama is running on localhost:11434
        # 2. Send prompt via HTTP POST
        # 3. Stream response tokens (for real-time display)
        # 4. Handle rate limiting gracefully
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
                "stream": False  # Set to True for streaming
            }
            
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama error: {await resp.text()}")
                
                data = await resp.json()
                return data.get("response", "")
```

---

### Step 7: Confidence Scoring & Validation
**File: `backend/services/confidence_scorer_enhanced.py`**

```python
# EXTEND EXISTING confidence_scorer.py

class EnhancedConfidenceScorerService:
    """
    Multi-factor confidence scoring:
    - Source quality (domain authority, recency)
    - Context alignment (does context match query?)
    - Citation coverage (is answer well-cited?)
    - Reasoning consistency (do CoT steps support answer?)
    - Self-consistency (would answer be consistent if re-asked?)
    """
    
    async def score_answer(
        self,
        query: str,
        answer: str,
        sources: List[SearchResult],
        cot_steps: List[str]
    ) -> ConfidenceScore:
        """
        Returns: {
            "overall_score": 0.0-1.0,
            "level": "high|medium|low",
            "factors": {
                "source_quality": 0.0-1.0,
                "context_alignment": 0.0-1.0,
                "citation_coverage": 0.0-1.0,
                "reasoning_consistency": 0.0-1.0
            },
            "should_regenerate": bool,
            "regeneration_reason": str
        }
        """
        
        scores = {
            "source_quality": await self.score_source_quality(sources),
            "context_alignment": await self.score_context_alignment(query, answer),
            "citation_coverage": self.score_citation_coverage(answer, sources),
            "reasoning_consistency": await self.score_reasoning_consistency(
                answer, cot_steps
            )
        }
        
        # Weighted average
        weights = {
            "source_quality": 0.25,
            "context_alignment": 0.25,
            "citation_coverage": 0.25,
            "reasoning_consistency": 0.25
        }
        
        overall = sum(
            scores[key] * weights[key] for key in scores
        )
        
        # Determine if regeneration needed
        should_regenerate = overall < 0.6 or any(
            score < 0.4 for score in scores.values()
        )
        
        return ConfidenceScore(
            overall_score=overall,
            level="high" if overall > 0.8 else "medium" if overall > 0.6 else "low",
            factors=scores,
            should_regenerate=should_regenerate,
            regeneration_reason=self.get_regeneration_reason(scores)
        )
```

---

### Step 8: Main Orchestration Router
**File: `backend/routers/orchestration.py`**

```python
# NEW ROUTER: Main orchestration endpoint

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/orchestrate", tags=["orchestration"])

class OrchestratedQuery(BaseModel):
    query: str
    session_id: Optional[str] = None
    focus_mode: str = "balanced"  # speed | balanced | quality
    include_web: bool = True
    include_local: bool = True

@router.post("/search")
async def orchestrated_search(req: OrchestratedQuery) -> dict:
    """
    MAIN ENDPOINT: Orchestrates entire CoT + search flow
    
    Flow:
    1. Classify query
    2. Generate CoT
    3. Orchestrate searches (parallel)
    4. Synthesize context
    5. Generate answer
    6. Score confidence
    7. Return with transparency
    """
    
    # Step 1: Classify query
    query_class = await query_classifier.classify_query(req.query)
    
    # Step 2: Generate Chain-of-Thought
    cot_result = await cot_generator.generate_cot(req.query, query_class)
    
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
        req.session_id
    )
    
    # Step 5: Generate answer
    answer = await answer_generator.generate_answer(
        req.query,
        context,
        query_class,
        temperature=query_class.temperature
    )
    
    # Step 6: Score confidence
    if answer.confidence.should_regenerate:
        # Retry with adjusted parameters
        answer = await answer_generator.generate_answer(
            req.query,
            context,
            query_class,
            temperature=query_class.temperature + 0.2
        )
    
    # Step 7: Save to session if provided
    if req.session_id:
        await memory_service.save_exchange(
            session_id=req.session_id,
            query=req.query,
            answer=answer,
            cot_steps=cot_result.reasoning_steps
        )
    
    # Step 8: Return with full transparency
    return {
        "answer": answer.answer,
        "sources": answer.sources,
        "confidence": {
            "score": answer.confidence.overall_score,
            "level": answer.confidence.level,
            "factors": answer.confidence.factors
        },
        "reasoning_transparency": {
            "cot_steps": cot_result.reasoning_steps,
            "key_questions": cot_result.key_questions,
            "search_terms_used": cot_result.search_terms,
            "sources_consulted": len(answer.sources),
            "model_used": answer.model_used
        },
        "session_id": req.session_id
    }
```

---

## PHASE 3: CRITICAL PROMPTS & TEMPLATES

### Prompt 1: Query Classification
```
Classify the following query into ONE category:

Query: {query}

Categories:
1. FACTUAL: Questions about facts, dates, definitions, "what is", "when did"
2. ANALYTICAL: Questions requiring analysis, comparison, "how does", "why"
3. CREATIVE: Questions requiring generation, brainstorming, "imagine", "design"
4. META: Questions about system capabilities, "can you", "how do you"

Additional Information to Extract:
- Requires current information? (web search needed?)
- Local knowledge sufficient? (can answer from existing knowledge?)
- Confidence in local answer without search? (0-100%)

Respond in JSON:
{
  "category": "factual|analytical|creative|meta",
  "requires_web": true/false,
  "local_confidence": 0-100,
  "temperature": 0.2-0.8,
  "search_mode": "speed|balanced|quality"
}
```

### Prompt 2: Chain-of-Thought Generation
```
Let's think step-by-step about this query.

Query: {query}
Query Type: {type}

INSTRUCTIONS:
1. Break down the query into fundamental sub-questions
2. Identify what information is required to answer
3. Determine what is already known vs. what needs research
4. Order the investigation logically
5. Identify any assumptions or potential ambiguities

RESPOND WITH:

CORE QUESTION:
[State the fundamental question being asked]

SUB-QUESTIONS:
1. [First thing to understand]
2. [Second thing to understand]
3. [Etc.]

INFORMATION NEEDED:
- [Type of information required]
- [Type of information required]

EXISTING KNOWLEDGE:
- [What we likely know already]
- [What we likely know already]

GAPS TO FILL:
- [What needs research]
- [What needs research]

SEARCH STRATEGY:
1. First search for: [specific terms/concepts]
2. Then search for: [related concepts]
3. Finally verify: [assumptions]

REASONING CONSISTENCY CHECK:
- Is this logical? [yes/no]
- Are steps in correct order? [yes/no]
- Anything missing? [description]
```

### Prompt 3: Answer Generation with Context
```
You are an intelligent research assistant. Use the provided context to answer the user's query accurately, with citations.

CONTEXT PROVIDED:
{context}

USER QUERY: {query}

REQUIREMENTS:
1. Answer directly and clearly
2. Use citations [1], [2], etc. for claims from sources
3. Show your reasoning process
4. If sources conflict, present both views
5. Be honest about confidence levels
6. Highlight any assumptions or caveats

FORMAT YOUR RESPONSE AS:

DIRECT ANSWER:
[2-3 sentences answering the core question]

DETAILED EXPLANATION:
[Supporting details with citations]
[Sub-points with evidence]
[Alternative perspectives if relevant]

SOURCES CITED:
[Verify each citation matches provided sources]

CONFIDENCE ASSESSMENT:
Level: [High/Medium/Low]
Reasoning: [Why this confidence level?]

CAVEATS & LIMITATIONS:
[Any gaps, assumptions, or limitations]

Generate the response:
```

### Prompt 4: Source Ranking & Quality Assessment
```
Rank these search results by relevance and quality for answering: {query}

RESULTS TO RANK:
{search_results}

SCORING CRITERIA:
1. Relevance (0-100): Does result directly address the query?
2. Recency (0-100): Is information current? (recent = higher)
3. Authority (0-100): Is source authoritative? (academic > blog)
4. Completeness (0-100): Does result provide comprehensive answer?

For each result, provide:
{
  "url": "...",
  "relevance_score": 0-100,
  "recency_score": 0-100,
  "authority_score": 0-100,
  "completeness_score": 0-100,
  "overall_score": 0-100,
  "rank": 1-N,
  "reasoning": "why ranked this way"
}

Return as JSON array sorted by overall_score descending.
```

---

## PHASE 4: ENVIRONMENT & CONFIGURATION

### `.env` Configuration
```env
# OLLAMA (Local LLM - REQUIRED)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_OLLAMA_MODEL=gemma3:4b
# Alternatives: llama3.2, mistral, phi3, gemma2:2b

# SEARXNG (Privacy-Preserving Web Search)
SEARXNG_URL=http://localhost:8888
# Setup: docker run -p 8888:8888 searxng/searxng

# NEO4J (Local Knowledge Graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# ORCHESTRATION SETTINGS
ENABLE_COT=true
ENABLE_ORCHESTRATION=true
DEFAULT_FOCUS_MODE=balanced
# speed=1 search only, balanced=parallel, quality=exhaustive

# CONFIDENCE SCORING
CONFIDENCE_THRESHOLD=0.6
AUTO_REGENERATE_LOW_CONFIDENCE=true

# LLM PARAMETERS
TEMPERATURE_FACTUAL=0.2
TEMPERATURE_ANALYTICAL=0.6
TEMPERATURE_CREATIVE=0.8
MAX_TOKENS=2000

# SEARCH PARAMETERS
MAX_SEARCH_RESULTS=5
SEARXNG_TIMEOUT=10
DEDUPLICATE_RESULTS=true
```

### Docker Compose (Local Stack)
```yaml
version: '3.8'

services:
  # Ollama (Local LLM)
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_MODELS=/root/.ollama/models

  # SearxNG (Privacy Search)
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8888:8888"
    environment:
      - SEARXNG_SECRET=your-random-secret
    volumes:
      - searxng_data:/etc/searxng

  # Neo4j (Knowledge Graph)
  neo4j:
    image: neo4j:latest
    ports:
      - "7687:7687"
      - "7474:7474"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

  # Backend (FastAPI)
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - SEARXNG_URL=http://searxng:8888
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - ollama
      - searxng
      - neo4j

volumes:
  ollama_data:
  searxng_data:
  neo4j_data:
```

---

## PHASE 5: TESTING & VALIDATION

### Test Case 1: Factual Query
```
Query: "What is the current population of India?"
Expected: 
- Classify as FACTUAL
- Requires web search
- Low temperature (0.2)
- CoT steps about finding latest census data
- SearxNG search for "India population 2024"
- Response with recent data + citations
```

### Test Case 2: Analytical Query
```
Query: "How does machine learning differ from deep learning?"
Expected:
- Classify as ANALYTICAL
- Can use local knowledge + web
- Medium temperature (0.6)
- CoT steps about defining each concept, comparing
- Combine local definitions with web examples
- Response with comprehensive comparison
```

### Test Case 3: Multi-step Reasoning
```
Query: "Why did the stock market react negatively to recent interest rate increases, and what does this mean for tech stocks?"
Expected:
- Classify as ANALYTICAL
- Requires current web data
- CoT steps:
  1. Define relationship between interest rates and markets
  2. Find recent interest rate news
  3. Find recent market reactions
  4. Analyze tech sector impact
  5. Synthesize conclusion
- Parallel searches for: rates, markets, tech stocks
- Response with causal reasoning
```

---

## PHASE 6: ADVANCED FEATURES (Post-MVP)

### Feature 1: Self-Consistency
```python
# Generate answer multiple times, vote on best
async def self_consistent_generation(query: str, num_attempts: int = 3):
    answers = []
    for _ in range(num_attempts):
        answer = await answer_generator.generate_answer(query, ...)
        answers.append(answer)
    
    # Vote on answers using semantic similarity
    best_answer = self.majority_vote(answers)
    confidence = self.consensus_confidence(answers)
    return best_answer, confidence
```

### Feature 2: Multi-Agent Reasoning
```python
# Parallel agents: Researcher, Analyzer, Critic
# Researcher: Finds information
# Analyzer: Analyzes information
# Critic: Validates answer quality
```

### Feature 3: Adaptive Temperature
```python
# Dynamically adjust temperature based on:
# - Query uncertainty
# - Source consensus
# - Reasoning complexity
```

---

## CRITICAL SUCCESS METRICS

### Implementation Checklist
- [ ] Query classifier working (all 4 types)
- [ ] CoT generator producing step-by-step reasoning
- [ ] SearxNG integration fetching results
- [ ] Neo4j local search working
- [ ] Parallel orchestration (asyncio.gather)
- [ ] Context synthesis combining all sources
- [ ] Ollama answer generation working
- [ ] Citation parsing and validation
- [ ] Confidence scoring implementation
- [ ] End-to-end flow working (query → answer)

### Performance Metrics
- **Latency**: Full flow < 10 seconds (quality mode)
- **Accuracy**: Answer relevance > 85%
- **Confidence**: Calibrated (score matches actual accuracy)
- **Privacy**: Zero external API calls except SearxNG
- **Cost**: $0 (all local)

---

## TROUBLESHOOTING GUIDE

### Issue 1: Ollama Not Responding
```
Error: Connection to ollama failed
Solution:
1. Ensure Ollama installed: ollama.ai
2. Start service: ollama serve
3. Pull model: ollama pull gemma3:4b
4. Check: curl http://localhost:11434/api/tags
```

### Issue 2: SearxNG Returns No Results
```
Error: SearxNG search failed
Solution:
1. Verify SearxNG running: docker ps | grep searxng
2. Test: curl http://localhost:8888/search?q=test&format=json
3. Check firewall/port access
4. Verify search terms are valid
```

### Issue 3: CoT Steps Not Improving Accuracy
```
Problem: Chain-of-thought not helping
Solution:
1. Increase reasoning_depth parameter
2. Use larger Ollama model (llama3.2 instead of gemma3:4b)
3. Provide few-shot examples in prompt
4. Add constraint: "Your reasoning must be logically sound"
```

### Issue 4: Low Confidence Scores
```
Problem: Answers scoring < 0.6 confidence
Solution:
1. Check source quality (old/unreliable sources)
2. Increase web search results to 10
3. Use quality mode instead of balanced
4. Verify Neo4j has sufficient local knowledge
```

---

## SUMMARY FOR AGENT

Your task is to implement an intelligent search orchestration system with Chain-of-Thought reasoning. This system:

**Inputs:**
- User query
- Optional session ID (for conversation memory)
- Optional focus mode (speed/balanced/quality)

**Process (Implement in order):**
1. **Classify query** → Determine type, required sources, temperature
2. **Generate CoT** → Break query into reasoning steps
3. **Orchestrate searches** → Parallel searches (SearxNG + Neo4j + widgets)
4. **Synthesize context** → Combine all sources into coherent context
5. **Generate answer** → Use Ollama with context to generate answer
6. **Score confidence** → Multi-factor confidence assessment
7. **Validate & regenerate if needed** → Improve low-confidence answers
8. **Return with transparency** → Include reasoning, sources, confidence

**Key Technologies:**
- **Ollama**: Local LLM (no API costs, full privacy)
- **SearxNG**: Privacy-preserving web search
- **Neo4j**: Local knowledge graph
- **FastAPI**: Backend framework
- **asyncio**: Parallel orchestration

**Success Criteria:**
- Answers include step-by-step reasoning (CoT)
- Sources properly cited with high confidence
- Full system runs locally (privacy-preserving)
- Latency < 10 seconds
- Accuracy > 85%

You have all the architecture, code templates, prompts, and configuration needed. Start implementation from PHASE 2, Step 1.
