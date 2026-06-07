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

    # API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=1, env="API_WORKERS")

    # CORS
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # LLM Provider
    LLM_PROVIDER: str = Field(default="groq", env="LLM_PROVIDER")
    
    # Groq
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    
    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Anthropic (optional)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    
    # GitHub
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")
    GITHUB_APP_ID: Optional[str] = Field(default=None, env="GITHUB_APP_ID")
    
    # Azure Storage (optional - for logs/reports)
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_CONTAINER: str = Field(default="debug-reports", env="AZURE_STORAGE_CONTAINER")
    
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
    
    # Redis (for SSE/WebSocket state)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()