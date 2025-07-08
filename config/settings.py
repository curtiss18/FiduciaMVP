from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    searchapi_key: str
    
    # Security
    token_secret_key: Optional[str] = None  # For compliance token signing
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/fiducia_mvp"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # App Settings
    debug: bool = True
    log_level: str = "INFO"
    api_v1_str: str = "/api/v1"
    
    # CORS - Adding wildcard for development
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8000", "http://127.0.0.1:3002"]
    
    # Email Settings (SendGrid)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "notifications@fiducia.ai"
    sendgrid_from_name: str = "Fiducia Compliance System"
    
    class Config:
        env_file = ".env"


settings = Settings()
