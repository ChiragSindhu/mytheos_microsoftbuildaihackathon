"""Base agent class."""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from src.providers.base import BaseLLMProvider, Message
from src.providers.factory import get_llm_provider
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        llm_provider: Optional[BaseLLMProvider] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.name = name
        self.llm_provider = llm_provider or get_llm_provider()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = get_logger(f"agent.{name}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the agent's task."""
        pass
    
    def generate(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using the LLM."""
        messages = [
            Message(role="system", content=system_prompt or self.get_system_prompt()),
            Message(role="user", content=user_message)
        ]
        
        self.logger.info(f"{self.name} generating response...")
        
        response = self.llm_provider.complete(
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        
        self.logger.info(f"{self.name} response generated. Tokens: {response.usage['total_tokens']}")
        
        return response.content
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"