# Enhanced Web Crawler and Image Services

## Overview

The web crawler and image services have been significantly enhanced with state-of-the-art features, multiple provider support, and improved content extraction.

## Web Crawler Service Enhancements

### Multi-Engine Search
- **DuckDuckGo**: Primary search engine with VQD token extraction
- **Bing**: Secondary search engine with HTML scraping
- **Serper API**: Google search via Serper API (requires API key)

### Features
1. **Parallel Search**: Searches multiple engines simultaneously
2. **Result Deduplication**: Automatically removes duplicate URLs
3. **Improved Content Extraction**:
   - Multiple extraction strategies (article, main, content divs)
   - Metadata extraction (title, description, author, published date)
   - Open Graph and JSON-LD support
   - Clean text processing

4. **Enhanced Summarization**:
   - Option to fetch full page content
   - Better context for LLM summarization
   - Structured prompts for comprehensive summaries

### API Usage

```python
# Basic search
POST /api/crawler/search
{
  "query": "Aristotle free will",
  "num_results": 10,
  "search_engines": ["duckduckgo", "bing"]
}

# Fetch full page content
POST /api/crawler/fetch
{
  "url": "https://example.com/article",
  "max_length": 10000
}

# Search and summarize with full content
POST /api/crawler/summarize
{
  "query": "latest research on free will",
  "num_results": 5,
  "fetch_full_content": true,
  "llm_provider": "ollama"
}
```

## Image Service Enhancements

### Multi-Provider Support
- **DuckDuckGo**: Free, no API key required (primary)
- **Unsplash**: High-quality photos (requires API key)
- **Pexels**: Free stock photos (requires API key)
- **Bing Image Search**: Microsoft's image search (optional API key)

### Features
1. **Provider Fallback**: Tries providers in order until enough results
2. **Deduplication**: Removes duplicate image URLs
3. **Rich Metadata**:
   - Image dimensions
   - Author information
   - Source URLs
   - Thumbnails

4. **Specialized Queries**:
   - Philosopher portraits
   - Concept illustrations

### API Usage

```python
# Basic image search
POST /api/images/search
{
  "query": "Aristotle philosopher",
  "num_results": 10,
  "providers": ["duckduckgo", "unsplash", "pexels"]
}

# Philosopher images
GET /api/images/philosopher/{philosopher_name}?num_results=5

# Concept images
POST /api/images/concept
{
  "concept": "free will",
  "num_results": 5
}
```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Web Search APIs (Optional)
SERPER_API_KEY=your_serper_api_key  # For Google search via Serper

# Image Search APIs (Optional)
UNSPLASH_ACCESS_KEY=your_unsplash_key  # Get from https://unsplash.com/developers
PEXELS_API_KEY=your_pexels_key  # Get from https://www.pexels.com/api/
BING_SEARCH_API_KEY=your_bing_key  # Get from Azure Cognitive Services
```

### API Key Setup

1. **Unsplash**:
   - Visit https://unsplash.com/developers
   - Create a developer account
   - Create an application
   - Copy the Access Key

2. **Pexels**:
   - Visit https://www.pexels.com/api/
   - Sign up for free account
   - Get your API key

3. **Bing Image Search**:
   - Visit https://azure.microsoft.com/en-us/services/cognitive-services/bing-image-search-api/
   - Create Azure account
   - Create Bing Search resource
   - Get API key

4. **Serper** (for Google search):
   - Visit https://serper.dev
   - Sign up and get API key

## Service Architecture

### Web Crawler Flow

```
User Query
    ↓
Parallel Search (DuckDuckGo, Bing, Serper)
    ↓
Result Aggregation & Deduplication
    ↓
Optional: Fetch Full Content
    ↓
LLM Summarization
    ↓
Structured Response
```

### Image Search Flow

```
User Query
    ↓
Try Providers in Order:
  1. DuckDuckGo (always works)
  2. Unsplash (if API key)
  3. Pexels (if API key)
  4. Bing (if API key)
    ↓
Deduplicate Results
    ↓
Return Rich Metadata
```

## Performance Improvements

1. **Async Operations**: All I/O operations are async for better performance
2. **Parallel Processing**: Multiple search engines queried simultaneously
3. **Smart Fallbacks**: If one provider fails, others are tried
4. **Caching Ready**: Structure supports easy caching implementation

## Error Handling

- Graceful degradation: If one provider fails, others continue
- Detailed logging for debugging
- User-friendly error messages
- Timeout handling for slow requests

## Best Practices

1. **API Keys**: Start without API keys (DuckDuckGo works), add keys for better results
2. **Rate Limiting**: Be mindful of API rate limits
3. **Result Limits**: Use appropriate `num_results` to balance quality and speed
4. **Full Content**: Use `fetch_full_content` sparingly (slower but more accurate)

## Example Integration

```python
# In your RAG service
web_context = await self.web_crawler.search_and_summarize(
    question,
    self.llm_service,
    num_results=5,
    fetch_full_content=False  # Set True for better summaries
)

images = await self.image_service.search_images(
    question,
    num_results=3,
    providers=["duckduckgo", "unsplash"]  # Falls back if unsplash fails
)
```

## Future Enhancements

Potential improvements:
- Result caching
- Image similarity search
- Content quality scoring
- Automatic provider selection based on query type
- Web scraping with Playwright for JavaScript-heavy sites
