"""Groq LLM provider implementation."""
from typing import List
from groq import Groq
from .base import BaseLLMProvider, Message, LLMResponse

class GroqProvider(BaseLLMProvider):
    """Groq LLM provider."""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = Groq(api_key=api_key)
    
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Groq."""
        formatted_messages = self.format_messages(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
            raw_response=response
        )
    
    def stream_complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        """Stream completion using Groq."""
        formatted_messages = self.format_messages(messages)
        
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content