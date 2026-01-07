"""
Conversation Memory Service using LangChain's ConversationKGMemory.

This implementation:
1. Extracts philosophers, concepts, arguments from conversation
2. Stores them in your existing Neo4j knowledge graph
3. Maintains conversation context within token limits
4. Enables cross-session entity retrieval

Benefits for Philosophy RAG:
- Automatically recognizes Kant, Aristotle, etc.
- Builds relationships: "User asked about virtue ethics"
- Links to main philosophy KG: "Aristotle" → existing philosophy node
- Improves context retrieval with conversation entities
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from langchain_community.memory.kg import ConversationKGMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from backend.config import settings

logger = logging.getLogger(__name__)

# Memory management constants
MAX_ACTIVE_EXCHANGES = 20  # Keep only last 20 exchanges in active memory
MAX_SESSION_SIZE_MB = 50  # Archive if session grows beyond 50MB
ARCHIVE_THRESHOLD = 30  # Archive when >30 exchanges
IMPORTANT_ENTITIES_THRESHOLD = 3  # Entity mentioned 3+ times = important
SESSION_TTL_DAYS = 30  # Auto-archive sessions older than 30 days


class ConversationMemoryService:
    """Manage conversation memory with automatic entity extraction"""
    
    def __init__(
        self,
        llm: BaseLanguageModel,
        neo4j_graph: Neo4jGraph,
        session_id: Optional[str] = None,
        max_history: int = 15,
        enable_archival: bool = True,
        enable_importance_scoring: bool = True
    ):
        """
        Initialize conversation memory service with smart memory management
        
        Args:
            llm: Language model for entity extraction
            neo4j_graph: Neo4j graph instance (existing philosophy KG)
            session_id: Unique conversation session identifier
            max_history: Maximum exchanges to keep in active memory
            enable_archival: Enable automatic archival of old exchanges
            enable_importance_scoring: Track entity importance/frequency
        """
        self.session_id = session_id or self._generate_session_id()
        self.neo4j_graph = neo4j_graph
        self.max_history = max_history
        self.enable_archival = enable_archival
        self.enable_importance_scoring = enable_importance_scoring
        
        # Create a Networkx-backed graph that also persists to Neo4j
        class Neo4jBackedNetworkxGraph(NetworkxEntityGraph):
            def __init__(self, neo4j_graph: Neo4jGraph, session_id: Optional[str] = None):
                super().__init__()
                self.neo4j_graph = neo4j_graph
                self.session_id = session_id

            def add_triple(self, knowledge_triple):
                # Add to in-memory networkx graph
                try:
                    super().add_triple(knowledge_triple)
                except Exception:
                    pass

                # Persist to Neo4j (use generic relationship type, store predicate as property)
                try:
                    subj = getattr(knowledge_triple, 'subject', None)
                    pred = getattr(knowledge_triple, 'predicate', None)
                    obj = getattr(knowledge_triple, 'object_', None) or getattr(knowledge_triple, 'object', None)
                    if subj and obj:
                        self.neo4j_graph.query(
                            '''
                            MERGE (a:Entity {name: $subj})
                            MERGE (b:Entity {name: $obj})
                            MERGE (a)-[r:RELATED]->(b)
                            SET r.predicate = $pred, r.conversation_id = $session_id
                            RETURN id(r) as rid
                            ''',
                            {"subj": subj, "obj": obj, "pred": pred, "session_id": self.session_id}
                        )
                except Exception:
                    logger.exception('Failed to persist triple to Neo4j')

            def get_entity_knowledge(self, entity: str, depth: int = 1):
                # Prefer fetching from Neo4j for up-to-date KG
                try:
                    rows = self.neo4j_graph.query(
                        '''
                        MATCH (a {name: $entity})-[r]->(b)
                        RETURN a.name as a, type(r) as rel, b.name as b
                        LIMIT $limit
                        ''',
                        {"entity": entity, "limit": depth * 10}
                    ) or []
                    results = [f"{r['a']} {r['rel']} {r['b']}" for r in rows if r.get('a') and r.get('b')]
                    if results:
                        return results
                except Exception:
                    logger.debug('Neo4j fetch for entity knowledge failed, falling back to local graph')

                # Fallback to in-memory networkx behavior
                return super().get_entity_knowledge(entity, depth=depth)

        networkx_kg = Neo4jBackedNetworkxGraph(neo4j_graph=neo4j_graph, session_id=self.session_id)

        # Initialize LangChain KG memory using Networkx-backed adapter
        self.kg_memory = ConversationKGMemory(
            llm=llm,
            kg=networkx_kg,
            return_messages=True,
            max_history=max_history,
            entity_types=["Philosopher", "Concept", "Theory", "Argument"],
            relationship_types=["DISCUSSED", "RELATES_TO", "QUESTIONS_ABOUT", "CONCERNS"]
        )
        
        self.exchange_count = 0
        self.created_at = datetime.now()
        self.last_exchange_at = None
        self.archived_exchanges = 0
        self.entity_importance = {}  # Track mention frequency
        
        logger.info(
            f"Conversation memory initialized. "
            f"Session: {self.session_id}, Max history: {max_history}, "
            f"Archival enabled: {enable_archival}"
        )
    
    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session identifier"""
        from uuid import uuid4
        return f"conv_{uuid4().hex[:12]}"
    
    async def add_exchange(
        self,
        question: str,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add Q&A exchange with automatic entity extraction and memory management
        
        Args:
            question: User's question
            answer: Assistant's answer
            metadata: Additional context (sources, confidence, etc.)
            
        Returns:
            Summary with entities, archival status, memory health
        """
        try:
            # Save to KG memory
            self.kg_memory.save_context(
                {"input": question},
                {"output": answer}
            )
            
            self.exchange_count += 1
            self.last_exchange_at = datetime.now()
            
            # Extract entities and update importance scores
            extracted = self._get_extracted_entities()
            self._update_entity_importance(extracted["entities"])
            
            # Check if archival needed (memory management)
            archival_action = None
            if self.enable_archival and self.exchange_count > ARCHIVE_THRESHOLD:
                archival_action = await self._manage_memory_growth()
            
            result = {
                "exchange_count": self.exchange_count,
                "extracted_entities": extracted["entities"],
                "extracted_relationships": extracted["relationships"],
                "timestamp": self.last_exchange_at.isoformat(),
                "memory_health": self._assess_memory_health(),
                "archival_action": archival_action
            }
            
            logger.info(
                f"Exchange {self.exchange_count} saved. "
                f"Entities: {len(extracted['entities'])}, "
                f"Memory status: {result['memory_health']['status']}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error adding exchange: {str(e)}")
            raise
    
    def _update_entity_importance(self, entities: List[str]) -> None:
        """Track entity mention frequency for importance scoring"""
        if not self.enable_importance_scoring:
            return
        
        for entity in entities:
            self.entity_importance[entity] = self.entity_importance.get(entity, 0) + 1
    
    async def _manage_memory_growth(self) -> Optional[Dict[str, Any]]:
        """
        Manage memory growth to prevent catastrophic forgetting while controlling size
        
        Strategy:
        1. Keep important entities (mentioned 3+ times) permanently
        2. Archive older exchanges to separate node
        3. Keep recent exchanges in active memory
        4. Summarize archived content
        
        Returns:
            Archival action taken or None
        """
        try:
            # Identify important entities (appeared 3+ times)
            important_entities = {
                ent: count for ent, count in self.entity_importance.items()
                if count >= IMPORTANT_ENTITIES_THRESHOLD
            }
            
            # Mark important entities to preserve
            if important_entities:
                self.neo4j_graph.query("""
                    UNWIND $entities AS entity_name
                    MATCH (e {name: entity_name})
                    WHERE e.session_id = $session_id
                    SET e.importance = 'HIGH', e.marked_for_preservation = true
                """, {
                    "entities": list(important_entities.keys()),
                    "session_id": self.session_id
                })
            
            # Archive old exchanges (keep last MAX_ACTIVE_EXCHANGES)
            if self.exchange_count > MAX_ACTIVE_EXCHANGES:
                archives_created = self._archive_old_exchanges(
                    keep_recent=MAX_ACTIVE_EXCHANGES
                )
                
                self.archived_exchanges += archives_created
                
                logger.info(
                    f"Archived {archives_created} exchanges. "
                    f"Important entities preserved: {list(important_entities.keys())}"
                )
                
                return {
                    "action": "archival",
                    "exchanges_archived": archives_created,
                    "important_entities_preserved": list(important_entities.keys()),
                    "active_exchanges": min(self.exchange_count, MAX_ACTIVE_EXCHANGES),
                    "total_archived": self.archived_exchanges
                }
            
            return None
        
        except Exception as e:
            logger.warning(f"Memory management error: {e}")
            return None
    
    def _archive_old_exchanges(self, keep_recent: int = MAX_ACTIVE_EXCHANGES) -> int:
        """
        Archive old exchanges to Neo4j, keeping only recent ones in active memory
        
        Returns:
            Number of exchanges archived
        """
        try:
            # Find exchanges beyond our keep_recent threshold
            archived = self.neo4j_graph.query("""
                MATCH (e:Exchange)-[:IN_SESSION]->(s {session_id: $session_id})
                WITH e, e.timestamp as ts
                ORDER BY ts DESC
                WITH collect(e) as exchanges, count(e) as total
                UNWIND exchanges[$keep:$total] as old_exchange
                SET old_exchange:Archived, old_exchange.archived_at = datetime()
                RETURN count(old_exchange) as count
            """, {
                "session_id": self.session_id,
                "keep": keep_recent
            })
            
            count = archived[0]["count"] if archived else 0
            return count
        except Exception as e:
            logger.warning(f"Error archiving exchanges: {e}")
            return 0
    
    def _assess_memory_health(self) -> Dict[str, Any]:
        """
        Assess memory system health
        
        Returns:
            Health metrics including status, size, and recommendations
        """
        health = {
            "status": "healthy",
            "exchange_count": self.exchange_count,
            "archived_exchanges": self.archived_exchanges,
            "important_entities": len({
                e for e, c in self.entity_importance.items()
                if c >= IMPORTANT_ENTITIES_THRESHOLD
            }),
            "total_unique_entities": len(self.entity_importance),
            "recommendations": []
        }
        
        # Check if approaching limits
        if self.exchange_count > ARCHIVE_THRESHOLD:
            health["status"] = "archived"
            health["recommendations"].append(
                f"Older exchanges archived. Active: {min(self.exchange_count, MAX_ACTIVE_EXCHANGES)}"
            )
        
        if self.exchange_count > MAX_ACTIVE_EXCHANGES * 2:
            health["status"] = "warning"
            health["recommendations"].append(
                "Heavy archival load. Consider session review."
            )
        
        return health
    
    def _get_extracted_entities(self) -> Dict[str, List[str]]:
        """Get entities and relationships extracted by KG memory"""
        try:
            # Access the knowledge graph memory's entity storage
            entity_dict = self.kg_memory.entity_memory.to_dict() if hasattr(
                self.kg_memory, 'entity_memory'
            ) else {}
            
            entities = list(entity_dict.keys()) if entity_dict else []
            
            # Get relationships from Neo4j
            relationships = self._query_conversation_relationships()
            
            return {
                "entities": entities,
                "relationships": relationships
            }
        except Exception as e:
            logger.warning(f"Could not extract entities: {e}")
            return {"entities": [], "relationships": []}
    
    def _get_recent_exchanges(self) -> List[Dict[str, str]]:
        """Get recent exchanges for context"""
        try:
            result = self.neo4j_graph.query("""
                MATCH (e:Exchange)-[:IN_SESSION]->(s {session_id: $session_id})
                WHERE NOT e:Archived
                WITH e ORDER BY e.timestamp DESC LIMIT $limit
                RETURN e.input as question, e.output as answer, e.timestamp as ts
                ORDER BY ts
            """, {
                "session_id": self.session_id,
                "limit": MAX_ACTIVE_EXCHANGES
            }) or []
            return result
        except Exception as e:
            logger.warning(f"Could not get recent exchanges: {e}")
            return []
    
    def _query_conversation_relationships(self) -> List[Dict[str, str]]:
        """Query Neo4j for relationships in conversation context"""
        try:
            result = self.neo4j_graph.query("""
                MATCH (a)-[r]->(b)
                WHERE r.conversation_id = $session_id
                RETURN a.id as entity_a, type(r) as relationship, b.id as entity_b
                LIMIT 20
            """, {"session_id": self.session_id})
            
            return [
                {
                    "from": row["entity_a"],
                    "relationship": row["relationship"],
                    "to": row["entity_b"]
                }
                for row in result
            ]
        except Exception as e:
            logger.warning(f"Could not query relationships: {e}")
            return []
    
    async def get_conversation_context(
        self,
        query: Optional[str] = None,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Get conversation context with intelligent truncation for token limits
        
        Handles:
        - Context length overhead (token counting)
        - Recent vs important exchanges prioritization
        - Graceful degradation when context too long
        
        Args:
            query: Optional current query for relevance weighting
            max_tokens: Maximum tokens to return
            
        Returns:
            Context dict with exchanges, entities, metadata
        """
        try:
            context = self.kg_memory.buffer
            
            # Estimate token usage
            token_estimate = self._estimate_context_tokens(context)
            
            optimization_action = None
            if token_estimate > max_tokens:
                # Context too long - optimize
                context, optimization_action = await self._optimize_context_for_tokens(
                    max_tokens,
                    query
                )
            
            # Prepare response
            response = {
                "context": context,
                "exchange_count": self.exchange_count,
                "active_exchanges": min(self.exchange_count, MAX_ACTIVE_EXCHANGES),
                "archived_exchanges": self.archived_exchanges,
                "important_entities": list({
                    e for e, c in self.entity_importance.items()
                    if c >= IMPORTANT_ENTITIES_THRESHOLD
                }),
                "token_estimate": self._estimate_context_tokens(context),
                "max_tokens_allowed": max_tokens,
                "optimization_applied": optimization_action
            }
            
            if optimization_action:
                logger.warning(
                    f"Context optimized: {optimization_action['method']}. "
                    f"Tokens: {token_estimate} → {response['token_estimate']}"
                )
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise
    
    def _estimate_context_tokens(self, text: str) -> int:
        """
        Estimate token count for text (for OpenAI API and context length management)
        
        Uses tiktoken for accurate estimation (GPT-3.5/4 encoding)
        Falls back to rough estimation if unavailable
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except ImportError:
            # Rough fallback: ~4 chars per token
            return len(text) // 4
        except Exception as e:
            logger.warning(f"Token estimation error: {e}. Using character-based fallback.")
            return len(text) // 4
    
    async def _optimize_context_for_tokens(
        self,
        max_tokens: int,
        query: Optional[str] = None
    ) -> tuple:
        """
        Optimize context to fit within token limit while preserving important information
        
        Strategy:
        1. Keep entities (small, high information density)
        2. Keep recent exchanges
        3. Keep exchanges matching query
        4. Summarize or drop older exchanges
        
        Args:
            max_tokens: Maximum tokens to use
            query: Current query for relevance weighting
            
        Returns:
            (optimized_context, optimization_action_dict)
        """
        try:
            # Get important entities first (small, essential)
            important_entities = {
                e: count for e, count in self.entity_importance.items()
                if count >= IMPORTANT_ENTITIES_THRESHOLD
            }
            
            entities_text = (
                f"Important entities: {', '.join(important_entities.keys())}\n"
                if important_entities else ""
            )
            
            # Get recent exchanges
            recent_exchanges = self.neo4j_graph.query("""
                MATCH (e:Exchange)-[:IN_SESSION]->(s {session_id: $session_id})
                WHERE NOT e:Archived
                WITH e ORDER BY e.timestamp DESC LIMIT $limit
                RETURN e.input as question, e.output as answer, e.timestamp as ts
                ORDER BY ts
            """, {
                "session_id": self.session_id,
                "limit": MAX_ACTIVE_EXCHANGES // 2  # Take half of active
            }) or []
            
            # Build optimized context
            exchanges_text = ""
            for exc in recent_exchanges:
                exc_text = f"Q: {exc['question']}\nA: {exc['answer']}\n\n"
                exchanges_text += exc_text
            
            optimized = entities_text + exchanges_text
            
            # If still too long, summarize older exchanges
            if self._estimate_context_tokens(optimized) > max_tokens and self.archived_exchanges > 0:
                summary = self._summarize_archived_exchanges()
                optimized = entities_text + f"[Previous context summary]\n{summary}\n\n" + exchanges_text
            
            # If still over, truncate exchanges (keep recent most)
            if self._estimate_context_tokens(optimized) > max_tokens:
                # Keep just the entities and most recent exchange
                optimized = entities_text
                if recent_exchanges:
                    last_exc = recent_exchanges[-1]
                    optimized += f"\nLast exchange:\nQ: {last_exc['question']}\nA: {last_exc['answer']}"
            
            optimization_action = {
                "method": "context_optimization",
                "entities_preserved": len(important_entities),
                "recent_exchanges_included": len(recent_exchanges),
                "archived_summary_included": self.archived_exchanges > 0
            }
            
            return optimized, optimization_action
        
        except Exception as e:
            logger.warning(f"Context optimization failed: {e}. Returning full context.")
            return self.kg_memory.buffer, {"method": "fallback_no_optimization"}
    
    def _summarize_archived_exchanges(self) -> str:
        """
        Generate summary of archived exchanges to preserve information without bloat
        
        Returns:
            Summary of archived exchanges
        """
        try:
            result = self.neo4j_graph.query("""
                MATCH (e:Exchange:Archived)-[:IN_SESSION]->(s {session_id: $session_id})
                RETURN count(e) as total, 
                       min(e.timestamp) as oldest,
                       max(e.timestamp) as newest
            """, {"session_id": self.session_id})
            
            if result:
                row = result[0]
                return (
                    f"[Archived: {row['total']} exchanges from "
                    f"{row['oldest'][:10] if row['oldest'] else 'unknown'} "
                    f"to {row['newest'][:10] if row['newest'] else 'unknown'}]"
                )
            
            return "[No archived exchanges]"
        
        except Exception as e:
            logger.warning(f"Error summarizing archives: {e}")
            return "[Archive summary unavailable]"
    
    async def get_entity_context(self) -> Dict[str, Any]:
        """
        Get extracted entities and their relationships
        
        Returns:
            Dictionary of entities and their conversation context
        """
        try:
            if not hasattr(self.kg_memory, 'entity_memory'):
                return {}
            
            entity_data = self.kg_memory.entity_memory.to_dict()
            
            # Enrich with relationship information
            enriched = {}
            for entity, summary in entity_data.items():
                enriched[entity] = {
                    "summary": summary,
                    "relationships": self._query_entity_relationships(entity)
                }
            
            return enriched
        
        except Exception as e:
            logger.warning(f"Error getting entity context: {e}")
            return {}
    
    def _query_entity_relationships(self, entity_name: str) -> List[Dict]:
        """Get Neo4j relationships for a specific entity"""
        try:
            result = self.neo4j_graph.query("""
                MATCH (e {name: $entity})-[r]-(other)
                WHERE r.conversation_id = $session_id
                RETURN other.name as connected_entity, type(r) as relationship
            """, {"entity": entity_name, "session_id": self.session_id})
            
            return [
                {
                    "entity": row["connected_entity"],
                    "relationship": row["relationship"]
                }
                for row in result
            ]
        except Exception:
            return []
    
    async def get_summary(self) -> str:
        """
        Get concise summary of conversation for context
        
        Returns:
            Summary text suitable for including in prompts
        """
        context_data = await self.get_conversation_context()
        
        if not context_data or not context_data.get("context"):
            return "No previous conversation context."
        
        return context_data["context"]
    
    async def link_to_main_kg(self) -> Dict[str, int]:
        """
        Link conversation entities to main philosophy knowledge graph
        
        Returns:
            Statistics on linked entities
        """
        try:
            result = self.neo4j_graph.query("""
                // Match philosophers in conversation
                MATCH (convo_entity)-[r]-(other)
                WHERE r.conversation_id = $session_id
                
                // Find same entities in main KG
                WITH convo_entity, other, r, 
                     lower(convo_entity.name) as convo_name,
                     lower(other.name) as other_name
                
                MATCH (main_entity:Philosopher {name: convo_entity.name})
                OR MATCH (main_entity:Concept {name: convo_entity.name})
                
                // Create relationship to main KG
                CREATE (convo_entity)-[:LINKS_TO]->(main_entity)
                
                RETURN count(*) as linked_count
            """, {"session_id": self.session_id})
            
            linked = result[0]["linked_count"] if result else 0
            logger.info(f"Linked {linked} entities to main KG")
            
            return {"entities_linked": linked}
        
        except Exception as e:
            logger.warning(f"Could not link to main KG: {e}")
            return {"entities_linked": 0}
    
    async def export_session(self) -> Dict[str, Any]:
        """
        Export complete conversation for analysis or persistence
        
        Returns:
            Dictionary with all conversation data and extracted knowledge
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_exchange_at": self.last_exchange_at.isoformat() if self.last_exchange_at else None,
            "exchange_count": self.exchange_count,
            "conversation_context": await self.get_conversation_context(),
            "extracted_entities": await self.get_entity_context(),
            "relationships": self._query_conversation_relationships()
        }
    
    async def clear_history(self) -> None:
        """Clear conversation memory (caution: destructive)"""
        try:
            self.kg_memory.clear()
            self.exchange_count = 0
            logger.info(f"Cleared conversation memory for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")
            raise
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get metadata about current session"""
        return {
            "session_id": self.session_id,
            "exchange_count": self.exchange_count,
            "created_at": self.created_at.isoformat(),
            "last_exchange_at": self.last_exchange_at.isoformat() if self.last_exchange_at else None,
            "elapsed_seconds": (datetime.now() - self.created_at).total_seconds(),
            "max_history": self.max_history
        }
