# RAG Output Quality Improvements

Based on your current implementation, here are systematic ways to improve response quality and formatting for philosophy RAG.

---

## **1. PROMPT ENGINEERING FOR BETTER OUTPUTS**

### Current Issue
Your prompt is generic:
```python
prompt_text = f"""You are a helpful assistant that answers questions about philosophy...
Question: {question}
Provide a comprehensive answer...
Answer:"""
```

### Problem
- Generic structure doesn't leverage philosophy domain
- No guidance on how to structure answers
- Missing critical thinking directives

### Solution: Philosophy-Specific Prompt Template

```python
PHILOSOPHY_PROMPT_TEMPLATE = """You are an expert philosophy assistant with deep knowledge of philosophers, 
concepts, and arguments throughout philosophical history.

TASK: Answer the following question thoroughly and accurately.

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
   - Use bullet points for supporting ideas
5. **Cite Sources**: Reference which texts or philosophers you're drawing from
6. **Critical Analysis**: Don't just describe - analyze and evaluate

RESPONSE FORMAT (REQUIRED):
## Main Concept
[Definition and overview]

## Historical Development
[How this idea evolved, key philosophers]

## Key Arguments
1. [First argument]
2. [Second argument]
3. [Third argument]

## Counterarguments
- [Common objections]
- [Alternative views]

## Contemporary Relevance
[How this applies today]

## Conclusion
[Summary and synthesis]

Now provide your comprehensive answer:"""

# Usage:
prompt = PHILOSOPHY_PROMPT_TEMPLATE.format(
    question=question,
    context=combined_context
)
```

---

## **2. OUTPUT POST-PROCESSING & REFINEMENT**

### Current Issue
Raw LLM output goes directly to frontend with no refinement.

### Solution: Output Processor Pipeline

```python
class OutputProcessor:
    """Post-process LLM outputs for quality and consistency"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def process_response(
        self,
        raw_response: str,
        question: str,
        context: str,
        is_philosophy: bool = True
    ) -> Dict[str, Any]:
        """Process and enhance raw LLM output"""
        
        # 1. Validate response quality
        quality_score = self._evaluate_response_quality(
            raw_response, question
        )
        
        # 2. Ensure markdown formatting
        formatted_response = self._ensure_markdown_format(
            raw_response, is_philosophy=is_philosophy
        )
        
        # 3. Add section metadata
        sections = self._extract_sections(formatted_response)
        
        # 4. Extract key concepts
        key_concepts = self._extract_key_concepts(
            formatted_response, question
        )
        
        # 5. Validate citations/sources
        citations = self._extract_citations(formatted_response)
        
        # 6. If quality low, attempt improvement
        if quality_score < 0.6:
            formatted_response = await self._improve_response(
                raw_response, question, context
            )
            quality_score = self._evaluate_response_quality(
                formatted_response, question
            )
        
        return {
            "response": formatted_response,
            "quality_score": quality_score,
            "sections": sections,
            "key_concepts": key_concepts,
            "citations": citations,
            "is_improved": quality_score >= 0.6
        }
    
    def _evaluate_response_quality(self, response: str, question: str) -> float:
        """Score response quality 0.0-1.0"""
        score = 0.0
        
        # Length (too short = bad)
        word_count = len(response.split())
        if word_count < 50:
            score += 0.1
        elif word_count < 150:
            score += 0.5
        elif word_count < 500:
            score += 0.8
        else:
            score += 1.0
        
        # Structure
        has_headers = "##" in response or "#" in response
        has_lists = "-" in response or "1." in response
        has_quotes = ">" in response or '"' in response
        has_bold = "**" in response
        
        structure_score = sum([has_headers, has_lists, has_quotes, has_bold]) / 4
        score = (score * 0.4) + (structure_score * 0.6)
        
        # Relevance (simple check)
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        overlap = len(question_words & response_words) / len(question_words)
        score = (score * 0.7) + (overlap * 0.3)
        
        return min(score, 1.0)
    
    def _ensure_markdown_format(self, text: str, is_philosophy: bool = True) -> str:
        """Ensure response uses proper markdown formatting"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Convert headers
            if line.startswith('**') and line.endswith('**'):
                # Already bold, make it header
                content = line.replace('**', '')
                formatted_lines.append(f"## {content.strip()}")
            elif re.match(r'^[A-Z][a-zA-Z\s]+:$', line):
                # "Key Points:" style → markdown header
                formatted_lines.append(f"## {line[:-1]}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _extract_sections(self, response: str) -> List[Dict[str, str]]:
        """Extract markdown sections"""
        sections = []
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('##'):
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip()
                    })
                current_section = line.replace('##', '').strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip()
            })
        
        return sections
    
    def _extract_key_concepts(self, response: str, question: str) -> List[str]:
        """Extract philosophy concepts mentioned"""
        concepts = []
        
        # Look for bolded terms
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', response)
        concepts.extend(bold_matches)
        
        # Look for quoted concepts
        quote_matches = re.findall(r'[„""]([^„""]+)[„""]', response)
        concepts.extend(quote_matches)
        
        # Remove duplicates, limit to 10
        return list(set(concepts))[:10]
    
    def _extract_citations(self, response: str) -> List[str]:
        """Extract philosopher names and source citations"""
        citations = []
        
        # Common philosopher names (from constants)
        from backend.constants import COMMON_PHILOSOPHERS
        
        text = response.lower()
        for philosopher in COMMON_PHILOSOPHERS:
            if philosopher.lower() in text:
                citations.append(philosopher)
        
        return list(set(citations))
    
    async def _improve_response(
        self,
        poor_response: str,
        question: str,
        context: str
    ) -> str:
        """Use LLM to improve low-quality response"""
        improvement_prompt = f"""The following response to a philosophy question is too brief or poorly structured.
Please rewrite it to be more comprehensive, better organized, and properly formatted with markdown.

ORIGINAL RESPONSE:
{poor_response}

ORIGINAL QUESTION:
{question}

AVAILABLE CONTEXT:
{context}

REQUIREMENTS:
1. Use markdown headers (##) for sections
2. Include at least 3-4 major sections
3. Use **bold** for key concepts
4. Explain philosopher names and their contributions
5. Be comprehensive (300+ words minimum)
6. Maintain accuracy to original response

IMPROVED RESPONSE:"""
        
        improved = await self.llm_service.ainvoke(improvement_prompt)
        return improved
```

---

## **3. STRUCTURED OUTPUT WITH METADATA**

### Current Issue
Response is just a string; no metadata about its structure/quality.

### Solution: Enhanced Response Structure

```python
class EnhancedRAGResponse:
    """Structured response with metadata"""
    
    async def generate(
        self,
        question: str,
        combined_context: str,
        chat_history: List[Tuple[str, str]] = None,
        rag_service: RAGService = None
    ) -> Dict[str, Any]:
        """Generate comprehensive structured response"""
        
        # 1. Generate base response
        raw_response = await self.llm_service.ainvoke(
            self._build_philosophy_prompt(question, combined_context, chat_history)
        )
        
        # 2. Process output
        processor = OutputProcessor(self.llm_service)
        processed = await processor.process_response(
            raw_response, question, combined_context
        )
        
        # 3. Extract entities for graph
        entities = self._extract_entities(processed["response"])
        
        # 4. Build final response
        return {
            "answer": processed["response"],  # Main markdown response
            "metadata": {
                "quality_score": processed["quality_score"],
                "sections": processed["sections"],
                "key_concepts": processed["key_concepts"],
                "citations": processed["citations"],
                "was_improved": processed["is_improved"]
            },
            "entities": entities,
            "structure": {
                "has_headers": any(s["title"] for s in processed["sections"]),
                "section_count": len(processed["sections"]),
                "key_concept_count": len(processed["key_concepts"])
            }
        }
```

---

## **4. RESPONSE VALIDATION**

### Check if response actually answers the question

```python
async def validate_response(
    self,
    response: str,
    question: str,
    llm_service: LLMService
) -> Dict[str, Any]:
    """Validate response quality and relevance"""
    
    validation_prompt = f"""Given a question and a response, evaluate:
1. Does the response actually answer the question? (yes/no)
2. Is the response accurate and helpful? (1-5 scale)
3. Is it well-structured and professional? (1-5 scale)
4. What's missing or could be improved? (brief list)

QUESTION: {question}

RESPONSE: {response}

Please evaluate in JSON format:
{{
    "answers_question": true/false,
    "accuracy_score": 1-5,
    "structure_score": 1-5,
    "missing_elements": ["element1", "element2"],
    "overall_assessment": "brief summary"
}}"""
    
    validation_result = await llm_service.ainvoke(validation_prompt)
    
    # Parse JSON response
    import json
    try:
        data = json.loads(validation_result)
        return {
            "is_valid": data["answers_question"],
            "scores": {
                "accuracy": data["accuracy_score"],
                "structure": data["structure_score"]
            },
            "improvements_needed": data["missing_elements"]
        }
    except:
        return {"is_valid": True, "scores": {}, "improvements_needed": []}
```

---

## **5. TEMPERATURE & SAMPLING OPTIMIZATION**

### Current Issue
Fixed `temperature=0` (deterministic but boring)

### Solution: Temperature Based on Task

```python
class AdaptiveTemperature:
    """Adjust temperature based on query type"""
    
    @staticmethod
    def get_temperature(question: str) -> float:
        """
        - Factual questions (e.g., "What is...?") → low temp (0.0-0.3)
        - Analytical questions (e.g., "Discuss...") → medium temp (0.5-0.7)
        - Creative/exploratory → high temp (0.7-1.0)
        """
        question_lower = question.lower()
        
        # Factual indicators
        if any(q in question_lower for q in ["what is", "define", "explain", "describe"]):
            return 0.2
        
        # Analytical
        elif any(q in question_lower for q in ["compare", "contrast", "discuss", "analyze"]):
            return 0.6
        
        # Creative
        elif any(q in question_lower for q in ["imagine", "propose", "create", "invent"]):
            return 0.8
        
        # Default
        return 0.5

# Usage in LLM:
temperature = AdaptiveTemperature.get_temperature(question)
self.llm.temperature = temperature
```

---

## **6. STREAMING RESPONSES (For Better UX)**

### Current Issue
Wait for entire response before showing to user.

### Solution: Stream Response to Frontend

```python
async def stream_response(
    self,
    question: str,
    combined_context: str,
    chat_history: List = None
) -> AsyncGenerator[str, None]:
    """Stream response chunks to frontend"""
    
    prompt = self._build_philosophy_prompt(
        question, combined_context, chat_history
    )
    
    # Stream from LLM
    async for chunk in self.llm_service.astream(prompt):
        if hasattr(chunk, 'content'):
            yield chunk.content
        else:
            yield str(chunk)

# In FastAPI router:
from fastapi.responses import StreamingResponse

@router.post("/query/stream")
async def stream_query(request: RAGQueryRequest):
    """Stream response for better UX"""
    rag_service = get_rag_service(request.llm_provider, request.model)
    
    async def response_generator():
        async for chunk in rag_service.stream_response(
            question=request.question,
            combined_context=await rag_service._get_combined_context(request),
            chat_history=request.chat_history
        ):
            yield chunk
    
    return StreamingResponse(response_generator(), media_type="text/plain")
```

---

## **7. CONFIDENCE SCORING**

### Help user understand response reliability

```python
class ConfidenceScorer:
    """Assess confidence in response"""
    
    @staticmethod
    def score(
        response: str,
        context_quality: float,  # 0-1
        sources_count: int,
        has_citations: bool,
        topic_coverage: float    # 0-1
    ) -> Dict[str, Any]:
        """
        Calculate confidence based on multiple factors
        """
        
        factors = {
            "context_quality": context_quality * 0.3,
            "source_count": min(sources_count / 5, 1.0) * 0.2,
            "citations": 0.2 if has_citations else 0.0,
            "coverage": topic_coverage * 0.3
        }
        
        overall = sum(factors.values())
        
        # Categorize
        if overall >= 0.8:
            confidence = "High"
        elif overall >= 0.6:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        return {
            "score": round(overall, 2),
            "level": confidence,
            "factors": factors,
            "warning": "Limited sources" if sources_count < 2 else None
        }
```

---

## **Implementation Priority**

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 🔴 | Philosophy Prompt Template | Low | Very High |
| 🔴 | Output Post-Processing | Medium | High |
| 🟡 | Structured Response Metadata | Medium | Medium |
| 🟡 | Confidence Scoring | Low | Medium |
| 🟢 | Response Validation | Medium | Medium |
| 🟢 | Streaming Responses | Medium | High (UX) |
| 🟢 | Adaptive Temperature | Low | Low |

---

## **Quick Implementation: Start Here**

```python
# 1. Update rag_service.py - Replace _generate_response:

PHILOSOPHY_PROMPT = """You are an expert philosophy assistant.

Question: {question}

Context: {context}

Provide your answer using this structure:
## Main Concept
[Define key terms]

## Historical Background  
[Philosophers and development]

## Key Arguments
[List main points]

## Critical Analysis
[Evaluate ideas]

## Conclusion
[Summary]

Use **bold** for concepts, > for quotes."""

async def _generate_response(self, question, context, chat_history=None):
    prompt = PHILOSOPHY_PROMPT.format(
        question=question,
        context=context
    )
    return await self.llm_service.ainvoke(prompt)
```

This alone will dramatically improve output quality without additional complexity.

