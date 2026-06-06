"""LLM provider factory."""
from typing import Optional
from .base import BaseLLMProvider
from .groq import GroqProvider
from config.settings import settings

class ProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        "groq": GroqProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """Register a new provider."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create(
        cls,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Create an LLM provider instance."""
        provider_name = provider_name or settings.LLM_PROVIDER
        
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Get API key and model from settings if not provided
        if provider_name == "groq":
            api_key = api_key or settings.GROQ_API_KEY
            model = model or settings.GROQ_MODEL
        elif provider_name == "openai":
            api_key = api_key or settings.OPENAI_API_KEY
            model = model or settings.OPENAI_MODEL
        elif provider_name == "anthropic":
            api_key = api_key or settings.ANTHROPIC_API_KEY
            model = model or settings.ANTHROPIC_MODEL
        
        if not api_key:
            raise ValueError(f"API key not provided for {provider_name}")
        
        provider_class = cls._providers[provider_name]
        return provider_class(api_key=api_key, model=model, **kwargs)

# Convenience function
def get_llm_provider(**kwargs) -> BaseLLMProvider:
    """Get the default LLM provider."""
    return ProviderFactory.create(**kwargs)