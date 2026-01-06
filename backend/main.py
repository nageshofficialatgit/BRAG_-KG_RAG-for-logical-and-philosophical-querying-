from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from backend.routers import kg, rag, web_crawler, images, books

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(
    title="Knowledge Graph RAG API",
    description="API for Knowledge Graph RAG system with web crawling and image retrieval",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kg.router, prefix="/api/kg", tags=["knowledge-graph"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(web_crawler.router, prefix="/api/crawler", tags=["web-crawler"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(books.router, prefix="/api/books", tags=["books"])

@app.get("/")
async def root():
    return {"message": "Knowledge Graph RAG API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
