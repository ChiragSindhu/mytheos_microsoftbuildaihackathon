"""Abstract LLM provider interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Message:
    """Message format."""
    role: str  # 'system', 'user', 'assistant'
    content: str

@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    raw_response: Any = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate completion."""
        pass
    
    @abstractmethod
    def stream_complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ):
        """Stream completion."""
        pass
    
    def format_messages(self, messages: List[Message]) -> Any:
        """Format messages for provider-specific API."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]