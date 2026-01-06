# Code Quality Improvements

## Overview

All hardcoded values have been removed and replaced with proper configuration management following best coding practices.

## Changes Made

### 1. Created Constants Module (`backend/constants.py`)

**Purpose**: Centralized location for all constants, URLs, and configuration values.

**Contents**:
- API endpoint URLs (all external service URLs)
- Domain lists (philosophy, academic, low-quality)
- Keyword lists (philosophy, academic indicators)
- Quality scoring weights
- Search configuration constants
- HTTP headers
- User agent string

### 2. Enhanced Configuration (`backend/config.py`)

**Added**:
- Philosophy search configuration options
- User agent configuration (name, version, URL)
- Quality score thresholds
- Query enhancement limits

**Benefits**:
- All settings configurable via environment variables
- No hardcoded values in business logic
- Easy to adjust without code changes

### 3. Refactored Services

**Philosophy Search Enhancer**:
- ✅ Removed hardcoded domain lists → Uses `constants.py`
- ✅ Removed hardcoded URLs → Uses `APIEndpoints` class
- ✅ Removed magic numbers → Uses `QualityScores` class
- ✅ Removed hardcoded philosopher list → Uses `COMMON_PHILOSOPHERS`
- ✅ Uses `settings` for configuration values

**Web Crawler Service**:
- ✅ Removed hardcoded URLs → Uses `APIEndpoints`
- ✅ Removed hardcoded user agent → Uses `settings.USER_AGENT`
- ✅ Removed hardcoded headers → Uses `DEFAULT_HEADERS`
- ✅ Uses constants for all configuration

**Image Service**:
- ✅ Removed hardcoded URLs → Uses `APIEndpoints`
- ✅ Removed hardcoded user agent → Uses `settings.USER_AGENT`
- ✅ Removed hardcoded headers → Uses `DEFAULT_HEADERS`

## Configuration Structure

### Environment Variables

All configuration is now externalized:

```env
# Philosophy Search
PRIORITIZE_PHILOSOPHY=true
MIN_QUALITY_SCORE=0.0
MAX_ENHANCED_QUERIES=5
MAX_PHILOSOPHER_CONTEXT=2

# User Agent
USER_AGENT_NAME=KnowledgeGraphRAG-Bot
USER_AGENT_VERSION=1.0
USER_AGENT_URL=+https://github.com/your-repo; research bot
```

### Constants File Structure

```python
# API Endpoints - All URLs in one place
class APIEndpoints:
    DUCKDUCKGO_BASE = "..."
    BING_SEARCH = "..."
    # etc.

# Quality Scoring - All weights configurable
class QualityScores:
    PHILOSOPHY_DOMAIN_SCORE = 10.0
    ACADEMIC_DOMAIN_SCORE = 5.0
    # etc.

# Search Configuration
class SearchConfig:
    MAX_ENHANCED_QUERIES = 5
    QUERY_MULTIPLIER = 2
    # etc.
```

## Benefits

### 1. Maintainability
- Change URLs in one place (`constants.py`)
- Adjust scoring weights without touching business logic
- Update domain lists easily

### 2. Testability
- Easy to mock constants
- Can override settings for testing
- Isolated configuration

### 3. Flexibility
- All values configurable via environment variables
- Easy to add new domains/keywords
- Simple to adjust thresholds

### 4. Best Practices
- ✅ No magic numbers
- ✅ No hardcoded strings
- ✅ Single source of truth
- ✅ Separation of concerns
- ✅ Configuration externalized

## Example: Adding a New Philosophy Domain

**Before** (hardcoded):
```python
# Had to find and modify in multiple places
PHILOSOPHY_DOMAINS = [...]
```

**After** (configurable):
```python
# Add to constants.py
PHILOSOPHY_DOMAINS.append("new-philosophy-site.edu")

# Or via environment variable (future enhancement)
```

## Example: Changing Quality Scores

**Before** (hardcoded):
```python
score += 10.0  # What does 10.0 mean?
```

**After** (named constants):
```python
score += QualityScores.PHILOSOPHY_DOMAIN_SCORE  # Clear intent
```

## Code Organization

```
backend/
├── constants.py          # All constants, URLs, lists
├── config.py            # Environment-based configuration
├── services/
│   ├── philosophy_search_enhancer.py  # Uses constants & config
│   ├── web_crawler_service.py         # Uses constants & config
│   └── image_service.py               # Uses constants & config
```

## Future Enhancements

Potential improvements:
1. Load domain lists from JSON/YAML files
2. Database-backed configuration
3. Runtime configuration updates
4. Configuration validation
5. Configuration documentation generation

## Testing Benefits

With this structure:
- Easy to create test fixtures
- Can override constants in tests
- Mock external URLs easily
- Test different configurations

## Migration Notes

All existing functionality preserved:
- Default values match previous hardcoded values
- Backward compatible
- No breaking changes
- All features work as before
