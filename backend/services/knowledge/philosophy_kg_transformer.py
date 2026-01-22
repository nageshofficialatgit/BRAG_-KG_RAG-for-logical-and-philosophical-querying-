"""
Philosophy-specific knowledge graph transformer with custom entity and relationship extraction
"""
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field
import logging
import json

logger = logging.getLogger(__name__)

# Philosophy-specific entity types
class PhilosophyEntity(BaseModel):
    """Philosophy entity with type and properties"""
    name: str = Field(description="Name of the entity")
    entity_type: str = Field(
        description="Type: Philosopher, Concept, Work, SchoolOfThought, Argument, Theory, Principle"
    )
    description: Optional[str] = Field(default=None, description="Brief description")
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional properties like time_period, nationality, etc."
    )

class PhilosophyRelationship(BaseModel):
    """Philosophy relationship between entities"""
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    relationship_type: str = Field(
        description="Type: INFLUENCES, CONTRADICTS, BUILDS_ON, REFERENCES, DISCUSSES, "
                   "AGREES_WITH, DISAGREES_WITH, INSPIRED_BY, CRITIQUES, SUPPORTS, OPPOSES"
    )
    description: Optional[str] = Field(default=None, description="Context of the relationship")

class PhilosophyGraphExtraction(BaseModel):
    """Complete graph extraction for philosophy text"""
    entities: List[PhilosophyEntity] = Field(description="List of entities found")
    relationships: List[PhilosophyRelationship] = Field(description="List of relationships found")

class PhilosophyKGTransformer:
    """Custom transformer for philosophy-specific knowledge graph extraction"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=PhilosophyGraphExtraction)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup philosophy-specific extraction prompts"""
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in philosophy and knowledge graph extraction. 
Extract entities and relationships from philosophical text with high precision.

ENTITY TYPES:
- Philosopher: Historical or contemporary philosophers (e.g., Aristotle, Kant, Hume)
- Concept: Philosophical concepts, ideas, theories (e.g., free will, determinism, virtue)
- Work: Books, essays, treatises (e.g., "Nicomachean Ethics", "Critique of Pure Reason")
- SchoolOfThought: Philosophical schools or traditions (e.g., Stoicism, Utilitarianism)
- Argument: Specific philosophical arguments or positions
- Theory: Philosophical theories (e.g., virtue ethics, deontology)
- Principle: Fundamental principles or maxims

RELATIONSHIP TYPES:
- INFLUENCES: One philosopher/concept influences another
- CONTRADICTS: Entities that contradict each other
- BUILDS_ON: One idea builds upon another
- REFERENCES: One work/philosopher references another
- DISCUSSES: Entity discusses or addresses another
- AGREES_WITH: Agreement between philosophers/concepts
- DISAGREES_WITH: Disagreement between philosophers/concepts
- INSPIRED_BY: Inspiration relationship
- CRITIQUES: Critical analysis of one by another
- SUPPORTS: Supporting relationship
- OPPOSES: Opposition relationship

Extract ALL relevant entities and relationships. Be thorough and precise."""),
            ("human", """Extract entities and relationships from this philosophical text:

{text}

Return a JSON object with:
- entities: List of all entities with their types and descriptions
- relationships: List of all relationships between entities

Focus on:
1. Philosophers mentioned and their ideas
2. Philosophical concepts and their relationships
3. Works cited and their connections
4. Arguments and positions
5. Schools of thought and traditions

Be comprehensive but accurate. Only extract relationships that are explicitly stated or clearly implied."""),
        ])
    
    async def extract_philosophy_graph(
        self,
        text: str,
        chunk_index: int = 0
    ) -> Dict[str, Any]:
        """Extract philosophy-specific graph from text"""
        try:
            # Get structured extraction
            chain = self.extraction_prompt | self.llm | self.parser
            
            result = await chain.ainvoke({"text": text})
            
            # Handle case where result might be a dict or Pydantic model
            if hasattr(result, 'entities'):
                entities = result.entities
                relationships = result.relationships
            else:
                entities = result.get("entities", [])
                relationships = result.get("relationships", [])
            
            # Convert to graph document format
            nodes = []
            rels = []
            
            # Process entities
            for entity in entities:
                # Handle both dict and Pydantic model
                if hasattr(entity, 'name'):
                    name = entity.name
                    entity_type = entity.entity_type
                    description = entity.description
                    props = entity.properties or {}
                else:
                    name = entity.get("name", "")
                    entity_type = entity.get("entity_type", "Entity")
                    description = entity.get("description", "")
                    props = entity.get("properties", {})
                
                node = {
                    "id": name,
                    "type": entity_type,
                    "properties": {
                        "description": description or "",
                        "chunk_index": chunk_index,
                        **props
                    }
                }
                nodes.append(node)
            
            # Process relationships
            for rel in relationships:
                # Handle both dict and Pydantic model
                if hasattr(rel, 'source'):
                    source = rel.source
                    target = rel.target
                    rel_type = rel.relationship_type
                    description = rel.description
                else:
                    source = rel.get("source", "")
                    target = rel.get("target", "")
                    rel_type = rel.get("relationship_type", "RELATED_TO")
                    description = rel.get("description", "")
                
                relationship = {
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "properties": {
                        "description": description or "",
                        "chunk_index": chunk_index
                    }
                }
                rels.append(relationship)
            
            return {
                "nodes": nodes,
                "relationships": rels,
                "chunk_index": chunk_index
            }
        except Exception as e:
            logger.error(f"Error extracting philosophy graph: {str(e)}")
            # Fallback to basic extraction
            return self._fallback_extraction(text, chunk_index)
    
    def _fallback_extraction(self, text: str, chunk_index: int) -> Dict[str, Any]:
        """Fallback extraction if structured extraction fails"""
        # Simple keyword-based extraction as fallback
        nodes = []
        relationships = []
        
        # This is a minimal fallback - in production, use more sophisticated NER
        return {
            "nodes": nodes,
            "relationships": relationships,
            "chunk_index": chunk_index
        }
    
    def convert_to_graph_documents(
        self,
        documents: List[Document]
    ) -> List[Any]:
        """Convert documents to LangChain GraphDocument format"""
        from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        all_graph_docs = []
        
        for doc in documents:
            try:
                result = loop.run_until_complete(
                    self.extract_philosophy_graph(doc.page_content, chunk_index=documents.index(doc))
                )
                
                # Convert to Node and Relationship objects
                nodes = []
                relationships = []
                
                # Create nodes
                for node_data in result.get("nodes", []):
                    node = Node(
                        id=node_data["id"],
                        type=node_data.get("type", "Entity"),
                        properties=node_data.get("properties", {})
                    )
                    nodes.append(node)
                
                # Create relationships
                for rel_data in result.get("relationships", []):
                    # Find or create source and target nodes
                    source_node = next((n for n in nodes if n.id == rel_data["source"]), None)
                    target_node = next((n for n in nodes if n.id == rel_data["target"]), None)
                    
                    if not source_node:
                        source_node = Node(id=rel_data["source"], type="Entity")
                        nodes.append(source_node)
                    if not target_node:
                        target_node = Node(id=rel_data["target"], type="Entity")
                        nodes.append(target_node)
                    
                    relationship = Relationship(
                        source=source_node,
                        target=target_node,
                        type=rel_data["type"],
                        properties=rel_data.get("properties", {})
                    )
                    relationships.append(relationship)
                
                # Create GraphDocument
                graph_doc = GraphDocument(
                    nodes=nodes,
                    relationships=relationships,
                    source=doc.metadata.get("source", "unknown")
                )
                all_graph_docs.append(graph_doc)
                
            except Exception as e:
                logger.warning(f"Error processing document: {e}")
                continue
        
        return all_graph_docs
