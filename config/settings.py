"""Configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings."""
    
    # Project
    PROJECT_NAME: str = "MYTHEOS"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # LLM Provider
    LLM_PROVIDER: str = Field(default="groq", env="LLM_PROVIDER")
    
    # Groq
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Anthropic (optional)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    
    # GitHub
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")
    GITHUB_APP_ID: Optional[str] = Field(default=None, env="GITHUB_APP_ID")
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # Agent Settings
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300  # seconds
    
    # Code Execution
    ENABLE_CODE_EXECUTION: bool = True
    EXECUTION_TIMEOUT: int = 60
    DOCKER_IMAGE: str = "python:3.11-slim"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()