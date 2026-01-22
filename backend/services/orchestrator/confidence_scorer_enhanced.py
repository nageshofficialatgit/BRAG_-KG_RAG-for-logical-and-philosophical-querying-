from typing import List, Dict, Any
from backend.models.orchestration_models import (
    ConfidenceScore, SearchResult, ConfidenceFactor
)

class EnhancedConfidenceScorerService:
    """
    Multi-factor confidence scoring:
    - Source quality (domain authority, recency)
    - Context alignment (does context match query?)
    - Citation coverage (is answer well-cited?)
    - Reasoning consistency (do CoT steps support answer?)
    - Self-consistency (would answer be consistent if re-asked?)
    """
    
    async def score_answer(
        self,
        query: str,
        answer: str,
        sources: List[SearchResult],
        cot_steps: List[str]
    ) -> ConfidenceScore:
        """
        Returns confidence score
        """
        
        scores = {
            "source_quality": await self.score_source_quality(sources),
            "context_alignment": await self.score_context_alignment(query, answer),
            "citation_coverage": self.score_citation_coverage(answer, sources),
            "reasoning_consistency": await self.score_reasoning_consistency(
                answer, cot_steps
            )
        }
        
        # Weighted average
        weights = {
            "source_quality": 0.25,
            "context_alignment": 0.25,
            "citation_coverage": 0.25,
            "reasoning_consistency": 0.25
        }
        
        overall = sum(
            scores[key] * weights[key] for key in scores
        )
        
        # Determine if regeneration needed
        should_regenerate = overall < 0.6 or any(
            score < 0.4 for score in scores.values()
        )
        
        return ConfidenceScore(
            overall_score=overall,
            level="high" if overall > 0.8 else "medium" if overall > 0.6 else "low",
            factors=ConfidenceFactor(
                source_quality=scores["source_quality"],
                context_alignment=scores["context_alignment"],
                citation_coverage=scores["citation_coverage"],
                reasoning_consistency=scores["reasoning_consistency"]
            ),
            should_regenerate=should_regenerate,
            regeneration_reason=self.get_regeneration_reason(scores) if should_regenerate else None
        )
        
    async def score_source_quality(self, sources: List[SearchResult]) -> float:
        if not sources:
            return 0.5
        score = 0
        for s in sources:
            # Simple heuristic: longer snippets and valid sources = better
            score += 0.5 + (0.1 if len(s.snippet) > 100 else 0)
        return min(1.0, score / len(sources))

    async def score_context_alignment(self, query: str, answer: str) -> float:
        # Placeholder: Ideally uses LLM to check alignment
        return 0.8

    def score_citation_coverage(self, answer: str, sources: List[SearchResult]) -> float:
        if not sources:
            return 0.5
        # Count citations
        import re
        citations = len(re.findall(r'\[\d+\]', answer))
        return min(1.0, citations / (len(sources) or 1))

    async def score_reasoning_consistency(self, answer: str, cot_steps: List[str]) -> float:
        # Placeholder
        return 0.8

    def get_regeneration_reason(self, scores: Dict[str, float]) -> str:
        lowest = min(scores, key=scores.get)
        return f"Low score in {lowest}"
