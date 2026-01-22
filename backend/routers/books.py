from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.services.knowledge.reference_service import ReferenceService
from backend.services.knowledge.kg_service import KnowledgeGraphService
from backend.services.core.llm_service import LLMService

router = APIRouter()

def get_reference_service():
    return ReferenceService()

def get_kg_service():
    return KnowledgeGraphService()

class ProcessBookRequest(BaseModel):
    filename: str
    llm_provider: str = "ollama"
    model: Optional[str] = None
    overwrite: bool = False

class ProcessMultipleBooksRequest(BaseModel):
    filenames: List[str]
    llm_provider: str = "ollama"
    model: Optional[str] = None
    overwrite: bool = False

class AddBookRequest(BaseModel):
    filename: str
    content: str

@router.get("/list")
def list_books(ref_service: ReferenceService = Depends(get_reference_service)):
    """Get list of all books in the reference folder"""
    try:
        books = ref_service.get_all_books()
        return {"books": books, "count": len(books)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
def get_book(
    filename: str,
    ref_service: ReferenceService = Depends(get_reference_service)
):
    """Get book information and content"""
    try:
        info = ref_service.get_book_info(filename)
        if not info:
            raise HTTPException(status_code=404, detail=f"Book '{filename}' not found")
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
def add_book(
    request: AddBookRequest,
    ref_service: ReferenceService = Depends(get_reference_service)
):
    """Add a new book from text content"""
    try:
        result = ref_service.add_book_from_text(request.filename, request.content)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
def upload_book(
    file: UploadFile = File(...),
    ref_service: ReferenceService = Depends(get_reference_service)
):
    """Upload a book file"""
    try:
        content = file.file.read()
        
        # Decode text files
        if file.filename.endswith(('.txt', '.md')):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # For PDF, we need to save and read it
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                from pypdf import PdfReader
                reader = PdfReader(tmp_path)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                text_content = "\n".join(text_parts)
            finally:
                os.unlink(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        result = ref_service.add_book_from_text(file.filename, text_content)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
def delete_book(
    filename: str,
    ref_service: ReferenceService = Depends(get_reference_service)
):
    """Delete a book file"""
    try:
        result = ref_service.delete_book(filename)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
def process_book(
    request: ProcessBookRequest,
    ref_service: ReferenceService = Depends(get_reference_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Process a single book and create knowledge graph"""
    try:
        content = ref_service.read_book_content(request.filename)
        if not content:
            raise HTTPException(status_code=404, detail=f"Could not read book '{request.filename}'")
        
        source_name = request.filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
        result = kg_service.create_graph_from_text(
            text=content,
            source_name=source_name,
            llm_provider=request.llm_provider,
            model=request.model,
            overwrite=request.overwrite
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-multiple")
def process_multiple_books(
    request: ProcessMultipleBooksRequest,
    ref_service: ReferenceService = Depends(get_reference_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Process multiple books and create knowledge graphs"""
    try:
        books = []
        for filename in request.filenames:
            content = ref_service.read_book_content(filename)
            if content:
                source_name = filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
                books.append({
                    "filename": filename,
                    "name": source_name,
                    "content": content
                })
        
        if not books:
            raise HTTPException(status_code=404, detail="No valid books found")
        
        result = kg_service.process_multiple_books(
            books=books,
            llm_provider=request.llm_provider,
            model=request.model,
            overwrite=request.overwrite
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/list")
def list_sources(kg_service: KnowledgeGraphService = Depends(get_kg_service)):
    """Get list of all sources (books) in the knowledge graph"""
    try:
        sources = kg_service.get_sources()
        stats = []
        for source in sources:
            stats.append(kg_service.get_source_stats(source))
        return {"sources": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
