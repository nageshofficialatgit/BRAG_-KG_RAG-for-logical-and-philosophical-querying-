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

### 📚 Philosophy Book Use Case

Perfect for reading philosophy books where you need:
- References to philosophers (Aristotle, Hume, Kant, etc.)
- Summarized information from both reference text and latest web sources
- Visual representation of how concepts and philosophers are related
- Image retrieval for philosophers and concepts

## Project Structure

```
BRAG/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── routers/               # API route handlers
│   │   ├── kg.py              # Knowledge graph endpoints
│   │   ├── rag.py             # RAG query endpoints
│   │   ├── web_crawler.py     # Web crawling endpoints
│   │   └── images.py          # Image search endpoints
│   └── services/              # Business logic services
│       ├── kg_service.py      # Knowledge graph operations
│       ├── rag_service.py     # RAG pipeline
│       ├── web_crawler_service.py  # Web crawling
│       ├── image_service.py   # Image retrieval
│       └── llm_service.py     # LLM abstraction (OpenAI/Ollama)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main app component
│   │   └── components/
│   │       ├── ChatInterface.jsx      # Chat UI
│   │       ├── GraphVisualization.jsx # Graph visualization
│   │       └── SettingsPanel.jsx      # Settings UI
│   ├── package.json
│   └── vite.config.js
├── healthcare/                 # Legacy healthcare examples
├── kgraph_rag/                # Legacy RAG examples
├── simple_kg/                 # Legacy simple KG examples
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
DEFAULT_OLLAMA_MODEL=llama3.2

# Web Crawler Configuration
MAX_SEARCH_RESULTS=5
CRAWL_TIMEOUT=10

# Image Search
ENABLE_IMAGE_SEARCH=true

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
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

### RAG

- `POST /api/rag/query` - Query the RAG system
- `GET /api/rag/providers` - Get available LLM providers

### Web Crawler

- `POST /api/crawler/search` - Search the web
- `POST /api/crawler/fetch` - Fetch page content
- `POST /api/crawler/summarize` - Search and summarize

### Images

- `POST /api/images/search` - Search for images
- `GET /api/images/philosopher/{name}` - Get philosopher images

## Example Workflow

1. **Add Reference Text**:
   ```
   "In his work on free will, Aristotle discusses the relationship between 
   voluntary action and moral responsibility. Hume, in contrast, argues that 
   free will is an illusion based on our experience of causation."
   ```

2. **Create Knowledge Graph**: The system extracts entities (Aristotle, Hume, free will) and relationships

3. **Ask Questions**:
   - "What does Aristotle say about free will?"
   - "How do Aristotle and Hume differ on free will?"
   - "What is the latest research on free will?"

4. **View Results**: 
   - Get summarized answers combining reference text and web sources
   - See graph visualization showing relationships
   - View relevant images

## Architecture

### Backend Architecture

- **FastAPI**: Modern async web framework
- **Neo4j**: Graph database for knowledge storage
- **LangChain**: LLM orchestration and graph transformation
- **Modular Services**: Separate services for KG, RAG, web crawling, images, and LLM

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

### RAG Pipeline

1. **Query Processing**: Extract entities from user query
2. **Knowledge Graph Retrieval**: Get related entities and relationships
3. **Web Search**: Fetch latest information (if enabled)
4. **Context Combination**: Merge KG and web contexts
5. **LLM Generation**: Generate comprehensive answer
6. **Graph Visualization**: Extract graph data for visualization

## Configuration

### LLM Providers

**Ollama (Default)**:
- Local, free, privacy-focused
- Models: llama3.2, llama3, mistral, phi3
- Requires Ollama running locally

**OpenAI**:
- Cloud-based, requires API key
- Models: gpt-4o-mini, gpt-4, gpt-3.5-turbo
- Better performance but costs money

### Node and Relationship Extraction

The system automatically extracts:
- **Entities**: People, concepts, places, works
- **Relationships**: Influences, discusses, argues, references, etc.

For philosophy books, it's optimized to recognize:
- Philosophers (Aristotle, Hume, Kant, etc.)
- Concepts (free will, determinism, ethics, etc.)
- Works (books, essays, treatises)
- Relationships (influences, contradicts, builds on, etc.)

## Troubleshooting

### Ollama Not Available

If you see "Ollama is not running":
1. Install Ollama from https://ollama.ai
2. Start Ollama service
3. Pull a model: `ollama pull llama3.2`
4. Verify: `curl http://localhost:11434/api/tags`

### Neo4j Connection Issues

1. Verify your Neo4j credentials in `.env`
2. Check if Neo4j is running (local) or accessible (Aura)
3. Test connection: `cypher-shell -u username -p password`

### Frontend Not Connecting

1. Ensure backend is running on port 8000
2. Check CORS settings in `backend/main.py`
3. Verify proxy settings in `frontend/vite.config.js`

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


