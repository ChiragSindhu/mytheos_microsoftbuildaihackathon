"""Azure OpenAI provider implementation."""
from typing import List
from openai import OpenAI

from config import settings
from .base import BaseLLMProvider, Message, LLMResponse

class AzureOpenAIProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        azure_endpoint: str,
        **kwargs
    ):
        super().__init__(api_key, model, **kwargs)

        self.client = OpenAI(
            api_key=api_key,
            base_url=f"{azure_endpoint}/openai/v1"
        )

    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        
        return LLMResponse(
            content="""
                Bug Analysis:
                The error occurs because an integer is being added to a string.

                Root Cause:
                Type mismatch between operands.

                Suggested Fix:
                Convert the string to an integer before performing addition.

                Example:
                result = number + int(text_value)
                """,
            model="debug-mock",
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            finish_reason="debug",
            raw_response=None
        )
        

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
        max_tokens: int = 4000,
        **kwargs
    ):
        """Stream completion using Azure OpenAI."""
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
                