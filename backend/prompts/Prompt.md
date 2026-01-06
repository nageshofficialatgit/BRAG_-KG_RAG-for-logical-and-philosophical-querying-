# Philosophy RAG Prompts

This directory contains decoupled prompt templates following the [Microsoft GraphRAG pattern](https://github.com/microsoft/graphrag/tree/main/graphrag/prompts).

## Structure

Each prompt is stored as a separate `.txt` file, allowing for:
- **Easy modification** without code changes
- **Version control** friendly diffs
- **Reusability** across different services
- **Hot-reloading** capability

## Available Prompts

### 1. `philosophy_response.txt`
**Purpose**: Primary response generation template
**Use Case**: General philosophy questions requiring structured, comprehensive answers
**Features**:
- Structured format with clear sections
- Markdown formatting instructions
- Citation requirements
- Critical analysis guidance

**Template Variables**: `{question}`, `{context}`

### 2. `factual_question.txt`
**Purpose**: Factual question answering
**Use Case**: "What is...", "Define...", "Who is..." questions
**Features**:
- Precise, concise responses
- Definition-focused
- Key facts emphasis

**Template Variables**: `{question}`, `{context}`

### 3. `analytical_question.txt`
**Purpose**: Analytical and evaluative questions
**Use Case**: "Discuss...", "Compare...", "Evaluate..." questions
**Features**:
- Multi-perspective analysis
- Comparative evaluation
- Argument assessment

**Template Variables**: `{question}`, `{context}`

### 4. `creative_question.txt`
**Purpose**: Creative and exploratory questions
**Use Case**: "Imagine...", "Propose...", "How could..." questions
**Features**:
- Exploratory reasoning
- Speculative thinking
- Grounded in philosophical principles

**Template Variables**: `{question}`, `{context}`

### 5. `improvement.txt`
**Purpose**: Response quality enhancement
**Use Case**: Auto-improving low-quality responses
**Features**:
- Restructuring guidance
- Markdown compliance
- Comprehensiveness requirements

**Template Variables**: `{response}`, `{question}`, `{context}`

### 6. `validation.txt`
**Purpose**: Response quality assessment
**Use Case**: Evaluating response quality and relevance
**Features**:
- Multi-criteria evaluation
- JSON output format
- Improvement suggestions

**Template Variables**: `{question}`, `{response}`

## Usage

### Loading Prompts in Code

```python
from backend.services.prompt_loader import PromptLoader

# Initialize loader (auto-detects backend/prompts directory)
loader = PromptLoader()

# Get single prompt
prompt = loader.get_prompt("philosophy_response")

# Format with variables
formatted = loader.format_prompt(
    "philosophy_response",
    question="What is Kant's categorical imperative?",
    context="Philosophy context..."
)

# List all available prompts
available = loader.list_available()
```

### Using with RAGService

The RAGService automatically uses PromptLoader for question classification:

```python
# Questions are classified and matched to appropriate prompts
rag_service.query("What is Aristotle's concept of virtue?")  # Uses factual_question.txt
rag_service.query("Compare Plato and Aristotle's epistemologies")  # Uses analytical_question.txt
```

## Modifying Prompts

### Via Code
```python
loader = PromptLoader()

# Update a prompt
new_content = "Your improved prompt template..."
loader.set_prompt("philosophy_response", new_content)

# Changes are automatically saved to disk
```

### Via File
Simply edit the `.txt` files directly. Changes take effect after the PromptLoader cache is cleared.

## Best Practices

1. **Use Template Variables**: Use `{variable}` syntax for dynamic content
2. **Markdown Formatting**: Include markdown instructions in prompts
3. **Clear Instructions**: Make instructions explicit and actionable
4. **Philosopher Context**: Emphasize philosophical grounding
5. **Versioning**: Keep old prompts as `prompt_name.v1.txt` for easy rollback

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Update `PromptLoader.PROMPT_FILES` dict in `prompt_loader.py`
3. Register in `RAGService._get_prompt_name()` if it needs question classification

Example:
```python
# prompt_loader.py
PROMPT_FILES = {
    # ... existing prompts ...
    "my_new_prompt": "my_new_prompt.txt",
}

# rag_service.py
def _get_prompt_name(self, question_type: str) -> str:
    prompt_map = {
        # ... existing mappings ...
        "new_type": "my_new_prompt",
    }
```

## Performance Notes

- Prompts are **cached in memory** after first load
- Use `loader.reload_cache()` to force disk reload
- Loading time is negligible even with large prompts
- Consider prompt length for token limits

## Extending

For more complex prompt management (versioning, A/B testing, analytics), consider:
- Database storage of prompts
- Prompt version control system
- Performance metrics collection
- Dynamic prompt generation based on context
