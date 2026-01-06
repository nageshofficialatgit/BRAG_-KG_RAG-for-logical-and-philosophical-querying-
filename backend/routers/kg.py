from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.services.kg_service import KnowledgeGraphService
from backend.services.llm_service import LLMService

router = APIRouter()

# Dependency to get KG service
def get_kg_service():
    return KnowledgeGraphService()

class CreateGraphRequest(BaseModel):
    text: str
    source_name: str = "reference_text"
    llm_provider: str = "ollama"
    model: Optional[str] = None
    overwrite: bool = False
    use_philosophy_transformer: bool = True

class QueryRequest(BaseModel):
    cypher_query: str

class EntityRequest(BaseModel):
    entity_name: str
    limit: int = 10

@router.post("/create")
async def create_graph(
    request: CreateGraphRequest,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Create knowledge graph from reference text"""
    try:
        result = kg_service.create_graph_from_text(
            text=request.text,
            source_name=request.source_name,
            llm_provider=request.llm_provider,
            model=request.model,
            overwrite=request.overwrite,
            use_philosophy_transformer=request.use_philosophy_transformer
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(kg_service: KnowledgeGraphService = Depends(get_kg_service)):
    """Get knowledge graph statistics"""
    try:
        stats = kg_service._get_graph_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_graph(
    request: QueryRequest,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Execute a Cypher query on the graph"""
    try:
        results = kg_service.query_graph(request.cypher_query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities/related")
async def get_related_entities(
    request: EntityRequest,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get entities related to a given entity"""
    try:
        results = kg_service.get_related_entities(
            request.entity_name,
            limit=request.limit
        )
        return {"entities": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visualization")
async def get_visualization_data(
    query: str,
    limit: int = 50,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get graph data for visualization"""
    try:
        graph_data = kg_service.get_graph_for_visualization(query, limit)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_graph(kg_service: KnowledgeGraphService = Depends(get_kg_service)):
    """Clear all nodes and relationships from the graph"""
    try:
        result = kg_service.clear_graph()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/philosopher/{philosopher_name}/influences")
async def get_philosopher_influences(
    philosopher_name: str,
    direction: str = "both",
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get philosopher influences"""
    try:
        result = kg_service.get_philosopher_influences(philosopher_name, direction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/philosopher/path")
async def find_philosopher_path(
    philosopher1: str,
    philosopher2: str,
    max_depth: int = 3,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Find path between two philosophers"""
    try:
        result = kg_service.find_philosopher_path(philosopher1, philosopher2, max_depth)
        return {"path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concept/{concept_name}/philosophers")
async def get_concept_philosophers(
    concept_name: str,
    sources: Optional[List[str]] = None,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get philosophers who discuss a concept"""
    try:
        result = kg_service.get_concept_philosophers(concept_name, sources)
        return {"philosophers": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/philosopher/compare")
async def compare_philosophers(
    philosopher1: str,
    philosopher2: str,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Compare two philosophers"""
    try:
        result = kg_service.compare_philosophers(philosopher1, philosopher2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concept/{concept_name}/network")
async def get_concept_network(
    concept_name: str,
    depth: int = 2,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get network of related concepts"""
    try:
        result = kg_service.get_concept_network(concept_name, depth)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/school/{school_name}/members")
async def get_school_members(
    school_name: str,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get philosophers in a school of thought"""
    try:
        result = kg_service.get_school_of_thought_members(school_name)
        return {"members": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity/{entity_name}")
async def get_entity_details(
    entity_name: str,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get detailed information about an entity"""
    try:
        result = kg_service.get_entity_details(entity_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
