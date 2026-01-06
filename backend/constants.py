"""
Constants and configuration values for the application
"""
from typing import List

# API Endpoints
class APIEndpoints:
    """API endpoint URLs"""
    DUCKDUCKGO_BASE = "https://duckduckgo.com/"
    DUCKDUCKGO_LINKS = "https://links.duckduckgo.com/d.js"
    DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/"
    DUCKDUCKGO_IMAGES = "https://duckduckgo.com/i.js"
    BING_SEARCH = "https://www.bing.com/search"
    BING_IMAGE_API = "https://api.bing.microsoft.com/v7.0/images/search"
    SERPER_SEARCH = "https://google.serper.dev/search"
    UNSPLASH_SEARCH = "https://api.unsplash.com/search/photos"
    PEXELS_SEARCH = "https://api.pexels.com/v1/search"
    
    # Philosophy-specific sources
    STANFORD_ENCYCLOPEDIA_SEARCH = "https://plato.stanford.edu/search/search?query={query}"
    IEP_SEARCH = "https://iep.utm.edu/search/?q={query}"
    PHILPAPERS_SEARCH = "https://philpapers.org/search.pl?query={query}"

# User Agent
USER_AGENT = "KnowledgeGraphRAG-Bot/1.0 (+https://github.com/your-repo; research bot)"

# Philosophy Domains
PHILOSOPHY_DOMAINS: List[str] = [
    "plato.stanford.edu",
    "iep.utm.edu",
    "philpapers.org",
    "philosophynow.org",
    "philosophybasics.com",
    "philosophy.lander.edu",
    "philosophy.hku.hk",
    "philosophy.ox.ac.uk",
    "philosophy.cornell.edu",
    "philosophy.fas.harvard.edu",
    "philosophy.princeton.edu",
    "philosophy.berkeley.edu",
    "philosophy.mit.edu",
    "philarchive.org",
    "jstor.org",
    "academia.edu",
    "researchgate.net",
    "springer.com",
    "wiley.com",
    "cambridge.org",
    "oxfordhandbooks.com",
    "routledge.com",
]

# Academic Domains
ACADEMIC_DOMAINS: List[str] = [
    ".edu",
    ".ac.uk",
    ".ac.",
    "scholar.google.com",
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
]

# Low Quality Domains
LOW_QUALITY_DOMAINS: List[str] = [
    "quora.com",
    "reddit.com",
    "yahoo.com",
    "answers.com",
    "wiki.answers.com",
    "ask.com",
]

# Philosophy Keywords
PHILOSOPHY_KEYWORDS: List[str] = [
    "philosophy",
    "philosopher",
    "philosophical",
    "ethics",
    "metaphysics",
    "epistemology",
    "philosophical analysis",
    "philosophical theory",
    "academic philosophy",
    "philosophy paper",
    "philosophy article",
    "philosophy journal",
]

# Academic Indicators
ACADEMIC_INDICATORS: List[str] = [
    "journal",
    "article",
    "paper",
    "scholar",
    "academic",
    "research",
    "study",
    "analysis",
    "theory",
    "encyclopedia",
]

# Philosophy Indicators
PHILOSOPHY_INDICATORS: List[str] = [
    "philosophy",
    "philosopher",
    "philosophical",
    "ethics",
    "metaphysics",
    "epistemology",
    "philosophical theory",
    "philosophical analysis",
]

# Common Philosophers
COMMON_PHILOSOPHERS: List[str] = [
    "Aristotle",
    "Plato",
    "Socrates",
    "Kant",
    "Hume",
    "Descartes",
    "Nietzsche",
    "Hegel",
    "Locke",
    "Berkeley",
    "Leibniz",
    "Spinoza",
    "Wittgenstein",
    "Russell",
    "Heidegger",
    "Sartre",
    "Mill",
    "Rawls",
    "Nozick",
    "Quine",
    "Kripke",
    "Searle",
    "Chalmers",
]

# Philosophy Entity Types
PHILOSOPHY_ENTITY_TYPES: List[str] = [
    "Philosopher",
    "Concept",
    "Work",
    "SchoolOfThought",
    "Argument",
    "Theory",
    "Principle",
    "Doctrine",
    "Tradition",
]

# Philosophy Relationship Types
PHILOSOPHY_RELATIONSHIP_TYPES: List[str] = [
    "INFLUENCES",
    "CONTRADICTS",
    "BUILDS_ON",
    "REFERENCES",
    "DISCUSSES",
    "AGREES_WITH",
    "DISAGREES_WITH",
    "INSPIRED_BY",
    "CRITIQUES",
    "SUPPORTS",
    "OPPOSES",
    "DEVELOPS",
    "CHALLENGES",
    "RESPONDS_TO",
]

# Quality Scoring Weights
class QualityScores:
    """Quality scoring weights and thresholds"""
    PHILOSOPHY_DOMAIN_SCORE = 10.0
    ACADEMIC_DOMAIN_SCORE = 5.0
    PHILOSOPHY_KEYWORD_TITLE = 2.0
    PHILOSOPHY_KEYWORD_SNIPPET = 1.0
    ACADEMIC_INDICATOR_TITLE = 1.5
    ACADEMIC_INDICATOR_SNIPPET = 0.5
    LOW_QUALITY_DOMAIN_PENALTY = -3.0
    SHORT_SNIPPET_PENALTY = -2.0
    SHORT_SNIPPET_THRESHOLD = 50
    
    # Direct source scores
    STANFORD_ENCYCLOPEDIA_SCORE = 15.0
    IEP_SCORE = 15.0
    PHILPAPERS_SCORE = 12.0

# Search Configuration
class SearchConfig:
    """Search-related configuration constants"""
    MAX_ENHANCED_QUERIES = 5
    MAX_PHILOSOPHER_CONTEXT = 2
    DEFAULT_MIN_QUALITY_SCORE = 0.0
    QUERY_MULTIPLIER = 2  # Multiply num_results when searching with enhanced queries

# HTTP Headers
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
