# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_OLLAMA_MODEL=llama3.2
```

### 3. Start Services

**Terminal 1 - Backend:**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Ollama (if using local models):**
```bash
ollama serve
# In another terminal:
ollama pull gemma3:4b
```

### 4. Open Browser

Navigate to `http://localhost:3000`

## First Steps

1. **Add Reference Text**: Click "+ Add Reference Text" and paste your philosophy book excerpt
2. **Create Graph**: Click "Create Knowledge Graph"
3. **Ask Questions**: Try "What does Aristotle say about free will?"
4. **View Graph**: See relationships in the right panel

## Example Reference Text

```
Aristotle's Nicomachean Ethics discusses voluntary action and moral responsibility. 
He argues that actions are voluntary when the agent has knowledge and acts without 
external compulsion. Hume, in his Treatise of Human Nature, takes a different view, 
arguing that free will is an illusion and that our actions are determined by 
causation and habit.
```

## Troubleshooting

- **Ollama not found**: Install from https://ollama.ai and run `ollama serve`
- **Neo4j connection error**: Check your credentials in `.env`
- **Frontend can't connect**: Ensure backend is running on port 8000
