from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/fiducia_mvp"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # App Settings
    debug: bool = True
    log_level: str = "INFO"
    api_v1_str: str = "/api/v1"
    
    # CORS
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
