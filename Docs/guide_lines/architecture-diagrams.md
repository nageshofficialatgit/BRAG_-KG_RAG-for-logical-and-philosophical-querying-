# SYSTEM ARCHITECTURE DIAGRAMS
## Perplexica CoT + Orchestration System

---

## 1. SYSTEM ARCHITECTURE FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         USER QUERY ENTRY POINT                             │
│                    POST /api/orchestrate/search                            │
│                          "What is X?"                                       │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              1. QUERY CLASSIFICATION LAYER                                 │
│              ════════════════════════════                                  │
│   Uses: Ollama LLM (local, free)                                          │
│   Input: "What is X?"                                                      │
│   Output:                                                                  │
│   {                                                                         │
│     "type": "factual",                                                     │
│     "requires_web": true,                                                  │
│     "temperature": 0.2,                                                    │
│     "focus_mode": "balanced",                                              │
│     "reasoning_depth": 2                                                   │
│   }                                                                         │
│                                                                             │
│   Logic:                                                                    │
│   • Factual queries → low temp (0.2), need web search                      │
│   • Analytical → medium temp (0.6), can use local context                  │
│   • Creative → high temp (0.8), local LLM only                             │
│   • Meta → no search, system knowledge only                                │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│          2. CHAIN-OF-THOUGHT (CoT) GENERATION LAYER                        │
│          ═══════════════════════════════════════════                       │
│   Uses: Ollama LLM (local, free)                                          │
│   Input: Query + Classification                                            │
│   Output:                                                                  │
│   {                                                                         │
│     "reasoning_steps": [                                                   │
│       {"step": 1, "reasoning": "What's the core question?"},               │
│       {"step": 2, "reasoning": "What info is needed?"},                    │
│       {"step": 3, "reasoning": "In what order?"}                           │
│     ],                                                                      │
│     "key_questions": ["Q1?", "Q2?", "Q3?"],                                │
│     "search_terms": ["term1", "term2", "term3"],                           │
│     "logic_quality": 0.85                                                  │
│   }                                                                         │
│                                                                             │
│   Purpose:                                                                  │
│   • Make reasoning transparent                                             │
│   • Identify what's really needed                                          │
│   • Generate better search terms                                           │
│   • Improve final answer quality                                           │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
               ┌─────────────┴──────────────┐
               │                            │
               ▼                            ▼
    ┌──────────────────────┐    ┌──────────────────────────┐
    │ 3a. WEB SEARCH       │    │ 3b. LOCAL KNOWLEDGE      │
    │ (SearxNG API)        │    │ SEARCH (Neo4j)           │
    │                      │    │                          │
    │ Input:               │    │ Input:                   │
    │ search_terms         │    │ key_questions            │
    │ ["term1", ...]       │    │ ["Q1?", "Q2?"]           │
    │                      │    │                          │
    │ Query SearxNG        │    │ Query Neo4j graph        │
    │ http://localhost:    │    │ MATCH (n) WHERE ...      │
    │      8888/search     │    │ RETURN n, relationships  │
    │                      │    │                          │
    │ Output:              │    │ Output:                  │
    │ [{                   │    │ [{                       │
    │   "title": "...",    │    │   "title": "entity_name",│
    │   "url": "...",      │    │   "url": "local://id",   │
    │   "snippet": "...",  │    │   "snippet": "...",      │
    │   "source": "domain" │    │   "source": "kg"         │
    │ }, ...]              │    │ }, ...]                  │
    │                      │    │                          │
    │ Privacy: ✓ Safe      │    │ Privacy: ✓ Safe (local)  │
    │ Cost: ✓ Free         │    │ Cost: ✓ Free             │
    │ Speed: ~2-5 sec      │    │ Speed: ~0.5-1 sec        │
    │                      │    │                          │
    └──────────────┬───────┘    └──────────────┬───────────┘
                  │                            │
                  └────────────┬─────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              4. CONTEXT SYNTHESIS LAYER                                    │
│              ════════════════════════════                                  │
│   Combines:                                                                 │
│   • CoT reasoning steps                                                    │
│   • Web search results                                                     │
│   • Local knowledge graph results                                          │
│   • Conversation history (if session_id provided)                          │
│                                                                             │
│   Output (FULL CONTEXT):                                                   │
│   ┌─────────────────────────────────────────────────────┐                 │
│   │ ## REASONING STEPS (Chain-of-Thought)               │                 │
│   │ Step 1: [reasoning]                                 │                 │
│   │ Step 2: [reasoning]                                 │                 │
│   │ Step 3: [reasoning]                                 │                 │
│   │                                                     │                 │
│   │ ## SEARCH RESULTS                                   │                 │
│   │ [1] Title: ...                                      │                 │
│   │     Snippet: ... (from web search)                  │                 │
│   │ [2] Title: ...                                      │                 │
│   │     Snippet: ... (from web search)                  │                 │
│   │ [3] Title: ...                                      │                 │
│   │     Snippet: ... (from local KG)                    │                 │
│   │                                                     │                 │
│   │ ## CONVERSATION CONTEXT                             │                 │
│   │ Previous Q: \"...\"                                  │                 │
│   │ Previous A: \"...\"                                  │                 │
│   │                                                     │                 │
│   │ ## SOURCE MAPPING                                   │                 │
│   │ 1 → https://example.com/page1                       │                 │
│   │ 2 → https://example.com/page2                       │                 │
│   │ 3 → local://graph/entity123                         │                 │
│   │                                                     │                 │
│   │ ## INSTRUCTIONS FOR LLM                             │                 │
│   │ - Use reasoning steps to guide answer               │                 │
│   │ - Cite sources [1], [2], etc.                       │                 │
│   │ - Be accurate and concise                           │                 │
│   │ - Show confidence level                             │                 │
│   └─────────────────────────────────────────────────────┘                 │
│                                                                             │
│   Purpose: Feed LLM with all necessary context in organized format         │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              5. ANSWER GENERATION LAYER                                    │
│              ════════════════════════════                                  │
│   Uses: Ollama LLM (local, free)                                          │
│   Input:                                                                    │
│   • Full Context (from layer 4)                                            │
│   • User Query                                                              │
│   • Temperature (from classification)                                       │
│                                                                             │
│   Prompt Template:                                                          │
│   ┌─────────────────────────────────────────────────────┐                 │
│   │ [FULL CONTEXT]                                      │                 │
│   │                                                     │                 │
│   │ USER QUERY: \"What is X?\"                           │                 │
│   │                                                     │                 │
│   │ REQUIREMENTS:                                       │                 │
│   │ 1. Answer directly                                  │                 │
│   │ 2. Use citations [1], [2], etc.                     │                 │
│   │ 3. Show confidence level                            │                 │
│   │ 4. Cite well                                        │                 │
│   │                                                     │                 │
│   │ Generate the answer:                                │                 │
│   └─────────────────────────────────────────────────────┘                 │
│                                                                             │
│   Output:                                                                  │
│   \"X is [answer with citations]. [Support 1 with cite]. [Support 2 with    │
│   cite]. Confidence: High. Sources: [1] Wikipedia, [2] Expert article.\"  │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              6. VALIDATION & IMPROVEMENT LAYER                             │
│              ═════════════════════════════════════                          │
│   Scoring Factors:                                                          │
│   • Source Quality (0-1): Are sources authoritative?                       │
│   • Context Alignment (0-1): Does context match query?                     │
│   • Citation Coverage (0-1): Is answer well-cited?                         │
│   • Reasoning Consistency (0-1): Do CoT steps support answer?              │
│                                                                             │
│   Overall Score = 0.25 * (quality + alignment + coverage + consistency)    │
│                                                                             │
│   If score < 0.6:                                                          │
│   → Regenerate answer with:                                                │
│     • Higher temperature (more creative)                                   │
│     • More search results (additional context)                             │
│     • Or different reasoning depth                                         │
│                                                                             │
│   Output:                                                                  │
│   {                                                                         │
│     \"confidence_score\": 0.82,                                             │
│     \"confidence_level\": \"high\",                                          │
│     \"factors\": {                                                           │
│       \"source_quality\": 0.85,                                             │
│       \"context_alignment\": 0.80,                                          │
│       \"citation_coverage\": 0.85,                                          │
│       \"reasoning_consistency\": 0.78                                       │
│     },                                                                      │
│     \"should_regenerate\": false                                            │
│   }                                                                         │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              7. RESPONSE FORMATTING & STORAGE                              │
│              ════════════════════════════════════════                       │
│                                                                             │
│   If session_id provided:                                                  │
│   → Save exchange to Neo4j for memory                                      │
│     (For follow-up questions with context)                                 │
│                                                                             │
│   Final Response:                                                           │
│   {                                                                         │
│     \"answer\": \"Full answer with citations...\",                           │
│     \"sources\": [                                                           │
│       {\"url\": \"...\", \"title\": \"...\", \"snippet\": \"...\"}              │
│     ],                                                                      │
│     \"confidence\": {                                                        │
│       \"score\": 0.82,                                                      │
│       \"level\": \"high\",                                                   │
│       \"factors\": {...}                                                    │
│     },                                                                      │
│     \"reasoning\": {                                                         │
│       \"cot_steps\": [\"Step 1: ...\", \"Step 2: ...\"],                      │
│       \"search_terms\": [\"term1\", \"term2\"],                               │
│       \"key_questions\": [\"Q1?\", \"Q2?\"]                                   │
│     },                                                                      │
│     \"processing_time_seconds\": 4.23,                                      │
│     \"model\": \"ollama: gemma3:4b\",                                         │
│     \"session_id\": \"session_xyz123\"                                       │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. PARALLEL EXECUTION ARCHITECTURE

```
USER QUERY
    │
    ▼
[Query Classification] → Determine type + requirements
    │
    ▼
[Generate CoT] → Break into reasoning steps
    │
    ▼
[Identify Search Needs] → Extract search terms & questions
    │
    ├─────────────────────────────────────────────┐
    │                                             │
    │ PARALLEL EXECUTION (asyncio.gather)         │
    │                                             │
    ▼                                             ▼
[SearxNG Web Search]                    [Neo4j Local KG Search]
Query: search_terms[:3]                 Query: key_questions[:3]
async GET /search                       async MATCH (n) WHERE...
Timeout: 10s                            Timeout: 5s
Max results: 5 per term                 Max results: 5 per question
Return: [SearchResult]                  Return: [SearchResult]
    │                                             │
    └──────────────┬──────────────────────────────┘
                   │
                   ▼ (All results combined)
        [Search Results Pool]
        • Web results (fresh, diverse)
        • Local results (relevant, contextual)
        • Deduplicated
        • Ranked by relevance
                   │
                   ▼
        [Synthesize Context]
        • Format reasoning
        • Format results
        • Create citation map
        • Load conversation history (if session)
                   │
                   ▼
        [Generate Answer] (Ollama)
        • Use temperature from classification
        • Include context in prompt
        • Generate with citations
                   │
                   ▼
        [Score Confidence]
        • Multi-factor scoring
        • Regenerate if needed
                   │
                   ▼
        [Return Response]
        • Answer with citations
        • Source list
        • Confidence scores
        • Reasoning transparency
```

---

## 3. DATA FLOW DIAGRAM

```
┌─────────────────┐
│  User Query     │
│  "What is AI?"  │
└────────┬────────┘
         │
         ▼
    ┌────────────────────────┐
    │ Query Classifier       │
    │ Ollama LLM             │
    │ (Fast, local)          │
    └────────┬───────────────┘
             │
             ├─► QueryType: FACTUAL
             ├─► RequiresWeb: TRUE
             ├─► Temperature: 0.2
             └─► FocusMode: BALANCED
                     │
                     ▼
            ┌─────────────────────────┐
            │ CoT Generator           │
            │ Ollama LLM              │
            │ (Reasoning)             │
            └────────┬────────────────┘
                     │
                     ├─► Reasoning Steps
                     │   ├─ Step 1: Define AI
                     │   ├─ Step 2: Identify key aspects
                     │   └─ Step 3: Provide examples
                     │
                     ├─► Key Questions
                     │   ├─ What is AI?
                     │   ├─ How does it work?
                     │   └─ What are applications?
                     │
                     └─► Search Terms
                         ├─ "artificial intelligence"
                         ├─ "AI definition"
                         └─ "machine learning"
                             │
            ┌────────────────┬┴─────────────────┐
            │                                   │
            ▼                                   ▼
    ┌──────────────────┐            ┌──────────────────┐
    │ SearxNG Search   │            │ Neo4j Graph      │
    │ Web Results      │            │ Local Knowledge  │
    └────────┬─────────┘            └────────┬─────────┘
             │                               │
             │ [Web Results]                 │ [Local Results]
             │ ├─ Wikipedia page             │ ├─ AI concept node
             │ ├─ Expert blog                │ ├─ Related entities
             │ ├─ Latest news                │ └─ Relationships
             │ └─ Academic paper             │
             │                               │
             └───────────────┬────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │ Context Synthesizer │
                    │ Format all inputs   │
                    └────────┬────────────┘
                             │
                             ├─► Full Context
                             │   ├─ Reasoning steps (formatted)
                             │   ├─ Search results (with citations)
                             │   ├─ Local knowledge
                             │   ├─ Conversation history
                             │   └─ Source mapping
                             │
                             ▼
                    ┌────────────────────┐
                    │ Answer Generator    │
                    │ Ollama LLM         │
                    │ (with context)      │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │ Generated Answer    │
                    │ With citations [1] │
                    │ [2] [3]             │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │ Confidence Scorer   │
                    │ Multi-factor score  │
                    └────────┬────────────┘
                             │
                             ├─► Source Quality: 0.85
                             ├─► Context Alignment: 0.80
                             ├─► Citation Coverage: 0.85
                             ├─► Reasoning Consistency: 0.78
                             │
                             ▼
                    ┌────────────────────┐
                    │ Overall Score: 0.82 │
                    │ Level: HIGH         │
                    │ Status: Ready       │
                    └────────┬────────────┘
                             │
                   ┌─────────┴──────────┐
                   │                    │
        Score > 0.6? YES               │
                   │                    │
                   ▼                    ▼
        Return Response         Regenerate with
        + Reasoning              Different params
        + Sources                (Higher temp,
        + Confidence             More results)
```

---

## 4. COMPONENT INTERACTION DIAGRAM

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION ROUTER                              │
│                   POST /api/orchestrate/search                           │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ├──► QueryClassifierService
       │    ├─ Input: query string
       │    ├─ Uses: Ollama LLM (local)
       │    └─ Output: QueryClassification
       │
       ├──► CoTGeneratorService
       │    ├─ Input: query + classification
       │    ├─ Uses: Ollama LLM (local)
       │    └─ Output: CoTResult
       │
       ├──► SearchOrchestratorService (Parallel)
       │    ├─ SearxNG Search
       │    │  ├─ Input: search_terms
       │    │  ├─ Endpoint: http://localhost:8888/search
       │    │  └─ Output: [SearchResult]
       │    │
       │    └─ Local Knowledge Search
       │       ├─ Input: key_questions
       │       ├─ Service: KnowledgeGraphService
       │       ├─ Uses: Neo4j (local)
       │       └─ Output: [SearchResult]
       │
       ├──► ContextSynthesizerService
       │    ├─ Input: query, CoT, search results, conversation history
       │    ├─ Uses: ConversationMemoryService (if session_id)
       │    └─ Output: SynthesizedContext
       │
       ├──► AnswerGeneratorService
       │    ├─ Input: SynthesizedContext + QueryClassification
       │    ├─ Uses: Ollama LLM (local)
       │    ├─ Config: Temperature from classification
       │    └─ Output: GeneratedAnswer
       │
       └──► ConfidenceScorerService
            ├─ Input: query, answer, sources, CoT steps
            ├─ Scoring Method: Multi-factor
            ├─ Factors:
            │  ├─ Source Quality
            │  ├─ Context Alignment
            │  ├─ Citation Coverage
            │  └─ Reasoning Consistency
            └─ Output: ConfidenceScore
                       ├─ score: 0.0-1.0
                       ├─ level: high|medium|low
                       └─ should_regenerate: bool
```

---

## 5. EXTERNAL SERVICE DEPENDENCIES

```
┌─────────────────────────────────────────────────────────────────┐
│  REQUIRED EXTERNAL SERVICES (All Local)                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ OLLAMA (Local LLM)                                               │
│ ═══════════════════════════════════════════════════════════════  │
│ URL: http://localhost:11434                                      │
│ Purpose: Language model inference (no API costs, full privacy)   │
│ Used by: All LLM services                                        │
│   • QueryClassifierService                                       │
│   • CoTGeneratorService                                          │
│   • AnswerGeneratorService                                       │
│ Models Available:                                                │
│   • gemma3:4b (default - fast, accurate)                         │
│   • llama3.2 (more powerful)                                     │
│   • mistral (good balance)                                       │
│   • phi3, gemma2:2b (lighter)                                    │
│ Setup:                                                            │
│   1. Install: https://ollama.ai                                  │
│   2. Run: ollama serve                                           │
│   3. Pull: ollama pull gemma3:4b                                 │
│ Status Check:                                                     │
│   curl http://localhost:11434/api/tags                           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ SEARXNG (Privacy-Preserving Web Search)                          │
│ ══════════════════════════════════════════════════════════════   │
│ URL: http://localhost:8888                                       │
│ Purpose: Web search (metasearch engine, no tracking, free)      │
│ Used by: SearchOrchestratorService                               │
│ Endpoint: GET /search?q={query}&format=json                      │
│ Features:                                                         │
│   • Aggregates results from multiple search engines              │
│   • Privacy-focused (no tracking)                                │
│   • Can run locally or use public instance                       │
│   • No API key required                                          │
│ Setup:                                                            │
│   docker run -d -p 8888:8888 searxng/searxng                     │
│ Status Check:                                                     │
│   curl http://localhost:8888/search?q=test&format=json           │
│ Response: JSON with results array                                │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ NEO4J (Local Knowledge Graph)                                    │
│ ═════════════════════════════════════════════════════════════    │
│ URL: bolt://localhost:7687 (or 7686 for older versions)          │
│ Purpose: Store and query knowledge graph                         │
│ Used by: LocalKnowledgeSearchService                             │
│ Features:                                                         │
│   • Graph database for relationship queries                      │
│   • Store entities and relationships                             │
│   • Query via Cypher language                                    │
│   • Supports conversation memory                                 │
│ Setup:                                                            │
│   docker run -d                                                  │
│     -p 7687:7687                                                 │
│     -p 7474:7474                                                 │
│     -e NEO4J_AUTH=neo4j/password                                 │
│     neo4j:latest                                                 │
│ Status Check:                                                     │
│   curl http://localhost:7474                                     │
│ Web UI: http://localhost:7474/browser                            │
└──────────────────────────────────────────────────────────────────┘

TOTAL COST: $0 (all local, free)
TOTAL PRIVACY: 100% (no external calls except SearxNG)
```

---

## 6. REQUEST-RESPONSE CYCLE TIMING

```
TOTAL TIME: ~4-8 seconds (depending on web search latency)

┌────────────────────────────────────────────────────────┐
│ REQUEST: POST /api/orchestrate/search                  │
│ {                                                      │
│   "query": "What is machine learning?",                │
│   "focus_mode": "balanced",                            │
│   "session_id": "session_123" (optional)               │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                       │
                       ▼
        ┌─ 0.5s: Query Classification ─┐
        │ Ollama generates classification│
        └─ 0.5s: Query Classification ─┘
                       │
                       ▼
        ┌─ 0.8s: CoT Generation ────────┐
        │ Break query into 3 steps      │
        └─ 0.8s: CoT Generation ────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
     ┌─ 2.5s: Web Search ─┐  ┌─ 0.3s: Local Search ─┐
     │ SearxNG query      │  │ Neo4j graph query    │
     │ Takes time (slow)  │  │ Fast (local)         │
     └─ 2.5s: Web Search ─┘  └─ 0.3s: Local Search ─┘
            │                     │
            └──────────┬──────────┘
                       ▼
        ┌─ 0.2s: Synthesize Context ────┐
        │ Format all results             │
        └─ 0.2s: Synthesize Context ────┘
                       │
                       ▼
        ┌─ 1.2s: Generate Answer ───────┐
        │ Ollama with context           │
        │ (Depends on model size)        │
        └─ 1.2s: Generate Answer ───────┘
                       │
                       ▼
        ┌─ 0.3s: Score Confidence ──────┐
        │ Multi-factor scoring          │
        └─ 0.3s: Score Confidence ──────┘
                       │
                       ▼
        ┌─ 0.1s: Save to Memory ────────┐
        │ (if session_id provided)      │
        └─ 0.1s: Save to Memory ────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ RESPONSE (4.9s total):                                │
│ {                                                      │
│   "answer": "Machine learning is...",                 │
│   "sources": [5 results with URLs],                   │
│   "confidence": {"score": 0.82, "level": "high"},     │
│   "reasoning": {CoT steps, search terms},             │
│   "processing_time_seconds": 4.9                      │
│ }                                                      │
└────────────────────────────────────────────────────────┘
```

---

## 7. ERROR HANDLING FLOW

```
┌─ Orchestration Request ─┐
│   /api/orchestrate/     │
└──────────┬──────────────┘
           │
           ▼
┌──────────────────────┐
│ Query Classification │
└──────────┬───────────┘
           │
        ERROR? Ollama connection failed
           │
           ├─ YES ──→ Return 503: "LLM service unavailable"
           │
           └─ NO ──→ Continue
                       │
                       ▼
          ┌────────────────────────┐
          │ CoT Generation         │
          └──────────┬─────────────┘
                     │
                  ERROR? CoT generation failed
                     │
                     ├─ YES ──→ Use default reasoning
                     │
                     └─ NO ──→ Continue
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Search Orchestration   │
                    └──────────┬─────────────┘
                               │
                            ERROR? Both searches failed
                               │
                               ├─ YES ──→ Return 503: "No search results"
                               │
                               ├─ PARTIAL ──→ Use available results
                               │
                               └─ NO ──→ Continue
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │ Answer Generation      │
                              └──────────┬─────────────┘
                                         │
                                      ERROR? Generation failed
                                         │
                                         ├─ YES ──→ Return 500: "Could not generate"
                                         │
                                         └─ NO ──→ Continue
                                                     │
                                                     ▼
                                        ┌────────────────────────┐
                                        │ Confidence Scoring     │
                                        └──────────┬─────────────┘
                                                   │
                                                ERROR? Scoring failed
                                                   │
                                                   ├─ YES ──→ Use default 0.5
                                                   │
                                                   └─ NO ──→ Return response
                                                               │
                                                               ▼
                                                    ┌──────────────────┐
                                                    │ 200: Success     │
                                                    │ Full response    │
                                                    └──────────────────┘
```

This comprehensive architecture documentation provides:
1. **Complete system flow** with all 7 layers
2. **Parallel execution** strategy for speed
3. **Data flow** through each component
4. **Component interactions** and dependencies
5. **External services** required (all local, all free)
6. **Timing breakdown** for performance analysis
7. **Error handling** gracefully
