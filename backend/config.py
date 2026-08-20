"""
AegisGraph Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./aegisgraph.db"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AegisGraph"
    DEBUG: bool = True
    
    # LLM Settings
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_MODEL: str = "qwen-plus"
    
    # Synthetic Data Settings
    NUM_ENTITIES: int = 100
    OBSERVATION_HOURS: int = 24
    OBSERVATIONS_PER_HOUR: int = 500  # Total ~12k observations
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
