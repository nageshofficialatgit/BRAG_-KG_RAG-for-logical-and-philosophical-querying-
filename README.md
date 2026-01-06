# Knowledge Graph RAG System

A comprehensive Knowledge Graph RAG (Retrieval-Augmented Generation) system with web crawling, image retrieval, and an interactive React dashboard. Perfect for philosophy research, book analysis, and contextual knowledge exploration.

## Features

### 🎯 Core Capabilities

1. **Knowledge Graph Creation** - Automatically creates knowledge graphs from reference text using Neo4j
2. **Web Crawling** - Retrieves latest information from the internet (like Perplexity)
3. **Interactive Dashboard** - React-based chat interface with real-time graph visualization
4. **Dual LLM Support** - Use OpenAI API or local Ollama models
5. **Image Retrieval** - Fetches relevant images for queries
6. **Context-Aware Responses** - Combines reference text and web sources for comprehensive answers
7. **Conversation Memory** - Maintains conversation history with automatic entity tracking and archival
8. **Session Management** - Per-session conversation memory with catastrophic forgetting prevention
9. **Smart Memory Management** - Automatic memory pile-up prevention and context length optimization
10. **Output Quality Scoring** - Confidence scoring and automatic response improvement
11. **Dynamic Prompt Loading** - Prompt templates decoupled from code, configurable behavior

### 📚 Philosophy Book Use Case

Perfect for reading philosophy books where you need:
- References to philosophers (Aristotle, Hume, Kant, etc.)
- Summarized information from both reference text and latest web sources
- Visual representation of how concepts and philosophers are related
- Image retrieval for philosophers and concepts
- Conversation continuity with automatic entity importance tracking

## Project Structure

```
BRAG/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Centralized configuration (all hardcoded values moved here)
│   ├── constants.py           # Reusable prompt templates and constants
│   ├── prompts/               # External prompt files (decoupled from code)
│   │   ├── philosophy_response.txt
│   │   ├── factual_question.txt
│   │   ├── analytical_question.txt
│   │   └── creative_question.txt
│   ├── routers/               # API route handlers
│   │   ├── kg.py              # Knowledge graph endpoints
│   │   ├── rag.py             # RAG query endpoints with session management
│   │   ├── web_crawler.py     # Web crawling endpoints
│   │   └── images.py          # Image search endpoints
│   └── services/              # Business logic services
│       ├── kg_service.py      # Knowledge graph operations
│       ├── rag_service.py     # RAG pipeline with memory integration
│       ├── conversation_memory_service.py  # Conversation memory with archival
│       ├── output_processor.py        # Response quality scoring & improvement
│       ├── confidence_scorer.py       # Multi-factor confidence scoring
│       ├── prompt_loader.py          # Dynamic prompt loading
│       ├── web_crawler_service.py    # Web crawling
│       ├── image_service.py          # Image retrieval
│       └── llm_service.py            # LLM abstraction (OpenAI/Ollama)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main app component
│   │   └── components/
│   │       ├── ChatInterface.jsx      # Chat UI with session support
│   │       ├── GraphVisualization.jsx # Graph visualization
│   │       └── SettingsPanel.jsx      # Settings UI
│   ├── package.json
│   └── vite.config.js
├── Learning_kg_rag/           # Legacy examples and learning materials
├── reference_texts/           # Sample reference texts
└── requirements.txt           # Python dependencies
```

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Neo4j database (Aura or local instance)
- (Optional) Ollama installed locally for local LLM support
- (Optional) OpenAI API key for OpenAI models

## Installation

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file in project root
cp .env.example .env
# Edit .env with your credentials
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Neo4j Configuration
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# LLM Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_OLLAMA_MODEL=gemma3:4b

# Web Crawler Configuration
MAX_SEARCH_RESULTS=5
CRAWL_TIMEOUT=10
RESPECT_ROBOTS_TXT=true

# Image Search
ENABLE_IMAGE_SEARCH=true

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Conversation Memory Configuration
MEMORY_MAX_HISTORY=15
MEMORY_ENABLE_ARCHIVAL=true
MEMORY_ENABLE_IMPORTANCE_SCORING=true
MEMORY_SESSION_ID_PREFIX=session

# Router Configuration
ROUTER_DEFAULT_INCLUDE_WEB=true
ROUTER_DEFAULT_INCLUDE_IMAGES=true
ROUTER_SESSION_CONTEXT_MAX_TOKENS=2000

# Temperature Settings (Adaptive by question type)
TEMPERATURE_FACTUAL=0.2
TEMPERATURE_ANALYTICAL=0.6
TEMPERATURE_CREATIVE=0.8
TEMPERATURE_DEFAULT=0.5

# Output Quality Configuration
OUTPUT_MIN_QUALITY_SCORE=0.6
OUTPUT_MIN_WORD_COUNT=50
OUTPUT_QUALITY_THRESHOLD_IMPROVE=0.6

# Confidence Scoring Configuration
CONFIDENCE_CONTEXT_WEIGHT=0.3
CONFIDENCE_SOURCE_WEIGHT=0.2
CONFIDENCE_CITATION_WEIGHT=0.2
CONFIDENCE_COVERAGE_WEIGHT=0.3
CONFIDENCE_THRESHOLD_HIGH=0.8
CONFIDENCE_THRESHOLD_MEDIUM=0.6

# Context Token Limits
MAX_CONTEXT_TOKENS=2000
MAX_CHAT_HISTORY_TOKENS=1000
CHAT_HISTORY_LIMIT=3
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Install Ollama (Optional, for local models)

```bash
# Visit https://ollama.ai for installation instructions
# Then pull a model:
ollama pull llama3.2
```

## Usage

### Start Backend Server

```bash
# From project root
python -m backend.main
# Or
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Using the System

1. **Add Reference Text**: Click "+ Add Reference Text" and paste your philosophy book content or any reference material
2. **Create Knowledge Graph**: Click "Create Knowledge Graph" to process the text and build the graph
3. **Ask Questions**: Type questions in the chat interface
4. **View Graph**: The right panel shows the knowledge graph visualization with nodes and relationships
5. **Configure Settings**: Click the settings button to switch between OpenAI and Ollama, enable/disable web search and images

## API Endpoints

### Knowledge Graph

- `POST /api/kg/create` - Create knowledge graph from text
- `GET /api/kg/stats` - Get graph statistics
- `POST /api/kg/query` - Execute Cypher query
- `POST /api/kg/entities/related` - Get related entities
- `POST /api/kg/visualization` - Get graph data for visualization
- `DELETE /api/kg/clear` - Clear the graph

### RAG & Conversation Memory

- `POST /api/rag/query` - Query the RAG system with optional session ID for conversation continuity
  - **New**: Accepts `session_id` for conversation memory management
  - **New**: Returns memory health metadata and archival status
- `GET /api/rag/providers` - Get available LLM providers (Ollama & OpenAI)
- `POST /api/rag/sessions/create` - Create new conversation session
- `GET /api/rag/sessions/{session_id}` - Get session info and memory health status
- `GET /api/rag/sessions/{session_id}/context` - Get current conversation context with extracted entities
- `DELETE /api/rag/sessions/{session_id}` - Clear conversation history for a session

### Web Crawler

- `POST /api/crawler/search` - Search the web
- `POST /api/crawler/fetch` - Fetch page content
- `POST /api/crawler/summarize` - Search and summarize

### Images

- `POST /api/images/search` - Search for images
- `GET /api/images/philosopher/{name}` - Get philosopher images

## Example Workflow

1. **Create Session** (Optional - auto-created if not provided):
   ```bash
   curl -X POST http://localhost:8000/api/rag/sessions/create
   # Returns: {"session_id": "session_abc12345", "created": true}
   ```

2. **Add Reference Text**:
   ```
   "In his work on free will, Aristotle discusses the relationship between 
   voluntary action and moral responsibility. Hume, in contrast, argues that 
   free will is an illusion based on our experience of causation."
   ```

3. **Create Knowledge Graph**: The system extracts entities (Aristotle, Hume, free will) and relationships

4. **Ask Questions** (with conversation memory):
   ```bash
   curl -X POST http://localhost:8000/api/rag/query \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What does Aristotle say about free will?",
       "session_id": "session_abc12345",
       "include_web": true,
       "include_images": true
     }'
   ```

5. **Follow-up Questions** (Automatic memory maintained):
   ```bash
   curl -X POST http://localhost:8000/api/rag/query \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How does this differ from Hume's view?",
       "session_id": "session_abc12345"
     }'
   ```

6. **View Results**: 
   - Get summarized answers combining reference text, web sources, and conversation context
   - See graph visualization showing relationships
   - View relevant images
   - Memory automatically tracks important entities across exchanges

7. **Check Memory Health**:
   ```bash
   curl http://localhost:8000/api/rag/sessions/session_abc12345
   # Returns: Memory status, entity importance, archival info
   ```

## Architecture

### Backend Architecture

- **FastAPI**: Modern async web framework
- **Neo4j**: Graph database for knowledge storage
- **LangChain 0.3+**: LLM orchestration and graph transformation
- **Modular Services**: Separate services for KG, RAG, memory, web crawling, images, and LLM
- **ConversationMemoryService**: Automatic conversation memory with entity tracking and archival
- **OutputProcessor**: Quality scoring and automatic response improvement
- **ConfidenceScorer**: Multi-factor confidence assessment
- **PromptLoader**: Dynamic prompt loading from external files

### Frontend Architecture

- **React**: Component-based UI framework
- **Vite**: Fast build tool and dev server
- **React Force Graph**: Interactive graph visualization
- **Axios**: HTTP client for API calls

### Knowledge Graph Creation

The system uses LangChain's `LLMGraphTransformer` to:
1. Split text into chunks
2. Extract entities and relationships using LLM
3. Store in Neo4j with proper labels and relationships
4. Support hybrid search (vector + graph)

### RAG Pipeline with Conversation Memory

1. **Session Management**: Create or retrieve conversation session with memory
2. **Memory Context Retrieval**: Load conversation history with automatic entity importance tracking
3. **Query Processing**: Extract entities from user query
4. **Knowledge Graph Retrieval**: Get related entities and relationships
5. **Web Search**: Fetch latest information (if enabled)
6. **Context Combination**: Merge memory context, KG context, and web sources (memory prioritized)
7. **LLM Generation**: Generate comprehensive answer with conversation context
8. **Memory Update**: Save exchange to memory with:
   - Entity importance tracking (prevents catastrophic forgetting)
   - Automatic archival when >30 exchanges (prevents pile-up)
   - Token-aware context optimization
9. **Output Quality**: Score confidence and improve if needed
10. **Graph Visualization**: Extract graph data for visualization

### Conversation Memory Management

The `ConversationMemoryService` provides:

**Active Memory Pool**:
- Keeps last 20 exchanges in active memory
- Used for immediate context in LLM prompts
- Entity relationships maintained in Neo4j

**Memory Archival**:
- Automatically archives exchanges when >30 total exchanges
- Preserves important entities (mentioned 3+ times)
- Creates summaries of archived exchanges
- Prevents unbounded memory growth

**Entity Importance Tracking**:
- Tracks mention frequency of philosophers, concepts
- Important entities marked for preservation
- Used to prevent catastrophic forgetting of key concepts

**Context Length Optimization**:
- Token counting using tiktoken (GPT-4 encoding)
- Smart truncation: Prioritizes recent exchanges and important entities
- Archive summarization: Compact representation of older exchanges
- Graceful degradation when context too large

**Session Isolation**:
- Each conversation session has independent memory
- Prevents cross-session contamination
- Allows multiple concurrent conversations

### RAG Pipeline
4. **Context Combination**: Merge memory, KG and web contexts
5. **LLM Generation**: Generate comprehensive answer
6. **Output Quality**: Score confidence and improve if needed
7. **Graph Visualization**: Extract graph data for visualization

## Configuration

All configuration values are centralized in `backend/config.py` and can be overridden via environment variables.

### LLM Configuration

**Ollama (Default)**:
- Local, free, privacy-focused
- Models: gemma3:4b, llama3.2, llama3, mistral, phi3, gemma2:2b
- Environment: `DEFAULT_LLM_PROVIDER=ollama`, `DEFAULT_OLLAMA_MODEL=gemma3:4b`
- Requires Ollama running locally: `http://localhost:11434`

**OpenAI**:
- Cloud-based, requires API key
- Models: gpt-4o-mini, gpt-4, gpt-3.5-turbo
- Environment: `OPENAI_API_KEY=your_key`, `DEFAULT_LLM_PROVIDER=openai`
- Better performance but costs money

### Conversation Memory Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Max History | `MEMORY_MAX_HISTORY` | 15 | Number of exchanges to keep in active memory |
| Enable Archival | `MEMORY_ENABLE_ARCHIVAL` | true | Automatically archive old exchanges |
| Importance Scoring | `MEMORY_ENABLE_IMPORTANCE_SCORING` | true | Track entity mention frequency |
| Session ID Prefix | `MEMORY_SESSION_ID_PREFIX` | "session" | Prefix for generated session IDs |

### Router Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Include Web | `ROUTER_DEFAULT_INCLUDE_WEB` | true | Include web search results by default |
| Include Images | `ROUTER_DEFAULT_INCLUDE_IMAGES` | true | Include image results by default |
| Context Max Tokens | `ROUTER_SESSION_CONTEXT_MAX_TOKENS` | 2000 | Maximum tokens for session context |

### Output Quality Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Min Quality Score | `OUTPUT_MIN_QUALITY_SCORE` | 0.6 | Minimum acceptable response quality |
| Min Word Count | `OUTPUT_MIN_WORD_COUNT` | 50 | Minimum words in response |
| Ideal Word Range | N/A | 150-500 | (Good, Excellent) word counts |
| Improve Threshold | `OUTPUT_QUALITY_THRESHOLD_IMPROVE` | 0.6 | Quality threshold to trigger improvement |

### Temperature Configuration (Adaptive)

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Factual | `TEMPERATURE_FACTUAL` | 0.2 | Low randomness for factual questions |
| Analytical | `TEMPERATURE_ANALYTICAL` | 0.6 | Medium randomness for analysis |
| Creative | `TEMPERATURE_CREATIVE` | 0.8 | High randomness for creative questions |
| Default | `TEMPERATURE_DEFAULT` | 0.5 | Fallback temperature |

### Confidence Scoring Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Context Weight | `CONFIDENCE_CONTEXT_WEIGHT` | 0.3 | Weight of context quality in score |
| Source Weight | `CONFIDENCE_SOURCE_WEIGHT` | 0.2 | Weight of source count |
| Citation Weight | `CONFIDENCE_CITATION_WEIGHT` | 0.2 | Weight of citations presence |
| Coverage Weight | `CONFIDENCE_COVERAGE_WEIGHT` | 0.3 | Weight of topic coverage |
| High Threshold | `CONFIDENCE_THRESHOLD_HIGH` | 0.8 | High confidence threshold |
| Medium Threshold | `CONFIDENCE_THRESHOLD_MEDIUM` | 0.6 | Medium confidence threshold |

### Node and Relationship Extraction

The system automatically extracts:
- **Entities**: People, concepts, places, works
- **Relationships**: Influences, discusses, argues, references, etc.

For philosophy books, it's optimized to recognize:
- Philosophers (Aristotle, Hume, Kant, etc.)
- Concepts (free will, determinism, ethics, etc.)
- Works (books, essays, treatises)
- Relationships (influences, contradicts, builds on, etc.)

## Recent Improvements

### Conversation Memory System (v2.0)

**New Features**:
- ✅ **Per-session conversation memory** - Each session maintains independent conversation history
- ✅ **Automatic entity importance tracking** - Philosophers and concepts mentioned 3+ times are preserved
- ✅ **Memory archival system** - Prevents pile-up by archiving old exchanges while preserving important entities
- ✅ **Token-aware context optimization** - Smart truncation using tiktoken (GPT-4 encoding)
- ✅ **Catastrophic forgetting prevention** - Important entities never lost even when archiving
- ✅ **Session health monitoring** - Track memory status, archival count, and entity importance

**Benefits**:
- Conversations remain coherent across many exchanges
- System won't lose track of key philosophers or concepts
- Automatic memory management prevents context overflow
- Each user conversation completely isolated

### Backend Architecture Improvements (v1.5)

**Service Refactoring**:
- ✅ **OutputProcessor** - Quality scoring and automatic response improvement
- ✅ **ConfidenceScorer** - Multi-factor confidence assessment with configurable weights
- ✅ **PromptLoader** - Dynamic prompt loading from external files (decoupled from code)
- ✅ **ConversationMemoryService** - Entity extraction and conversation memory management
- ✅ **RAGService enhancements** - Dependency injection for all services

**Dependency Management**:
- ✅ **LangChain 0.3+ compatible** - Uses `langchain_community.memory.kg.ConversationKGMemory`
- ✅ **All imports verified** - Compatible with langchain-neo4j 0.4.0, langchain-openai 0.3.12
- ✅ **Token counting** - Integrated tiktoken for accurate context length management

### Configuration & Decoupling (v1.4)

**Moved to Config**:
- ✅ **All model definitions** - DEFAULT_OLLAMA_FALLBACK_MODELS, AVAILABLE_OPENAI_MODELS
- ✅ **Memory settings** - MEMORY_MAX_HISTORY, MEMORY_ENABLE_ARCHIVAL, etc.
- ✅ **Router defaults** - ROUTER_DEFAULT_INCLUDE_WEB, ROUTER_DEFAULT_INCLUDE_IMAGES
- ✅ **Temperature settings** - Per-question-type temperature adaptation
- ✅ **Quality thresholds** - All quality scoring weights
- ✅ **Context limits** - Token limits and history sizes

**No More Hardcoding**:
- Router uses config values (no hardcoded "gemma3:4b" etc.)
- All defaults configurable via environment variables
- Easy customization for different deployments

## Troubleshooting

### Ollama Not Available

If you see "Ollama is not running":
1. Install Ollama from https://ollama.ai
2. Start Ollama service
3. Pull a model: `ollama pull gemma3:4b` or `ollama pull llama3.2`
4. Verify: `curl http://localhost:11434/api/tags`

### Neo4j Connection Issues

1. Verify your Neo4j credentials in `.env`
2. Check if Neo4j is running (local) or accessible (Aura)
3. Test connection: `cypher-shell -u username -p password`

### Frontend Not Connecting

1. Ensure backend is running on port 8000
2. Check CORS settings in `backend/main.py`
3. Verify proxy settings in `frontend/vite.config.js`

### Session Issues

If sessions aren't working:
1. Verify `MEMORY_ENABLE_ARCHIVAL=true` in `.env`
2. Check Neo4j is storing :Exchange nodes properly
3. Monitor memory health: `GET /api/rag/sessions/{session_id}`

## Development

### Running in Development Mode

```bash
# Backend with auto-reload
uvicorn backend.main:app --reload

# Frontend with hot reload
cd frontend && npm run dev
```

### Adding New Features

The modular structure makes it easy to:
- Add new LLM providers in `backend/services/llm_service.py`
- Extend entity extraction in `backend/services/kg_service.py`
- Add new visualization types in `frontend/src/components/GraphVisualization.jsx`

## License

This project is open source and available for educational and research purposes.


