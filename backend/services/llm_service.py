from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama  # ← CHANGED: from langchain_community to langchain_ollama
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from backend.config import settings
import httpx


class LLMService:
    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.model = model or settings.DEFAULT_OLLAMA_MODEL
        self.llm: Optional[BaseChatModel] = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=self.model or "gpt-4o-mini",
                temperature=0
            )
        elif self.provider == "ollama":
            self.llm = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=self.model,
                temperature=0
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def check_ollama_available(self) -> bool:
        if self.provider != "ollama":
            return False
        try:
            async with httpx.AsyncClient() as client:
                # Try both common endpoints
                for ep in ("/api/models", "/api/tags"):
                    try:
                        response = await client.get(f"{settings.OLLAMA_BASE_URL}{ep}", timeout=3.0)
                        if response.status_code == 200:
                            return True
                    except Exception:
                        continue
                return False
        except Exception:
            return False
    
    def invoke(self, prompt: str, **kwargs) -> str:
        if not self.llm:
            raise ValueError("LLM not initialized")
        return self.llm.invoke(prompt, **kwargs).content
    
    async def ainvoke(self, prompt: str, **kwargs) -> str:
        if not self.llm:
            raise ValueError("LLM not initialized")
        result = await self.llm.ainvoke(prompt, **kwargs)
        return result.content if hasattr(result, 'content') else str(result)
    
    def stream(self, prompt: str, **kwargs):
        if not self.llm:
            raise ValueError("LLM not initialized")
        return self.llm.stream(prompt, **kwargs)
    
    def get_chat_model(self) -> BaseChatModel:
        return self.llm
