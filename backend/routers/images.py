from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.services.tools.image_service import ImageService
from typing import Optional, List
router = APIRouter()

def get_image_service():
    return ImageService()

class ImageSearchRequest(BaseModel):
    query: str
    num_results: int = 5
    providers: Optional[List[str]] = None  # ["duckduckgo", "unsplash", "pexels", "bing"]

@router.post("/search")
async def search_images(
    request: ImageSearchRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Search for images related to the query using multiple providers"""
    try:
        results = await image_service.search_images(
            query=request.query,
            num_results=request.num_results,
            providers=request.providers
        )
        return {
            "images": results,
            "count": len(results),
            "query": request.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/philosopher/{philosopher_name}")
async def get_philosopher_images(
    philosopher_name: str,
    num_results: int = 5,
    image_service: ImageService = Depends(get_image_service)
):
    """Get images for a specific philosopher"""
    try:
        results = await image_service.get_philosopher_images(
            philosopher_name,
            num_results=num_results
        )
        return {
            "images": results,
            "count": len(results),
            "philosopher": philosopher_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/concept")
async def get_concept_images(
    concept: str,
    num_results: int = 5,
    image_service: ImageService = Depends(get_image_service)
):
    """Get images for a philosophical concept"""
    try:
        results = await image_service.get_concept_images(concept, num_results)
        return {
            "images": results,
            "count": len(results),
            "concept": concept
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
