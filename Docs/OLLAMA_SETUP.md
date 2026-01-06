# Ollama Model Configuration

## Current Setup

The system is configured to use **gemma3:4b** as the default Ollama model.

## Configuration

### Environment Variable

Set in your `.env` file:

```env
DEFAULT_OLLAMA_MODEL=gemma3:4b
```

If your model has a different name (e.g., `gemma3:4b`), update it:

```env
DEFAULT_OLLAMA_MODEL=gemma3:4b
```

### Dynamic Model Detection

The system automatically detects available Ollama models by querying:
```
http://localhost:11434/api/tags
```

This means:
- ✅ You don't need to manually list models
- ✅ New models are automatically available
- ✅ The frontend shows your actual installed models

## Using Your Model

### Option 1: Update .env File

```env
DEFAULT_OLLAMA_MODEL=gemma3:4b
```

### Option 2: Use Frontend Settings

1. Click ⚙️ Settings
2. Select "ollama" as provider
3. Choose "gemma3:4b" from the model dropdown

### Option 3: API Request

```json
POST /api/rag/query
{
  "question": "What is free will?",
  "llm_provider": "ollama",
  "model": "gemma3:4b"
}
```

## Verifying Your Model

Check if your model is available:

```bash
curl http://localhost:11434/api/tags
```

Or check in the frontend:
- Settings panel shows all available models
- Models are automatically detected from Ollama

## Model Name Format

Ollama model names can be:
- `gemma3:4b` - Specific tag
- `gemma3` - Latest tag
- `gemma3:latest` - Explicit latest

The system supports all formats.

## Troubleshooting

### Model Not Showing

1. **Check Ollama is running:**
   ```bash
   ollama serve
   ```

2. **Verify model is installed:**
   ```bash
   ollama list
   ```

3. **Pull model if needed:**
   ```bash
   ollama pull gemma3:4b
   ```

### Model Not Working

1. Check model name matches exactly (case-sensitive)
2. Verify model is compatible with ChatOllama
3. Check Ollama logs for errors

## Default Models

The system includes these in the fallback list:
- gemma3:4b (default)
- gemma3:2b
- llama3.2
- llama3
- mistral
- phi3

But it will automatically detect whatever you have installed!
