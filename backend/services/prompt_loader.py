"""
Dynamic prompt loading service following Microsoft's GraphRAG pattern.
Decouples prompts from code and allows runtime modification.
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load and manage prompts from external files"""
    
    # Prompt file names mapping
    PROMPT_FILES = {
        "philosophy_response": "philosophy_response.txt",
        "improvement": "improvement.txt",
        "validation": "validation.txt",
        "factual_question": "factual_question.txt",
        "analytical_question": "analytical_question.txt",
        "creative_question": "creative_question.txt",
    }
    
    def __init__(self, prompt_dir: Optional[str] = None):
        """
        Initialize PromptLoader
        
        Args:
            prompt_dir: Directory containing prompt files. Defaults to backend/prompts/
        """
        if prompt_dir is None:
            # Auto-detect prompts directory
            backend_dir = Path(__file__).parent.parent
            prompt_dir = str(backend_dir / "prompts")
        
        self.prompt_dir = Path(prompt_dir)
        self._cache: Dict[str, str] = {}
        
        if not self.prompt_dir.exists():
            logger.warning(f"Prompt directory does not exist: {self.prompt_dir}")
            self.prompt_dir.mkdir(parents=True, exist_ok=True)
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        Get a prompt template by name
        
        Args:
            prompt_name: Name of the prompt (e.g., 'philosophy_response', 'improvement')
            
        Returns:
            Prompt template string
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Check cache first
        if prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Get file path
        if prompt_name not in self.PROMPT_FILES:
            raise ValueError(
                f"Unknown prompt: {prompt_name}. "
                f"Available: {list(self.PROMPT_FILES.keys())}"
            )
        
        file_name = self.PROMPT_FILES[prompt_name]
        file_path = self.prompt_dir / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        # Load and cache
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self._cache[prompt_name] = content
            logger.debug(f"Loaded prompt: {prompt_name} from {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error loading prompt {prompt_name}: {str(e)}")
            raise
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all available prompts"""
        prompts = {}
        for prompt_name in self.PROMPT_FILES.keys():
            try:
                prompts[prompt_name] = self.get_prompt(prompt_name)
            except FileNotFoundError:
                logger.warning(f"Prompt file missing: {prompt_name}")
        
        return prompts
    
    def reload_cache(self) -> None:
        """Clear the prompt cache to force reload from disk"""
        self._cache.clear()
        logger.info("Prompt cache cleared")
    
    def set_prompt(self, prompt_name: str, content: str) -> None:
        """
        Update a prompt and save to disk
        
        Args:
            prompt_name: Name of the prompt
            content: New prompt content
        """
        if prompt_name not in self.PROMPT_FILES:
            raise ValueError(f"Unknown prompt: {prompt_name}")
        
        file_name = self.PROMPT_FILES[prompt_name]
        file_path = self.prompt_dir / file_name
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._cache[prompt_name] = content
            logger.info(f"Updated prompt: {prompt_name}")
        except Exception as e:
            logger.error(f"Error saving prompt {prompt_name}: {str(e)}")
            raise
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get and format a prompt with the given arguments
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt string
        """
        prompt = self.get_prompt(prompt_name)
        return prompt.format(**kwargs)
    
    def list_available(self) -> list:
        """List all available prompt names"""
        return list(self.PROMPT_FILES.keys())
