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
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        web_crawler: WebCrawlerService,
        image_service: ImageService,
        llm_service: LLMService
    ):
        self.kg_service = kg_service
        self.web_crawler = web_crawler
        self.image_service = image_service
        self.llm_service = llm_service
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
        """Main RAG query function"""
        try:
            # 1. Get context from knowledge graph (optionally filtered by sources)
            kg_context = self._get_kg_context(question, sources=sources)
            
            # 2. Get web context if enabled (with philosophy-specific enhancement)
            web_context = {}
            if include_web:
                web_context = await self.web_crawler.search_and_summarize(
                    question,
                    self.llm_service,
                    num_results=settings.MAX_SEARCH_RESULTS,
                    prioritize_philosophy=True  # Always prioritize philosophy for RAG queries
                )
            
            # 3. Get images if enabled
            images = []
            if include_images:
                images = await self.image_service.search_images(question, num_results=3)
            
            # 4. Combine contexts
            combined_context = self._combine_contexts(kg_context, web_context)
            
            # 5. Generate response using LLM
            response = await self._generate_response(question, combined_context, chat_history)
            
            # 6. Get graph visualization data
            graph_data = self.kg_service.get_graph_for_visualization(question)
            
            return {
                "answer": response,
                "sources": {
                    "knowledge_graph": kg_context.get("entities", []),
                    "web": web_context.get("sources", [])
                },
                "images": images,
                "graph": graph_data,
                "context_used": {
                    "kg": bool(kg_context),
                    "web": bool(web_context)
                }
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": {},
                "images": [],
                "graph": {"nodes": [], "edges": []},
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
        web_context: Dict[str, Any]
    ) -> str:
        """Combine knowledge graph and web contexts"""
        parts = []
        
        if kg_context.get("text"):
            parts.append("Reference Text Context:")
            parts.append(kg_context["text"])
        
        if web_context.get("summary"):
            parts.append("\nLatest Information from Web:")
            parts.append(web_context["summary"])
        
        return "\n".join(parts)
    
    async def _generate_response(
        self,
        question: str,
        context: str,
        chat_history: List[Tuple[str, str]] = None
    ) -> str:
        """Generate response using LLM"""
        try:
            # Build prompt
            if context:
                prompt_text = f"""You are a helpful assistant that answers questions about philosophy and related topics.

Context from reference materials and web:
{context}

Question: {question}

Provide a comprehensive answer that:
1. References the relevant philosophers or concepts mentioned
2. Summarizes information from both reference text and latest web sources
3. Is clear and well-structured

Answer:"""
            else:
                prompt_text = f"""Answer the following question about philosophy:

Question: {question}

Answer:"""
            
            # Include chat history if provided
            if chat_history:
                history_text = "\n".join([
                    f"Human: {h}\nAssistant: {a}"
                    for h, a in chat_history[-3:]  # Last 3 exchanges
                ])
                prompt_text = f"Previous conversation:\n{history_text}\n\n{prompt_text}"
            
            response = await self.llm_service.ainvoke(prompt_text)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"
