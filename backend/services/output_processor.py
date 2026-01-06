"""
Output processing service for RAG responses
Handles quality scoring, formatting, and improvements
"""
from typing import Dict, Any, List, Optional
import re
import logging
from backend.config import settings
from backend.constants import PromptTemplates, COMMON_PHILOSOPHERS
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class OutputProcessor:
    """Post-process LLM outputs for quality and consistency"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.min_quality = settings.OUTPUT_MIN_QUALITY_SCORE
        self.min_word_count = settings.OUTPUT_MIN_WORD_COUNT
        self.ideal_word_count = settings.OUTPUT_IDEAL_WORD_COUNT
        self.improve_threshold = settings.OUTPUT_QUALITY_THRESHOLD_IMPROVE
    
    async def process_response(
        self,
        raw_response: str,
        question: str,
        context: str,
        is_philosophy: bool = True
    ) -> Dict[str, Any]:
        """
        Process and enhance raw LLM output
        
        Args:
            raw_response: Raw text from LLM
            question: Original question
            context: Retrieved context
            is_philosophy: Whether to apply philosophy-specific processing
            
        Returns:
            Dict with processed response, quality score, sections, concepts
        """
        try:
            # 1. Evaluate initial quality
            quality_score = self._evaluate_response_quality(raw_response, question)
            
            # 2. Ensure markdown formatting
            formatted_response = self._ensure_markdown_format(raw_response)
            
            # 3. Extract sections
            sections = self._extract_sections(formatted_response)
            
            # 4. Extract key concepts
            key_concepts = self._extract_key_concepts(formatted_response)
            
            # 5. Extract citations
            citations = self._extract_citations(formatted_response)
            
            # 6. Improve if quality is below threshold
            was_improved = False
            if quality_score < self.improve_threshold:
                logger.info(f"Response quality low ({quality_score:.2f}), attempting improvement")
                formatted_response = await self._improve_response(
                    raw_response, question, context
                )
                quality_score = self._evaluate_response_quality(
                    formatted_response, question
                )
                was_improved = True
                # Re-extract components after improvement
                sections = self._extract_sections(formatted_response)
                key_concepts = self._extract_key_concepts(formatted_response)
                citations = self._extract_citations(formatted_response)
            
            return {
                "response": formatted_response,
                "quality_score": round(quality_score, 2),
                "sections": sections,
                "key_concepts": key_concepts,
                "citations": citations,
                "was_improved": was_improved,
                "metadata": {
                    "word_count": len(formatted_response.split()),
                    "section_count": len(sections),
                    "concept_count": len(key_concepts),
                    "citation_count": len(citations)
                }
            }
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            # Return raw response on error
            return {
                "response": raw_response,
                "quality_score": 0.5,
                "sections": [],
                "key_concepts": [],
                "citations": [],
                "was_improved": False,
                "error": str(e)
            }
    
    def _evaluate_response_quality(self, response: str, question: str) -> float:
        """
        Score response quality 0.0-1.0 based on multiple factors
        
        Args:
            response: The response text
            question: Original question for relevance check
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        
        # 1. Length evaluation (40% weight)
        word_count = len(response.split())
        if word_count < self.min_word_count:
            length_score = 0.2
        elif word_count < self.ideal_word_count[0]:
            length_score = 0.6
        elif word_count < self.ideal_word_count[1]:
            length_score = 0.9
        else:
            length_score = 1.0
        score += length_score * 0.4
        
        # 2. Structure evaluation (40% weight)
        structure_score = 0.0
        has_headers = bool(re.search(r'^#{1,4}\s', response, re.MULTILINE))
        has_lists = bool(re.search(r'^[-*]\s', response, re.MULTILINE))
        has_quotes = '"' in response or ">" in response
        has_bold = "**" in response
        
        structure_items = sum([has_headers, has_lists, has_quotes, has_bold])
        structure_score = structure_items / 4.0
        score += structure_score * 0.4
        
        # 3. Relevance to question (20% weight)
        question_words = set(w.lower() for w in question.split() if len(w) > 3)
        response_words = set(w.lower() for w in response.split() if len(w) > 3)
        
        if question_words:
            overlap = len(question_words & response_words) / len(question_words)
        else:
            overlap = 0.5
        
        score += overlap * 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def _ensure_markdown_format(self, text: str) -> str:
        """
        Ensure response uses proper markdown formatting
        
        Args:
            text: Raw response text
            
        Returns:
            Text with standardized markdown formatting
        """
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Convert all-caps with colon to headers
            if re.match(r'^[A-Z][A-Z\s]+:$', line):
                content = line[:-1].strip()
                formatted_lines.append(f"## {content}")
            # Convert bold-wrapped headers to markdown headers
            elif re.match(r'^\*\*[^*]+\*\*$', line):
                content = line.replace('**', '').strip()
                formatted_lines.append(f"## {content}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _extract_sections(self, response: str) -> List[Dict[str, str]]:
        """
        Extract markdown sections from response
        
        Args:
            response: Markdown-formatted response
            
        Returns:
            List of dicts with title and content
        """
        sections = []
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Detect section headers
            match = re.match(r'^#{1,4}\s+(.+)$', line)
            if match:
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip()
                    })
                current_section = match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Add final section
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip()
            })
        
        return sections
    
    def _extract_key_concepts(self, response: str) -> List[str]:
        """
        Extract bolded key concepts from response
        
        Args:
            response: The response text
            
        Returns:
            List of key concepts
        """
        concepts = []
        
        # Extract **bolded terms**
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', response)
        concepts.extend(bold_matches)
        
        # Extract "quoted concepts"
        quote_matches = re.findall(r'[„""]([^„""]+)[„""]', response)
        concepts.extend(quote_matches)
        
        # Remove duplicates and limit to 15
        unique_concepts = list(set(concepts))[:15]
        return unique_concepts
    
    def _extract_citations(self, response: str) -> List[str]:
        """
        Extract philosopher names and citations
        
        Args:
            response: The response text
            
        Returns:
            List of cited philosophers
        """
        citations = []
        text = response.lower()
        
        # Check for each common philosopher
        for philosopher in COMMON_PHILOSOPHERS:
            if philosopher.lower() in text:
                citations.append(philosopher)
        
        return list(set(citations))  # Remove duplicates
    
    async def _improve_response(
        self,
        poor_response: str,
        question: str,
        context: str
    ) -> str:
        """
        Use LLM to improve low-quality response
        
        Args:
            poor_response: Original low-quality response
            question: The question
            context: Retrieved context
            
        Returns:
            Improved response
        """
        try:
            prompt = PromptTemplates.IMPROVEMENT_PROMPT.format(
                response=poor_response,
                question=question,
                context=context
            )
            
            improved = await self.llm_service.ainvoke(prompt)
            return improved
        except Exception as e:
            logger.error(f"Error improving response: {e}")
            return poor_response  # Return original on failure
    
    def validate_response_completeness(
        self,
        response: str,
        min_sections: int = 3
    ) -> Dict[str, Any]:
        """
        Validate response has adequate structure
        
        Args:
            response: The response text
            min_sections: Minimum expected sections
            
        Returns:
            Validation result dict
        """
        sections = self._extract_sections(response)
        concepts = self._extract_key_concepts(response)
        citations = self._extract_citations(response)
        
        is_valid = (
            len(sections) >= min_sections and
            len(concepts) >= 3 and
            len(response.split()) >= self.min_word_count
        )
        
        return {
            "is_valid": is_valid,
            "section_count": len(sections),
            "concept_count": len(concepts),
            "citation_count": len(citations),
            "word_count": len(response.split()),
            "issues": {
                "too_few_sections": len(sections) < min_sections,
                "too_few_concepts": len(concepts) < 3,
                "too_short": len(response.split()) < self.min_word_count
            }
        }
