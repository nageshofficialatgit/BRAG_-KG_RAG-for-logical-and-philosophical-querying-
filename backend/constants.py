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
# Prompt Templates
class PromptTemplates:
    """Reusable prompt templates for philosophy RAG"""
    
    PHILOSOPHY_RESPONSE_STRUCTURE = """You are an expert philosophy assistant with deep knowledge of philosophers, concepts, and arguments.

QUESTION: {question}

CONTEXT FROM REFERENCE MATERIALS:
{context}

INSTRUCTIONS FOR YOUR RESPONSE:
1. **Start with Clarity**: Define key terms and concepts upfront
2. **Historical Context**: Mention relevant philosophers and their positions
3. **Arguments Structure**: 
   - State the main position clearly
   - Provide supporting arguments or evidence
   - Acknowledge counterarguments
4. **Use Markdown**:
   - Use **bold** for key concepts
   - Use ## for section headers
   - Use > for important quotes or philosophical positions
   - Use numbered lists for arguments
5. **Cite Sources**: Reference philosophers and texts you're drawing from
6. **Critical Analysis**: Don't just describe - analyze and evaluate

REQUIRED RESPONSE FORMAT:
## Main Concept
[Definition and overview of the central idea]

## Historical Development
[How this concept evolved, key philosophers involved]

## Key Arguments
[Main supporting positions and reasoning]

## Counterarguments
[Common objections and alternative views]

## Relevance
[How this applies today or to the question]

## Conclusion
[Summary and synthesis]

Now provide your comprehensive, well-structured answer:"""

    IMPROVEMENT_PROMPT = """The following response to a philosophy question needs to be improved in structure and comprehensiveness.
Please rewrite it to be more organized and better formatted with markdown.

ORIGINAL RESPONSE:
{response}

ORIGINAL QUESTION:
{question}

AVAILABLE CONTEXT:
{context}

REQUIREMENTS:
1. Use markdown headers (## for sections)
2. Include at least 4-5 major sections
3. Use **bold** for key concepts
4. Explain philosopher names and their contributions
5. Be comprehensive (300+ words minimum)
6. Use > for important quotes
7. Maintain accuracy to original response

IMPROVED RESPONSE:"""

    VALIDATION_PROMPT = """Evaluate this philosophy response for quality and relevance.
Respond with JSON containing: answers_question (bool), accuracy_score (1-5), structure_score (1-5), improvements (list).

QUESTION: {question}
RESPONSE: {response}

JSON:"""

    FACTUAL_QUESTION_PROMPT = """You are a precise philosophy expert answering factual questions.
Provide accurate, concise answers with definitions and key facts.

QUESTION: {question}
CONTEXT: {context}

Answer:"""

    ANALYTICAL_QUESTION_PROMPT = """You are a philosophy expert analyzing and evaluating philosophical ideas.
Provide thoughtful analysis comparing different perspectives.

QUESTION: {question}
CONTEXT: {context}

Answer:"""

    CREATIVE_QUESTION_PROMPT = """You are a creative philosophy thinker exploring hypothetical scenarios and new ideas.
Provide exploratory and speculative answers while grounding them in philosophical principles.

QUESTION: {question}
CONTEXT: {context}

Answer:"""