"""
Philosophy-specific search enhancement for better relevance and quality
"""
from typing import List, Dict, Any, Optional
import re
import logging
from urllib.parse import quote_plus
from backend.constants import (
    PHILOSOPHY_DOMAINS,
    ACADEMIC_DOMAINS,
    LOW_QUALITY_DOMAINS,
    PHILOSOPHY_KEYWORDS,
    ACADEMIC_INDICATORS,
    PHILOSOPHY_INDICATORS,
    COMMON_PHILOSOPHERS,
    QualityScores,
    SearchConfig,
    APIEndpoints,
)
from backend.config import settings

logger = logging.getLogger(__name__)

class PhilosophySearchEnhancer:
    """Enhances web searches for philosophy-specific content"""
    
    def __init__(self):
        self.philosophy_domains = PHILOSOPHY_DOMAINS
        self.academic_domains = ACADEMIC_DOMAINS
        self.low_quality_domains = LOW_QUALITY_DOMAINS
        self.philosophy_keywords = PHILOSOPHY_KEYWORDS
        self.academic_indicators = ACADEMIC_INDICATORS
        self.philosophy_indicators = PHILOSOPHY_INDICATORS
        self.common_philosophers = COMMON_PHILOSOPHERS
        self.max_enhanced_queries = settings.MAX_ENHANCED_QUERIES
        self.max_philosopher_context = settings.MAX_PHILOSOPHER_CONTEXT
    
    def enhance_query(self, query: str, context: Optional[str] = None) -> List[str]:
        """Generate enhanced queries for better philosophy-specific results"""
        enhanced_queries = []
        
        # Original query
        enhanced_queries.append(query)
        
        # Add philosophy context if not present
        query_lower = query.lower()
        has_philosophy_keyword = any(kw in query_lower for kw in self.philosophy_keywords)
        
        if not has_philosophy_keyword:
            # Add philosophy context
            enhanced_queries.append(f"{query} philosophy")
            enhanced_queries.append(f"{query} philosophical analysis")
        
        # Add academic context
        enhanced_queries.append(f"{query} academic paper")
        enhanced_queries.append(f"{query} scholarly article")
        
        # If context mentions specific philosophers, enhance
        if context:
            philosophers = self._extract_philosophers(context)
            for philosopher in philosophers[:self.max_philosopher_context]:
                enhanced_queries.append(f"{philosopher} {query}")
        
        return enhanced_queries[:self.max_enhanced_queries]
    
    def _extract_philosophers(self, text: str) -> List[str]:
        """Extract philosopher names from text"""
        found = []
        text_lower = text.lower()
        for philosopher in self.common_philosophers:
            if philosopher.lower() in text_lower:
                found.append(philosopher)
        
        return found
    
    def score_result_quality(self, result: Dict[str, Any]) -> float:
        """Score result quality based on domain and content"""
        score = 0.0
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # High-quality philosophy domains (highest score)
        for domain in self.philosophy_domains:
            if domain in url:
                score += QualityScores.PHILOSOPHY_DOMAIN_SCORE
                break
        
        # Academic domains
        for domain in self.academic_domains:
            if domain in url:
                score += QualityScores.ACADEMIC_DOMAIN_SCORE
                break
        
        # Philosophy keywords in title
        for keyword in self.philosophy_keywords:
            if keyword in title:
                score += QualityScores.PHILOSOPHY_KEYWORD_TITLE
            if keyword in snippet:
                score += QualityScores.PHILOSOPHY_KEYWORD_SNIPPET
        
        # Academic indicators
        for indicator in self.academic_indicators:
            if indicator in title:
                score += QualityScores.ACADEMIC_INDICATOR_TITLE
            if indicator in snippet:
                score += QualityScores.ACADEMIC_INDICATOR_SNIPPET
        
        # Penalize low-quality domains
        for domain in self.low_quality_domains:
            if domain in url:
                score += QualityScores.LOW_QUALITY_DOMAIN_PENALTY
        
        # Penalize very short snippets (likely low quality)
        if len(snippet) < QualityScores.SHORT_SNIPPET_THRESHOLD:
            score += QualityScores.SHORT_SNIPPET_PENALTY
        
        return score
    
    def filter_and_rank_results(
        self,
        results: List[Dict[str, Any]],
        min_quality_score: float = None,
        prioritize_philosophy: bool = None
    ) -> List[Dict[str, Any]]:
        """Filter and rank results by quality"""
        min_quality_score = min_quality_score if min_quality_score is not None else settings.MIN_QUALITY_SCORE
        prioritize_philosophy = prioritize_philosophy if prioritize_philosophy is not None else settings.PRIORITIZE_PHILOSOPHY
        
        # Score all results
        scored_results = []
        for result in results:
            score = self.score_result_quality(result)
            if score >= min_quality_score:
                scored_results.append({
                    **result,
                    "_quality_score": score
                })
        
        # Sort by quality score (descending)
        scored_results.sort(key=lambda x: x["_quality_score"], reverse=True)
        
        # Prioritize philosophy domains if requested
        if prioritize_philosophy:
            philosophy_results = []
            other_results = []
            
            for result in scored_results:
                url = result.get("url", "").lower()
                is_philosophy = any(domain in url for domain in self.philosophy_domains)
                
                if is_philosophy:
                    philosophy_results.append(result)
                else:
                    other_results.append(result)
            
            # Return philosophy results first, then others
            return philosophy_results + other_results
        
        return scored_results
    
    def get_philosophy_specific_sources(self, query: str) -> List[Dict[str, Any]]:
        """Get direct links to philosophy-specific sources"""
        encoded_query = quote_plus(query)
        
        sources = [
            {
                "title": f"Stanford Encyclopedia of Philosophy: {query}",
                "url": APIEndpoints.STANFORD_ENCYCLOPEDIA_SEARCH.format(query=encoded_query),
                "snippet": "High-quality philosophy encyclopedia articles",
                "source": "stanford_encyclopedia",
                "_quality_score": QualityScores.STANFORD_ENCYCLOPEDIA_SCORE
            },
            {
                "title": f"Internet Encyclopedia of Philosophy: {query}",
                "url": APIEndpoints.IEP_SEARCH.format(query=encoded_query),
                "snippet": "Comprehensive philosophy encyclopedia",
                "source": "iep",
                "_quality_score": QualityScores.IEP_SCORE
            },
            {
                "title": f"PhilPapers: {query}",
                "url": APIEndpoints.PHILPAPERS_SEARCH.format(query=encoded_query),
                "snippet": "Academic philosophy papers and articles",
                "source": "philpapers",
                "_quality_score": QualityScores.PHILPAPERS_SCORE
            }
        ]
        
        return sources
    
    def is_philosophy_relevant(self, result: Dict[str, Any]) -> bool:
        """Check if result is relevant to philosophy"""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Check if from philosophy domain
        if any(domain in url for domain in self.philosophy_domains):
            return True
        
        # Check for philosophy keywords
        text = f"{title} {snippet}"
        return any(indicator in text for indicator in self.philosophy_indicators)
