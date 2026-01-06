"""
Confidence scoring service for RAG responses
Assesses reliability based on multiple factors
"""
from typing import Dict, Any, List
import logging
from backend.config import settings

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Score confidence/reliability of RAG responses"""
    
    def __init__(self):
        self.context_weight = settings.CONFIDENCE_CONTEXT_WEIGHT
        self.source_weight = settings.CONFIDENCE_SOURCE_WEIGHT
        self.citation_weight = settings.CONFIDENCE_CITATION_WEIGHT
        self.coverage_weight = settings.CONFIDENCE_COVERAGE_WEIGHT
        self.threshold_high = settings.CONFIDENCE_THRESHOLD_HIGH
        self.threshold_medium = settings.CONFIDENCE_THRESHOLD_MEDIUM
    
    def score(
        self,
        response: str,
        context_quality: float = 0.5,
        sources_count: int = 0,
        has_citations: bool = False,
        topic_coverage: float = 0.5,
        is_improved: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate confidence score based on multiple factors
        
        Args:
            response: The response text
            context_quality: Quality of retrieved context (0-1)
            sources_count: Number of sources used
            has_citations: Whether response cites sources
            topic_coverage: How well question is covered (0-1)
            is_improved: Whether response was improved by LLM
            
        Returns:
            Dict with overall score, level, factors, and warnings
        """
        try:
            # Calculate individual factor scores
            factors = {
                "context_quality": self._score_context_quality(context_quality),
                "source_count": self._score_source_count(sources_count),
                "citations": self._score_citations(has_citations),
                "coverage": self._score_coverage(topic_coverage),
                "improvement": 0.1 if is_improved else 0.0  # Slight penalty for needing improvement
            }
            
            # Weighted overall score
            overall_score = (
                factors["context_quality"] * self.context_weight +
                factors["source_count"] * self.source_weight +
                factors["citations"] * self.citation_weight +
                factors["coverage"] * self.coverage_weight
            ) - factors["improvement"]
            
            overall_score = min(max(overall_score, 0.0), 1.0)
            
            # Categorize confidence level
            if overall_score >= self.threshold_high:
                confidence_level = "High"
            elif overall_score >= self.threshold_medium:
                confidence_level = "Medium"
            else:
                confidence_level = "Low"
            
            # Generate warnings
            warnings = self._generate_warnings(
                sources_count, has_citations, context_quality, is_improved
            )
            
            return {
                "score": round(overall_score, 2),
                "level": confidence_level,
                "factors": {
                    "context_quality": round(factors["context_quality"], 2),
                    "source_count": round(factors["source_count"], 2),
                    "citations": round(factors["citations"], 2),
                    "coverage": round(factors["coverage"], 2)
                },
                "warnings": warnings if warnings else None,
                "recommendation": self._get_recommendation(confidence_level, warnings)
            }
        except Exception as e:
            logger.error(f"Error scoring confidence: {e}")
            return {
                "score": 0.5,
                "level": "Unknown",
                "factors": {},
                "warnings": [f"Error calculating confidence: {str(e)}"],
                "recommendation": "Please verify response accuracy manually"
            }
    
    def _score_context_quality(self, quality: float) -> float:
        """Score based on context quality (0-1 input)"""
        # Directly use provided quality score
        return max(0.0, min(1.0, quality))
    
    def _score_source_count(self, count: int) -> float:
        """Score based on number of sources"""
        # 0 sources: 0.3, 1-2 sources: 0.6, 3-5 sources: 0.85, 5+ sources: 1.0
        if count == 0:
            return 0.3
        elif count <= 2:
            return 0.6
        elif count <= 5:
            return 0.85
        else:
            return 1.0
    
    def _score_citations(self, has_citations: bool) -> float:
        """Score based on whether response cites sources"""
        return 1.0 if has_citations else 0.5
    
    def _score_coverage(self, coverage: float) -> float:
        """Score based on topic coverage (0-1 input)"""
        return max(0.0, min(1.0, coverage))
    
    def _generate_warnings(
        self,
        sources_count: int,
        has_citations: bool,
        context_quality: float,
        is_improved: bool
    ) -> List[str]:
        """Generate warnings about response reliability"""
        warnings = []
        
        if sources_count == 0:
            warnings.append("No sources were used in retrieval")
        elif sources_count < 2:
            warnings.append("Limited number of sources (< 2)")
        
        if not has_citations:
            warnings.append("Response does not cite specific sources or philosophers")
        
        if context_quality < 0.5:
            warnings.append("Retrieved context quality is low")
        
        if is_improved:
            warnings.append("Response required improvement and was regenerated")
        
        return warnings
    
    def _get_recommendation(self, level: str, warnings: List[str]) -> str:
        """Get recommendation based on confidence level and warnings"""
        if level == "High":
            return "Response is reliable and well-sourced"
        elif level == "Medium":
            return "Response is generally reliable but verify critical claims"
        else:
            return "Please verify response thoroughly before relying on it"
    
    def compare_scores(
        self,
        score1: Dict[str, Any],
        score2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two confidence scores
        
        Args:
            score1, score2: Two confidence score dicts
            
        Returns:
            Comparison with winner and differences
        """
        return {
            "better_response": 1 if score1["score"] > score2["score"] else 2,
            "score_difference": abs(score1["score"] - score2["score"]),
            "score1": score1["score"],
            "score2": score2["score"],
            "level1": score1["level"],
            "level2": score2["level"]
        }
