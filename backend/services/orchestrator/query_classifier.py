import os
from typing import Optional
from backend.models.orchestration_models import (
    QueryClassification, QueryType, FocusMode
)
from backend.services.llm_service import OllamaLLMService

class QueryClassifierService:
    """Classifies queries into types"""
    
    def __init__(self, llm_service: OllamaLLMService):
        self.llm = llm_service
    
    async def classify_query(self, query: str) -> QueryClassification:
        """Classify query and return configuration"""
        
        prompt = f"""
Classify this query into exactly ONE category:

Query: "{query}"

CATEGORIES:
1. FACTUAL - Questions about facts, dates, definitions
   Examples: "What is X?", "When did Y happen?", "How many Z?"
   
2. ANALYTICAL - Questions requiring analysis, comparison, reasoning
   Examples: "How does X work?", "Why did Y happen?", "Compare X and Y"
   
3. CREATIVE - Questions requiring generation, brainstorming
   Examples: "Generate an idea for...", "Write a poem about...", "Design..."
   
4. META - Questions about system, capabilities, or instructions
   Examples: "Can you do X?", "How do you work?", "What can you help with?"

Also determine:
- Does this need current/real-time information? (true/false)
- Can we answer well with local knowledge only? (0-100%)
- What focus mode is appropriate? (speed | balanced | quality)

RESPOND IN THIS EXACT FORMAT:
CATEGORY: [factual|analytical|creative|meta]
REQUIRES_WEB: [true|false]
LOCAL_CONFIDENCE: [0-100]
FOCUS_MODE: [speed|balanced|quality]
TEMPERATURE: [0.2|0.5|0.8]
REASONING_DEPTH: [1|2|3]

Query classification:
"""
        
        response = await self.llm.generate(
            prompt,
            temperature=0.3,  # Low temp for consistent classification
            max_tokens=100
        )
        
        return self._parse_classification(response, query)
    
    def _parse_classification(self, response: str, query: str) -> QueryClassification:
        """Parse LLM response into QueryClassification"""
        
        lines = response.strip().split('\n')
        data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip().lower()
        
        # Map to enums
        query_type_map = {
            'factual': QueryType.FACTUAL,
            'analytical': QueryType.ANALYTICAL,
            'creative': QueryType.CREATIVE,
            'meta': QueryType.META
        }
        
        focus_mode_map = {
            'speed': FocusMode.SPEED,
            'balanced': FocusMode.BALANCED,
            'quality': FocusMode.QUALITY
        }
        
        return QueryClassification(
            query_type=query_type_map.get(
                data.get('category', 'analytical'),
                QueryType.ANALYTICAL
            ),
            requires_web=data.get('requires_web', 'true').lower() == 'true',
            local_knowledge_confidence=int(data.get('local_confidence', '50')) / 100.0,
            temperature=float(data.get('temperature', '0.5')),
            focus_mode=focus_mode_map.get(
                data.get('focus_mode', 'balanced'),
                FocusMode.BALANCED
            ),
            reasoning_depth=int(data.get('reasoning_depth', '2'))
        )
