# Robots.txt Compliance

## Overview

Our web crawler now fully respects robots.txt files, making it an ethical and legal web scraping solution. This is what makes an internet-based RAG system great - respecting website owners' wishes.

## Features

### 1. Robots.txt Parsing
- Automatically fetches and parses robots.txt files
- Supports all standard directives:
  - `User-agent`
  - `Allow`
  - `Disallow`
  - `Crawl-delay`
  - `Sitemap`
- Pattern matching with wildcards (`*`) and path matching

### 2. Compliance Checking
- Checks robots.txt before fetching any URL
- Respects user-agent specific rules
- Falls back to wildcard (`*`) rules if no specific user-agent match
- Blocks requests to disallowed paths

### 3. Rate Limiting
- Respects `Crawl-delay` directives
- Tracks last request time per domain
- Automatically waits between requests to the same domain
- Prevents overwhelming servers

### 4. Caching
- Caches robots.txt files for 24 hours
- Reduces redundant requests
- Improves performance

## Configuration

### Environment Variables

```env
# Enable/disable robots.txt compliance (default: true)
RESPECT_ROBOTS_TXT=true

# Default crawl delay in seconds (used if robots.txt doesn't specify)
DEFAULT_CRAWL_DELAY=1.0
```

### User Agent

Our crawler identifies itself as:
```
KnowledgeGraphRAG-Bot/1.0 (+https://github.com/your-repo; research bot)
```

Website owners can specifically allow or disallow our bot in their robots.txt:
```
User-agent: KnowledgeGraphRAG-Bot
Allow: /
Crawl-delay: 2
```

## How It Works

### 1. Before Fetching a URL

```python
# Check if URL is allowed
can_fetch = await robots_parser.can_fetch(url, user_agent)

if not can_fetch:
    # Skip this URL
    return {"error": "Blocked by robots.txt"}
```

### 2. Rate Limiting

```python
# Get crawl delay from robots.txt
delay = await robots_parser.get_crawl_delay(url, user_agent)

# Wait if needed
await rate_limiter.wait_if_needed(url, delay)
```

### 3. Pattern Matching

The parser supports robots.txt patterns:
- `*` matches any sequence of characters
- `/` matches root path
- `$` matches end of string

Examples:
- `Disallow: /private/` - Blocks all paths starting with `/private/`
- `Allow: /public/*` - Allows all paths starting with `/public/`
- `Disallow: /*.pdf$` - Blocks all PDF files

## API Usage

### Fetch with Robots Check

```python
POST /api/crawler/fetch
{
  "url": "https://example.com/article",
  "max_length": 10000,
  "check_robots": true  # Default: true
}
```

### Search and Summarize

```python
POST /api/crawler/summarize
{
  "query": "Aristotle free will",
  "num_results": 5,
  "fetch_full_content": true,
  "respect_robots": true  # Default: true
}
```

## Response Format

When a URL is blocked by robots.txt:

```json
{
  "url": "https://example.com/blocked",
  "success": false,
  "error": "Blocked by robots.txt",
  "blocked_by_robots": true
}
```

When successfully fetched:

```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "...",
  "success": true,
  "robots_respected": true
}
```

## Best Practices

1. **Always Respect robots.txt**: Keep `RESPECT_ROBOTS_TXT=true` in production
2. **Use Appropriate User Agent**: Identify your bot clearly
3. **Respect Crawl Delays**: Don't overwhelm servers
4. **Handle Blocks Gracefully**: Skip blocked URLs, don't fail
5. **Cache robots.txt**: Reduces server load

## Examples

### Example robots.txt

```
User-agent: *
Disallow: /private/
Disallow: /admin/
Allow: /public/

User-agent: KnowledgeGraphRAG-Bot
Allow: /
Crawl-delay: 2

Sitemap: https://example.com/sitemap.xml
```

### What Happens

1. Generic bots (`*`): Can access `/public/`, blocked from `/private/` and `/admin/`
2. Our bot: Can access everything, but must wait 2 seconds between requests
3. Sitemap: Available for discovery

## Legal and Ethical Considerations

### Why This Matters

1. **Legal Compliance**: Respecting robots.txt helps avoid legal issues
2. **Server Resources**: Prevents overwhelming websites
3. **Ethical Scraping**: Shows respect for website owners
4. **Good Citizenship**: Maintains good relationships with content providers

### When to Disable

Only disable robots.txt checking if:
- You have explicit permission from website owners
- You're testing on your own websites
- You're using official APIs instead of scraping

## Implementation Details

### Robots Parser

Located in `backend/services/robots_parser.py`:
- `RobotsParser`: Parses and checks robots.txt
- `RateLimiter`: Manages crawl delays

### Integration

The web crawler service automatically:
1. Checks robots.txt before fetching
2. Respects crawl delays
3. Logs blocked URLs
4. Returns appropriate error messages

## Monitoring

The system logs:
- When URLs are blocked by robots.txt
- When crawl delays are applied
- When robots.txt files are fetched and cached

Check logs for:
```
INFO: Blocked by robots.txt: https://example.com/private
INFO: Applied crawl delay of 2.0s for example.com
```

## Future Enhancements

Potential improvements:
- Sitemap parsing for better discovery
- Robots.txt statistics and reporting
- Per-domain robots.txt caching strategies
- Support for robots meta tags in HTML
