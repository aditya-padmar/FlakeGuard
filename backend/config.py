"""Configuration management for FlakeGuard backend."""
import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application settings."""
    
    # API Configuration
    app_name: str = "FlakeGuard"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # LLM Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./flakeguard.db")
    
    # Paths
    data_dir: str = "data"
    runs_dir: str = "data/runs"
    classifications_dir: str = "data/classifications"
    fixes_dir: str = "data/fixes"
    metrics_dir: str = "data/metrics"
    
    class Config:
        env_file = ".env"


settings = Settings()
