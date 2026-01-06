from typing import List, Dict, Any, Optional, Tuple
from langchain_neo4j import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from backend.services.kg_service import KnowledgeGraphService
from backend.services.web_crawler_service import WebCrawlerService
from backend.services.image_service import ImageService
from backend.services.llm_service import LLMService
from backend.services.output_processor import OutputProcessor
from backend.services.confidence_scorer import ConfidenceScorer
from backend.constants import PromptTemplates
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        web_crawler: WebCrawlerService,
        image_service: ImageService,
        llm_service: LLMService,
        output_processor: Optional[OutputProcessor] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None
    ):
        self.kg_service = kg_service
        self.web_crawler = web_crawler
        self.image_service = image_service
        self.llm_service = llm_service
        
        # Inject services or create defaults
        self.output_processor = output_processor or OutputProcessor(llm_service)
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        
        self.vector_index = None
        self._initialize_vector_index()
    
    def _initialize_vector_index(self):
        """Initialize vector index for hybrid search"""
        try:
            if settings.OPENAI_API_KEY:
                embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
                self.vector_index = Neo4jVector.from_existing_graph(
                    embeddings,
                    search_type="hybrid",
                    node_label="Document",
                    text_node_properties=["text"],
                    embedding_node_property="embedding",
                )
        except Exception as e:
            logger.warning(f"Could not initialize vector index: {str(e)}")
    
    async def query(
        self,
        question: str,
        chat_history: List[Tuple[str, str]] = None,
        include_web: bool = True,
        include_images: bool = True,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Main RAG query function with improved output processing"""
        errors = {}
        contexts = {}
        
        try:
            # 1. Get context from knowledge graph
            try:
                contexts["kg"] = self._get_kg_context(question, sources=sources)
            except Exception as e:
                logger.error(f"KG retrieval failed: {e}")
                errors["kg_retrieval"] = str(e)
            
            # 2. Get web context if enabled
            if include_web:
                try:
                    contexts["web"] = await self.web_crawler.search_and_summarize(
                        question,
                        self.llm_service,
                        num_results=settings.MAX_SEARCH_RESULTS,
                        prioritize_philosophy=True
                    )
                except Exception as e:
                    logger.warning(f"Web search failed: {e}")
                    errors["web_search"] = str(e)
            
            # 3. Get images if enabled
            images = []
            if include_images:
                try:
                    images = await self.image_service.search_images(question, num_results=3)
                except Exception as e:
                    logger.warning(f"Image search failed: {e}")
            
            # 4. Combine contexts with size limits
            combined_context = self._combine_contexts(
                contexts.get("kg", {}),
                contexts.get("web", {}),
                max_tokens=settings.MAX_CONTEXT_TOKENS
            )
            
            # 5. Generate response with improved prompt
            raw_response = await self._generate_response(
                question, combined_context, chat_history
            )
            
            # 6. Post-process response for quality
            processed = await self.output_processor.process_response(
                raw_response, question, combined_context
            )
            
            # 7. Calculate confidence score
            context_quality = self._estimate_context_quality(contexts)
            sources_used = (len(contexts.get("kg", {}).get("entities", [])) + 
                          len(contexts.get("web", {}).get("sources", [])))
            
            confidence = self.confidence_scorer.score(
                processed["response"],
                context_quality=context_quality,
                sources_count=sources_used,
                has_citations=len(processed["citations"]) > 0,
                topic_coverage=self._estimate_topic_coverage(
                    question, processed["response"]
                ),
                is_improved=processed["was_improved"]
            )
            
            # 8. Get graph visualization
            graph_data = self.kg_service.get_graph_for_visualization(question)
            
            return {
                "answer": processed["response"],
                "confidence": confidence,
                "sources": {
                    "knowledge_graph": contexts.get("kg", {}).get("entities", []),
                    "web": contexts.get("web", {}).get("sources", [])
                },
                "images": images,
                "graph": graph_data,
                "metadata": {
                    "processing": processed["metadata"],
                    "sections": processed["sections"],
                    "key_concepts": processed["key_concepts"],
                    "citations": processed["citations"],
                    "quality_score": processed["quality_score"]
                },
                "retrieval_methods_used": {
                    "graph": bool(contexts.get("kg")),
                    "web": bool(contexts.get("web")),
                    "vector_search": self.vector_index is not None
                },
                "errors": errors if errors else None
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": {},
                "images": [],
                "graph": {"nodes": [], "edges": []},
                "confidence": self.confidence_scorer.score(
                    "", context_quality=0.0, sources_count=0
                ),
                "error": str(e)
            }
    
    def _get_kg_context(
        self,
        question: str,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get context from knowledge graph, optionally filtered by sources"""
        try:
            # Get related entities
            entities = self.kg_service._extract_entities_from_query(question)
            
            context_parts = []
            all_entities = []
            
            for entity in entities:
                related = self.kg_service.get_related_entities(
                    entity,
                    limit=5,
                    sources=sources
                )
                for rel in related:
                    context_parts.append(
                        f"{rel.get('entity')} -{rel.get('relationship')}-> {rel.get('related_entity')}"
                    )
                    all_entities.append(rel.get('entity'))
                    all_entities.append(rel.get('related_entity'))
            
            # Also try vector search if available
            if self.vector_index:
                try:
                    vector_results = self.vector_index.similarity_search(
                        question,
                        k=settings.TOP_K_RESULTS
                    )
                    for doc in vector_results:
                        # Filter by sources if specified
                        if not sources or doc.metadata.get('source') in sources:
                            context_parts.append(doc.page_content[:200])
                except Exception as e:
                    logger.warning(f"Vector search error: {str(e)}")
            
            return {
                "text": "\n".join(context_parts),
                "entities": list(set(all_entities)),
                "sources_used": sources or []
            }
        except Exception as e:
            logger.error(f"Error getting KG context: {str(e)}")
            return {"text": "", "entities": [], "sources_used": []}
    
    def _combine_contexts(
        self,
        kg_context: Dict[str, Any],
        web_context: Dict[str, Any],
        max_tokens: int = 2000
    ) -> str:
        """Combine knowledge graph and web contexts with token limits"""
        parts = []
        current_length = 0
        max_chars = max_tokens * 4  # Rough approximation
        
        # Add KG context first (usually most relevant for philosophy)
        if kg_context.get("text"):
            kg_text = kg_context["text"]
            # Truncate if needed
            if current_length + len(kg_text) > max_chars:
                kg_text = kg_text[:max(100, max_chars - current_length)]
            parts.append("REFERENCE TEXT CONTEXT:")
            parts.append(kg_text)
            current_length += len(kg_text)
        
        # Add web context if room available
        if web_context.get("summary") and current_length < max_chars:
            web_text = web_context["summary"]
            remaining = max_chars - current_length
            if len(web_text) > remaining:
                web_text = web_text[:max(100, remaining)]
            parts.append("\nWEB SOURCES CONTEXT:")
            parts.append(web_text)
        
        return "\n".join(parts)
    
    async def _generate_response(
        self,
        question: str,
        context: str,
        chat_history: List[Tuple[str, str]] = None
    ) -> str:
        """Generate response using LLM with philosophy-specific prompt"""
        try:
            # Determine question type to select appropriate prompt
            question_type = self._classify_question(question)
            
            # Select prompt template based on question type
            if question_type == "factual":
                prompt_template = PromptTemplates.PHILOSOPHY_RESPONSE_STRUCTURE
            else:
                prompt_template = PromptTemplates.PHILOSOPHY_RESPONSE_STRUCTURE
            
            # Build prompt
            prompt_text = prompt_template.format(
                question=question,
                context=context
            )
            
            # Include chat history if provided (respecting token limit)
            if chat_history:
                history_context = self._prepare_chat_history(chat_history)
                if history_context:
                    prompt_text = f"Previous conversation context:\n{history_context}\n\n{prompt_text}"
            
            # Generate response with adaptive temperature
            # (temperature handling will be in LLMService)
            response = await self.llm_service.ainvoke(prompt_text)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _classify_question(self, question: str) -> str:
        """Classify question type for prompt selection"""
        question_lower = question.lower()
        
        # Factual indicators
        if any(q in question_lower for q in ["what is", "define", "explain", "describe", "who is"]):
            return "factual"
        # Analytical indicators
        elif any(q in question_lower for q in ["compare", "contrast", "discuss", "analyze", "evaluate"]):
            return "analytical"
        # Creative/exploratory indicators
        elif any(q in question_lower for q in ["imagine", "propose", "create", "invent", "could"]):
            return "creative"
        
        return "analytical"  # Default
    
    def _prepare_chat_history(
        self,
        chat_history: List[Tuple[str, str]],
        max_tokens: int = None
    ) -> str:
        """Prepare chat history respecting token limits"""
        if not chat_history:
            return ""
        
        max_tokens = max_tokens or settings.MAX_CHAT_HISTORY_TOKENS
        current_tokens = 0
        relevant_history = []
        
        # Work backwards from most recent
        for h, a in reversed(chat_history):
            # Rough token count (words / 1.3)
            h_tokens = len(h.split()) // 2
            a_tokens = len(a.split()) // 2
            total_tokens = h_tokens + a_tokens
            
            if current_tokens + total_tokens > max_tokens:
                break
            
            relevant_history.insert(0, (h, a))
            current_tokens += total_tokens
        
        # Format history
        return "\n".join(
            f"Human: {h}\nAssistant: {a}" for h, a in relevant_history
        )
    
    def _estimate_context_quality(self, contexts: Dict[str, Any]) -> float:
        """Estimate quality of retrieved context"""
        quality = 0.5  # Default baseline
        
        # Improve based on KG context
        if contexts.get("kg", {}).get("text"):
            quality += 0.2
        
        # Improve based on web context
        if contexts.get("web", {}).get("summary"):
            quality += 0.2
        
        # Improve based on entity count
        entity_count = len(contexts.get("kg", {}).get("entities", []))
        if entity_count >= 5:
            quality += 0.1
        
        return min(quality, 1.0)
    
    def _estimate_topic_coverage(self, question: str, response: str) -> float:
        """Estimate how well response covers the question topic"""
        question_words = set(w.lower() for w in question.split() if len(w) > 3)
        response_words = set(w.lower() for w in response.split() if len(w) > 3)
        
        if not question_words:
            return 0.5
        
        overlap = len(question_words & response_words) / len(question_words)
        return overlap
