@echo off
echo Starting Knowledge Graph RAG Backend...
python -m uvicorn backend.main:app --reload --port 8000
pause
