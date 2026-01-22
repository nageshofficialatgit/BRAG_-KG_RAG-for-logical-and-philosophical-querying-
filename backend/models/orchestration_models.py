from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum

class QueryType(str, Enum):
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    META = "meta"

class FocusMode(str, Enum):
    SPEED = "speed"
    BALANCED = "balanced"
    QUALITY = "quality"

class QueryClassification(BaseModel):
    """Output of query classifier"""
    query_type: QueryType
    requires_web: bool
    local_knowledge_confidence: float  # 0-1
    temperature: float
    focus_mode: FocusMode
    reasoning_depth: int  # 1-3

class CoTStep(BaseModel):
    """Single reasoning step"""
    step_number: int
    reasoning: str
    importance: str  # high, medium, low

class CoTResult(BaseModel):
    """Output of CoT generator"""
    reasoning_steps: List[CoTStep]
    key_questions: List[str]
    search_terms: List[str]
    overall_logic_quality: float  # 0-1

class SearchResult(BaseModel):
    """Single search result"""
    title: str
    url: str
    snippet: str
    source: str
    freshness_score: float  # 0-1 (1=very recent)
    relevance_score: Optional[float] = None

class SynthesizedContext(BaseModel):
    """Combined context from all sources"""
    full_context: str  # Formatted for LLM consumption
    source_map: Dict[int, str]  # Citation number to URL
    cot_steps: List[str]
    search_results: List[SearchResult]
    local_knowledge: Dict[str, Any]

class GeneratedAnswer(BaseModel):
    """Final answer with metadata"""
    answer: str
    sources: List[SearchResult]
    confidence_score: float
    confidence_level: str  # high, medium, low
    model_used: str
    reasoning_transparency: Dict[str, Any]

class ConfidenceFactor(BaseModel):
    source_quality: float
    context_alignment: float
    citation_coverage: float
    reasoning_consistency: float

class ConfidenceScore(BaseModel):
    overall_score: float  # 0-1
    level: str  # high, medium, low
    factors: ConfidenceFactor
    should_regenerate: bool
    regeneration_reason: Optional[str] = None

class OrchestratedSearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    focus_mode: FocusMode = FocusMode.BALANCED
    include_web: bool = True
    include_local: bool = True
    include_widgets: bool = True

class OrchestratedSearchResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: Dict[str, Any]
    reasoning: Dict[str, Any]
    session_id: Optional[str] = None
    processing_time_seconds: float
    model_used: str
