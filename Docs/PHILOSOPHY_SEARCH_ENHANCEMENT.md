# Philosophy-Specific Search Enhancement

## The Problem

Generic web searches often return:
- Random blog posts
- Low-quality forum discussions
- Irrelevant commercial content
- Non-academic sources
- Content that mentions keywords but isn't actually about philosophy

## The Solution

We've implemented a **Philosophy Search Enhancer** that ensures we get high-quality, relevant philosophy content.

## Key Features

### 1. Query Enhancement

Instead of searching for just "free will", we now search for:
- "free will philosophy"
- "free will philosophical analysis"
- "free will academic paper"
- "free will scholarly article"
- "Aristotle free will" (if context mentions Aristotle)

This ensures we get philosophy-specific results, not random mentions.

### 2. Quality Scoring System

Every result is scored based on:

**High-Quality Philosophy Sources (Score +10):**
- Stanford Encyclopedia of Philosophy (plato.stanford.edu)
- Internet Encyclopedia of Philosophy (iep.utm.edu)
- PhilPapers (philpapers.org)
- PhilArchive (philarchive.org)
- Major university philosophy departments

**Academic Sources (Score +5):**
- .edu domains
- .ac.uk domains
- JSTOR, Springer, Cambridge, Oxford
- Academia.edu, ResearchGate

**Content Quality Indicators (Score +1-2):**
- Philosophy keywords in title/snippet
- Academic indicators (journal, article, paper, scholar)
- Substantial content (not just short snippets)

**Penalties:**
- Low-quality domains (Quora, Yahoo Answers): -3
- Very short snippets: -2

### 3. Direct Philosophy Source Links

Before even searching, we add direct links to:
- Stanford Encyclopedia search
- Internet Encyclopedia search
- PhilPapers search

These are guaranteed high-quality sources.

### 4. Result Filtering and Ranking

Results are:
1. **Scored** by quality
2. **Filtered** by minimum quality threshold
3. **Ranked** with philosophy sources first
4. **Deduplicated** to avoid repeats

### 5. Philosophy Relevance Check

Every result is checked to ensure it's actually about philosophy, not just mentioning keywords.

## How It Works

### Example: "What is free will?"

**Step 1: Query Enhancement**
```
Original: "free will"
Enhanced:
- "free will philosophy"
- "free will philosophical analysis"  
- "free will academic paper"
```

**Step 2: Direct Sources**
```
Added automatically:
- Stanford Encyclopedia: free will
- Internet Encyclopedia: free will
- PhilPapers: free will
```

**Step 3: Search & Score**
```
Results from search engines are scored:
- plato.stanford.edu/entries/freewill/ → Score: 15.0
- iep.utm.edu/freewill/ → Score: 15.0
- random-blog.com/free-will → Score: 1.0
- quora.com/what-is-free-will → Score: -2.0
```

**Step 4: Filter & Rank**
```
Final results (top 5):
1. Stanford Encyclopedia (Score: 15.0)
2. Internet Encyclopedia (Score: 15.0)
3. Academic paper from JSTOR (Score: 8.0)
4. University philosophy page (Score: 7.0)
5. Philosophy journal article (Score: 6.0)
```

## Configuration

### API Parameters

```python
POST /api/crawler/search
{
  "query": "free will",
  "num_results": 5,
  "prioritize_philosophy": true,  # Default: true
  "min_quality_score": 0.0  # Filter out negative scores
}
```

### Quality Score Thresholds

- **0.0**: Include all results (default)
- **3.0**: Only academic/philosophy sources
- **5.0**: Only high-quality philosophy sources
- **10.0**: Only top philosophy encyclopedias

## Philosophy Domains Prioritized

### Top Tier (Score +10)
- plato.stanford.edu - Stanford Encyclopedia
- iep.utm.edu - Internet Encyclopedia
- philpapers.org - PhilPapers
- philarchive.org - PhilArchive

### Academic Tier (Score +5)
- Major university philosophy departments
- Academic publishers (JSTOR, Springer, etc.)
- Research platforms (Academia.edu, ResearchGate)

## Benefits

1. **Relevance**: Results are actually about philosophy
2. **Quality**: Prioritizes academic and authoritative sources
3. **Accuracy**: Reduces noise from random web content
4. **Efficiency**: Direct links to best sources
5. **Context-Aware**: Enhances queries based on conversation context

## Example Results Comparison

### Without Enhancement
```
1. "Free Will" - Wikipedia (general article)
2. "Do we have free will?" - Reddit discussion
3. "Free Will Software" - Commercial product
4. "Free Will Astrology" - Horoscope column
5. "Free Will Baptist Church" - Religious organization
```

### With Enhancement
```
1. "Free Will" - Stanford Encyclopedia of Philosophy
2. "Free Will" - Internet Encyclopedia of Philosophy
3. "Free Will and Determinism" - Academic paper (JSTOR)
4. "The Problem of Free Will" - Philosophy journal article
5. "Free Will: A Philosophical Analysis" - University course page
```

## Integration

The enhancement is automatically applied to:
- All RAG queries (via `rag_service.py`)
- Web crawler searches
- Search and summarize operations

You can control it via:
- `prioritize_philosophy` parameter (default: true)
- `min_quality_score` parameter (default: 0.0)

## Future Enhancements

Potential improvements:
- Machine learning-based relevance scoring
- User feedback integration
- Domain-specific knowledge bases
- Citation network analysis
- Temporal relevance (recent vs. classic works)
