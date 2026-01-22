from typing import List
import json
from backend.models.orchestration_models import (
    CoTResult, CoTStep, QueryClassification, QueryType
)
from backend.services.core.llm_service import OllamaLLMService

class CoTGeneratorService:
    """Generates Chain-of-Thought reasoning steps with dynamic strategies"""
    
    def __init__(self, llm_service: OllamaLLMService):
        self.llm = llm_service
    
    async def generate_cot(
        self, 
        query: str, 
        query_class: QueryClassification
    ) -> CoTResult:
        """Generate step-by-step reasoning"""
        
        strategy = self._get_strategy(query_class.query_type)
        
        prompt = f"""
Let's analyze this query step-by-step using a {query_class.query_type.value} strategy.

Query: "{query}"
Query Type: {query_class.query_type.value}
Reasoning Depth: {query_class.reasoning_depth}
Strategy: {strategy}

TASK: Break down the query into logical reasoning steps.

RESPOND IN THIS EXACT FORMAT:

STEP 1: [First reasoning step - Core Question Analysis]
STEP 2: [Second reasoning step - Information Retrieval Needs]
STEP 3: [Third reasoning step - Synthesis or Deduction]
{"STEP 4: [Fourth reasoning step - Compare/contrast or Detailed Analysis]" if query_class.reasoning_depth > 1 else ""}
{"STEP 5: [Fifth reasoning step - Creative/Meta Analysis]" if query_class.reasoning_depth > 2 else ""}
STEP VALUES: VALIDATION - [Critique: Does this plan fully address the prompt?]

KEY_QUESTIONS:
- [Specific question to answer STEP 1]
- [Specific question to answer STEP 2]
- [Specific question to answer STEP 3]

SEARCH_TERMS:
- [Precise search term 1]
- [Precise search term 2]
- [Broader search term 3]

LOGIC_QUALITY: [0-100]

Let's reason through this:
"""
        
        response = await self.llm.generate(
            prompt,
            temperature=0.4,  # Consistent reasoning
            max_tokens=800
        )
        
        return self._parse_cot_response(response)
    
    def _get_strategy(self, query_type: QueryType) -> str:
        if query_type == QueryType.FACTUAL:
            return "Focus on fact verification, entity application, and chronological accuracy."
        elif query_type == QueryType.ANALYTICAL:
            return "Focus on multiple perspectives, cause-and-effect relationships, and comparative analysis."
        elif query_type == QueryType.CREATIVE:
            return "Focus on brainstorming, pattern recognition, and novel combinations of ideas."
        else:
            return "Focus on understanding system capabilities and user intent."

    def _parse_cot_response(self, response: str) -> CoTResult:
        """Parse CoT response into structured format"""
        
        steps = []
        key_questions = []
        search_terms = []
        logic_quality = 0.7
        
        lines = response.strip().split('\n')
        current_section = None
        step_count = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('STEP'):
                # Handle STEP VALUES: VALIDATION case
                if 'VALIDATION' in line:
                     reasoning = line.split(':', 1)[1].strip() if ':' in line else line
                     steps.append(CoTStep(
                        step_number=99,
                        reasoning=f"VALIDATION: {reasoning}",
                        importance='critical'
                    ))
                else:
                    step_count += 1
                    reasoning = line.split(':', 1)[1].strip() if ':' in line else ''
                    steps.append(CoTStep(
                        step_number=step_count,
                        reasoning=reasoning,
                        importance='high' if step_count == 1 else 'medium'
                    ))
            
            elif line.startswith('KEY_QUESTIONS'):
                current_section = 'questions'
            
            elif line.startswith('SEARCH_TERMS'):
                current_section = 'search'
            
            elif line.startswith('LOGIC_QUALITY'):
                try:
                    logic_quality = int(line.split(':')[1].strip()) / 100.0
                except:
                    pass
            
            elif current_section == 'questions' and line.startswith('-'):
                key_questions.append(line.lstrip('-').strip())
            
            elif current_section == 'search' and line.startswith('-'):
                search_terms.append(line.lstrip('-').strip())
        
        return CoTResult(
            reasoning_steps=steps,
            key_questions=key_questions,
            search_terms=search_terms[:6],  
            overall_logic_quality=logic_quality
        )
