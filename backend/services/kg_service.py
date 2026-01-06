from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.text_splitter import TokenTextSplitter
from langchain_core.documents import Document
from backend.config import settings
from backend.services.llm_service import LLMService
from backend.services.philosophy_kg_transformer import PhilosophyKGTransformer
from backend.constants import COMMON_PHILOSOPHERS, PHILOSOPHY_ENTITY_TYPES, PHILOSOPHY_RELATIONSHIP_TYPES
import logging
import asyncio

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        self.kg = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
        )
        self.llm_service = llm_service
    
    def create_graph_from_text(
        self,
        text: str,
        source_name: str = "reference_text",
        llm_provider: str = "ollama",
        model: str = None,
        overwrite: bool = False,
        use_philosophy_transformer: bool = True
    ) -> Dict[str, Any]:
        """Create knowledge graph from reference text with philosophy-specific extraction"""
        try:
            # Check if source already exists
            if not overwrite and self._source_exists(source_name):
                return {
                    "success": False,
                    "error": f"Source '{source_name}' already exists in graph. Use overwrite=True to replace.",
                    "source_exists": True
                }
            
            # Remove existing data for this source if overwriting
            if overwrite:
                self._remove_source(source_name)
            
            # Initialize LLM for graph transformation
            if not self.llm_service:
                self.llm_service = LLMService(provider=llm_provider, model=model)
            
            llm = self.llm_service.get_chat_model()
            
            # Split text into chunks
            text_splitter = TokenTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            documents = [Document(page_content=text, metadata={"source": source_name})]
            chunks = text_splitter.split_documents(documents)
            
            # Use philosophy-specific transformer if enabled
            if use_philosophy_transformer:
                graph_documents = self._create_philosophy_graph(chunks, llm)
            else:
                # Use standard transformer
                llm_transformer = LLMGraphTransformer(llm=llm)
                graph_documents = llm_transformer.convert_to_graph_documents(chunks)
            
            # Store in Neo4j
            result = self.kg.add_graph_documents(
                graph_documents,
                include_source=True,
                baseEntityLabel=True,
            )
            
            # Get statistics
            stats = self._get_graph_stats()
            
            return {
                "success": True,
                "nodes_created": len(graph_documents),
                "statistics": stats,
                "source": source_name,
                "message": f"Created knowledge graph from {source_name}"
            }
        except Exception as e:
            logger.error(f"Error creating knowledge graph: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_philosophy_graph(
        self,
        chunks: List[Document],
        llm
    ) -> List[Any]:
        """Create philosophy-specific graph using custom transformer"""
        try:
            transformer = PhilosophyKGTransformer(llm)
            # Use the transformer's convert_to_graph_documents method
            graph_documents = transformer.convert_to_graph_documents(chunks)
            return graph_documents
            
        except Exception as e:
            logger.error(f"Error in philosophy graph creation: {e}")
            # Fallback to standard transformer
            llm_transformer = LLMGraphTransformer(llm=llm)
            return llm_transformer.convert_to_graph_documents(chunks)
    
    def _source_exists(self, source_name: str) -> bool:
        """Check if a source already exists in the graph"""
        try:
            query = """
            MATCH (d:Document {source: $source_name})
            RETURN count(d) as count
            """
            result = self.kg.query(query, {"source_name": source_name})
            return result[0]["count"] > 0 if result else False
        except Exception:
            return False
    
    def _remove_source(self, source_name: str) -> None:
        """Remove all nodes and relationships for a specific source"""
        try:
            query = """
            MATCH (d:Document {source: $source_name})-[*]-(connected)
            DETACH DELETE d, connected
            """
            self.kg.query(query, {"source_name": source_name})
        except Exception as e:
            logger.warning(f"Error removing source {source_name}: {str(e)}")
    
    def get_sources(self) -> List[str]:
        """Get list of all sources (books) in the knowledge graph"""
        try:
            query = """
            MATCH (d:Document)
            RETURN DISTINCT d.source as source
            ORDER BY source
            """
            results = self.kg.query(query)
            return [r["source"] for r in results if r.get("source")]
        except Exception as e:
            logger.error(f"Error getting sources: {str(e)}")
            return []
    
    def get_source_stats(self, source_name: str) -> Dict[str, Any]:
        """Get statistics for a specific source"""
        try:
            node_query = """
            MATCH (d:Document {source: $source_name})-[*]-(n)
            RETURN count(DISTINCT n) as node_count
            """
            rel_query = """
            MATCH (d:Document {source: $source_name})-[*]-(n1)-[r]-(n2)
            WHERE n1 <> n2
            RETURN count(DISTINCT r) as rel_count
            """
            
            node_result = self.kg.query(node_query, {"source_name": source_name})
            rel_result = self.kg.query(rel_query, {"source_name": source_name})
            
            return {
                "source": source_name,
                "nodes": node_result[0]["node_count"] if node_result else 0,
                "relationships": rel_result[0]["rel_count"] if rel_result else 0
            }
        except Exception as e:
            logger.error(f"Error getting source stats: {str(e)}")
            return {"source": source_name, "nodes": 0, "relationships": 0}
    
    def process_multiple_books(
        self,
        books: List[Dict[str, str]],
        llm_provider: str = "ollama",
        model: str = None,
        overwrite: bool = False,
        use_philosophy_transformer: bool = True
    ) -> Dict[str, Any]:
        """Process multiple books and create knowledge graphs"""
        results = []
        errors = []
        
        for book in books:
            source_name = book.get("name", book.get("filename", "unknown"))
            text = book.get("content", "")
            
            if not text:
                errors.append(f"No content for {source_name}")
                continue
            
            result = self.create_graph_from_text(
                text=text,
                source_name=source_name,
                llm_provider=llm_provider,
                model=model,
                overwrite=overwrite,
                use_philosophy_transformer=use_philosophy_transformer
            )
            
            if result.get("success"):
                results.append({
                    "source": source_name,
                    "nodes_created": result.get("nodes_created", 0)
                })
            else:
                errors.append(f"{source_name}: {result.get('error', 'Unknown error')}")
        
        return {
            "success": len(errors) == 0,
            "processed": len(results),
            "results": results,
            "errors": errors,
            "total_books": len(books)
        }
    
    def _get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        try:
            node_count = self.kg.query("MATCH (n) RETURN count(n) as count")[0]["count"]
            relationship_count = self.kg.query(
                "MATCH ()-[r]->() RETURN count(r) as count"
            )[0]["count"]
            
            # Get node labels
            labels = self.kg.query(
                "CALL db.labels() YIELD label RETURN collect(label) as labels"
            )
            node_labels = labels[0]["labels"] if labels else []
            
            # Get relationship types
            rel_types = self.kg.query(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types"
            )
            relationship_types = rel_types[0]["types"] if rel_types else []
            
            # Get philosophy-specific stats
            philosopher_count = self.kg.query(
                "MATCH (n) WHERE n.type = 'Philosopher' OR 'Philosopher' IN labels(n) RETURN count(n) as count"
            )
            concept_count = self.kg.query(
                "MATCH (n) WHERE n.type = 'Concept' OR 'Concept' IN labels(n) RETURN count(n) as count"
            )
            
            return {
                "total_nodes": node_count,
                "total_relationships": relationship_count,
                "node_labels": node_labels,
                "relationship_types": relationship_types,
                "philosophers": philosopher_count[0]["count"] if philosopher_count else 0,
                "concepts": concept_count[0]["count"] if concept_count else 0
            }
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            return {}
    
    def query_graph(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query on the graph"""
        try:
            return self.kg.query(cypher_query)
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}")
            raise
    
    def get_related_entities(
        self,
        entity_name: str,
        limit: int = 10,
        sources: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get entities related to a given entity, optionally filtered by sources and relationship types"""
        source_filter = ""
        if sources:
            source_list = "', '".join(sources)
            source_filter = f"""
            AND EXISTS {{
                MATCH (e)-[*]-(d:Document)
                WHERE d.source IN ['{source_list}']
            }}
            """
        
        rel_filter = ""
        if relationship_types:
            rel_list = "', '".join(relationship_types)
            rel_filter = f"AND type(r) IN ['{rel_list}']"
        
        query = f"""
        MATCH (e)-[r]->(related)
        WHERE toLower(e.id) CONTAINS toLower($entity_name)
        {source_filter}
        {rel_filter}
        RETURN e.id as entity, type(r) as relationship, related.id as related_entity, 
               e.type as entity_type, related.type as related_type
        LIMIT $limit
        UNION
        MATCH (e)<-[r]-(related)
        WHERE toLower(e.id) CONTAINS toLower($entity_name)
        {source_filter}
        {rel_filter}
        RETURN related.id as entity, type(r) as relationship, e.id as related_entity,
               related.type as entity_type, e.type as related_type
        LIMIT $limit
        """
        try:
            return self.kg.query(query, {"entity_name": entity_name, "limit": limit})
        except Exception as e:
            logger.error(f"Error getting related entities: {str(e)}")
            return []
    
    def find_philosopher_path(
        self,
        philosopher1: str,
        philosopher2: str,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Find path between two philosophers"""
        try:
            query = """
            MATCH path = shortestPath(
                (p1)-[*1..{max_depth}]-(p2)
            )
            WHERE (toLower(p1.id) CONTAINS toLower($phil1) OR toLower(p1.id) = toLower($phil1))
              AND (toLower(p2.id) CONTAINS toLower($phil2) OR toLower(p2.id) = toLower($phil2))
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 5
            """.format(max_depth=max_depth)
            
            results = self.kg.query(query, {"phil1": philosopher1, "phil2": philosopher2})
            return results
        except Exception as e:
            logger.error(f"Error finding philosopher path: {str(e)}")
            return []
    
    def get_philosopher_influences(
        self,
        philosopher_name: str,
        direction: str = "both"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get who influenced this philosopher and who they influenced"""
        try:
            results = {"influenced_by": [], "influences": []}
            
            if direction in ["both", "influenced_by"]:
                query = """
                MATCH (p)<-[r:INFLUENCES|INSPIRED_BY]-(influencer)
                WHERE toLower(p.id) CONTAINS toLower($philosopher)
                RETURN influencer.id as name, type(r) as relationship, p.id as philosopher
                LIMIT 20
                """
                results["influenced_by"] = self.kg.query(query, {"philosopher": philosopher_name})
            
            if direction in ["both", "influences"]:
                query = """
                MATCH (p)-[r:INFLUENCES|INSPIRED_BY]->(influenced)
                WHERE toLower(p.id) CONTAINS toLower($philosopher)
                RETURN influenced.id as name, type(r) as relationship, p.id as philosopher
                LIMIT 20
                """
                results["influences"] = self.kg.query(query, {"philosopher": philosopher_name})
            
            return results
        except Exception as e:
            logger.error(f"Error getting philosopher influences: {str(e)}")
            return {"influenced_by": [], "influences": []}
    
    def get_concept_philosophers(
        self,
        concept_name: str,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all philosophers who discuss a concept"""
        try:
            source_filter = ""
            if sources:
                source_list = "', '".join(sources)
                source_filter = f"""
                AND EXISTS {{
                    MATCH (c)-[*]-(d:Document)
                    WHERE d.source IN ['{source_list}']
                }}
                """
            
            query = f"""
            MATCH (c:Concept)-[r:DISCUSSES|REFERENCES|BUILDS_ON]-(p)
            WHERE (toLower(c.id) CONTAINS toLower($concept) OR c.type = 'Concept')
              AND (p.type = 'Philosopher' OR 'Philosopher' IN labels(p))
            {source_filter}
            RETURN DISTINCT p.id as philosopher, type(r) as relationship, c.id as concept
            LIMIT 30
            """
            return self.kg.query(query, {"concept": concept_name})
        except Exception as e:
            logger.error(f"Error getting concept philosophers: {str(e)}")
            return []
    
    def compare_philosophers(
        self,
        philosopher1: str,
        philosopher2: str
    ) -> Dict[str, Any]:
        """Compare two philosophers - find common concepts and disagreements"""
        try:
            # Common concepts
            common_query = """
            MATCH (p1)-[r1]->(c)<-[r2]-(p2)
            WHERE (toLower(p1.id) CONTAINS toLower($phil1) OR toLower(p1.id) = toLower($phil1))
              AND (toLower(p2.id) CONTAINS toLower($phil2) OR toLower(p2.id) = toLower($phil2))
              AND (c.type = 'Concept' OR 'Concept' IN labels(c))
            RETURN DISTINCT c.id as concept, type(r1) as rel1, type(r2) as rel2
            LIMIT 20
            """
            common = self.kg.query(common_query, {"phil1": philosopher1, "phil2": philosopher2})
            
            # Disagreements
            disagree_query = """
            MATCH (p1)-[r1:CONTRADICTS|DISAGREES_WITH|OPPOSES]->(c)<-[r2:CONTRADICTS|DISAGREES_WITH|OPPOSES]-(p2)
            WHERE (toLower(p1.id) CONTAINS toLower($phil1) OR toLower(p1.id) = toLower($phil1))
              AND (toLower(p2.id) CONTAINS toLower($phil2) OR toLower(p2.id) = toLower($phil2))
            RETURN DISTINCT c.id as concept, type(r1) as rel1, type(r2) as rel2
            LIMIT 20
            """
            disagreements = self.kg.query(disagree_query, {"phil1": philosopher1, "phil2": philosopher2})
            
            return {
                "philosopher1": philosopher1,
                "philosopher2": philosopher2,
                "common_concepts": common,
                "disagreements": disagreements,
                "path": self.find_philosopher_path(philosopher1, philosopher2)
            }
        except Exception as e:
            logger.error(f"Error comparing philosophers: {str(e)}")
            return {}
    
    def get_concept_network(
        self,
        concept_name: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get network of related concepts"""
        try:
            query = f"""
            MATCH path = (c)-[*1..{depth}]-(related)
            WHERE (toLower(c.id) CONTAINS toLower($concept) OR c.type = 'Concept')
              AND (related.type = 'Concept' OR 'Concept' IN labels(related))
            RETURN DISTINCT related.id as concept, length(path) as distance
            ORDER BY distance
            LIMIT 30
            """
            results = self.kg.query(query, {"concept": concept_name})
            
            # Get relationships
            rel_query = """
            MATCH (c1)-[r]-(c2)
            WHERE (toLower(c1.id) CONTAINS toLower($concept) OR toLower(c2.id) CONTAINS toLower($concept))
              AND (c1.type = 'Concept' OR c2.type = 'Concept')
            RETURN c1.id as source, type(r) as relationship, c2.id as target
            LIMIT 20
            """
            relationships = self.kg.query(rel_query, {"concept": concept_name})
            
            return {
                "concept": concept_name,
                "related_concepts": results,
                "relationships": relationships
            }
        except Exception as e:
            logger.error(f"Error getting concept network: {str(e)}")
            return {}
    
    def get_school_of_thought_members(
        self,
        school_name: str
    ) -> List[Dict[str, Any]]:
        """Get philosophers belonging to a school of thought"""
        try:
            query = """
            MATCH (s:SchoolOfThought)-[r]-(p)
            WHERE (toLower(s.id) CONTAINS toLower($school) OR s.type = 'SchoolOfThought')
              AND (p.type = 'Philosopher' OR 'Philosopher' IN labels(p))
            RETURN DISTINCT p.id as philosopher, type(r) as relationship, s.id as school
            LIMIT 30
            """
            return self.kg.query(query, {"school": school_name})
        except Exception as e:
            logger.error(f"Error getting school members: {str(e)}")
            return []
    
    def get_graph_for_visualization(
        self,
        query: str,
        limit: int = 50,
        include_concepts: bool = True
    ) -> Dict[str, Any]:
        """Get graph data formatted for visualization with enhanced philosophy support"""
        # Extract entities from query using LLM if available
        entities = self._extract_entities_from_query_enhanced(query)
        
        nodes = set()
        edges = []
        node_types = {}
        
        for entity in entities[:5]:  # Limit to 5 entities
            related = self.get_related_entities(entity, limit=10)
            for rel in related:
                source = rel.get("entity", "")
                target = rel.get("related_entity", "")
                relationship = rel.get("relationship", "")
                source_type = rel.get("entity_type", "Entity")
                target_type = rel.get("related_type", "Entity")
                
                if source and target:
                    nodes.add(source)
                    nodes.add(target)
                    node_types[source] = source_type
                    node_types[target] = target_type
                    edges.append({
                        "source": source,
                        "target": target,
                        "relationship": relationship
                    })
        
        return {
            "nodes": [
                {
                    "id": node,
                    "label": node,
                    "type": node_types.get(node, "Entity")
                }
                for node in nodes
            ],
            "edges": edges
        }
    
    def _extract_entities_from_query_enhanced(self, query: str) -> List[str]:
        """Enhanced entity extraction using LLM if available, fallback to keyword matching"""
        entities = []
        
        # Try LLM-based extraction if service available
        if self.llm_service:
            try:
                prompt = f"""Extract all philosopher names, concepts, and works mentioned in this query: "{query}"

Return only the names, one per line, no explanations."""
                result = self.llm_service.invoke(prompt)
                # Parse result (simple line-by-line)
                extracted = [line.strip() for line in result.split('\n') if line.strip()]
                entities.extend(extracted[:10])  # Limit to 10
            except Exception as e:
                logger.warning(f"LLM entity extraction failed: {e}")
        
        # Fallback to keyword matching
        if not entities:
            query_lower = query.lower()
            for philosopher in COMMON_PHILOSOPHERS:
                if philosopher.lower() in query_lower:
                    entities.append(philosopher)
        
        return entities if entities else [query]  # Fallback to query itself
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Extract potential entities from query (simplified)"""
        return self._extract_entities_from_query_enhanced(query)
    
    def get_entity_details(self, entity_name: str) -> Dict[str, Any]:
        """Get detailed information about an entity"""
        try:
            # Get entity node
            node_query = """
            MATCH (e)
            WHERE toLower(e.id) = toLower($entity_name) OR toLower(e.id) CONTAINS toLower($entity_name)
            RETURN e, labels(e) as labels
            LIMIT 1
            """
            nodes = self.kg.query(node_query, {"entity_name": entity_name})
            
            if not nodes:
                return {"entity": entity_name, "found": False}
            
            node = nodes[0]
            entity_id = node.get("e", {}).get("id", entity_name)
            
            # Get all relationships
            relationships = self.get_related_entities(entity_name, limit=50)
            
            # Get entity type
            entity_type = node.get("e", {}).get("type", "Entity")
            
            return {
                "entity": entity_id,
                "type": entity_type,
                "properties": dict(node.get("e", {})),
                "labels": node.get("labels", []),
                "relationships": relationships,
                "found": True
            }
        except Exception as e:
            logger.error(f"Error getting entity details: {str(e)}")
            return {"entity": entity_name, "found": False}
    
    def clear_graph(self) -> Dict[str, Any]:
        """Clear all nodes and relationships from the graph"""
        try:
            self.kg.query("MATCH (n) DETACH DELETE n")
            return {"success": True, "message": "Graph cleared"}
        except Exception as e:
            logger.error(f"Error clearing graph: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'driver'):
            self.driver.close()
