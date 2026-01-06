"""
Prompt management for philosophy RAG system.
Decoupled prompt templates following Microsoft's GraphRAG pattern.
"""

from .prompt_loader import PromptLoader

__all__ = ["PromptLoader"]
