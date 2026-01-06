import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings:
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
    DEFAULT_OLLAMA_MODEL: str = os.getenv("DEFAULT_OLLAMA_MODEL", "gemma3:4b")  # Change to your model name if different
    
    # Web Crawler Configuration
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT", "10"))
    RESPECT_ROBOTS_TXT: bool = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"
    DEFAULT_CRAWL_DELAY: float = float(os.getenv("DEFAULT_CRAWL_DELAY", "1.0"))
    
    # Image Search Configuration
    ENABLE_IMAGE_SEARCH: bool = os.getenv("ENABLE_IMAGE_SEARCH", "true").lower() == "true"
    UNSPLASH_ACCESS_KEY: Optional[str] = os.getenv("UNSPLASH_ACCESS_KEY")
    PEXELS_API_KEY: Optional[str] = os.getenv("PEXELS_API_KEY")
    BING_SEARCH_API_KEY: Optional[str] = os.getenv("BING_SEARCH_API_KEY")
    
    # Web Search Configuration
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")  # Google search via Serper
    
    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # Philosophy Search Configuration
    PRIORITIZE_PHILOSOPHY: bool = os.getenv("PRIORITIZE_PHILOSOPHY", "true").lower() == "true"
    MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "0.0"))
    MAX_ENHANCED_QUERIES: int = int(os.getenv("MAX_ENHANCED_QUERIES", "5"))
    MAX_PHILOSOPHER_CONTEXT: int = int(os.getenv("MAX_PHILOSOPHER_CONTEXT", "2"))
    
    # User Agent Configuration
    USER_AGENT_NAME: str = os.getenv("USER_AGENT_NAME", "KnowledgeGraphRAG-Bot")
    USER_AGENT_VERSION: str = os.getenv("USER_AGENT_VERSION", "1.0")
    USER_AGENT_URL: str = os.getenv("USER_AGENT_URL", "+https://github.com/your-repo; research bot")
    
    @property
    def USER_AGENT(self) -> str:
        """Construct user agent string from components"""
        return f"{self.USER_AGENT_NAME}/{self.USER_AGENT_VERSION} ({self.USER_AGENT_URL})"

settings = Settings()
