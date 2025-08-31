"""
Configuration management for the Geo-Regulation AI System
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # LLM API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/geolegal"
    
    # Legal MCP Database Configuration (for backwards compatibility)
    db_host: Optional[str] = "localhost"
    db_port: Optional[int] = 5432
    db_name: Optional[str] = "geolegal"
    db_user: Optional[str] = "user"
    db_password: Optional[str] = "password"
    root_path: Optional[str] = None
    
    # Application
    api_key: str = "demo-key-2025"
    log_level: str = "INFO"
    environment: str = "development"
    
    # Performance
    max_concurrent_analyses: int = 10
    llm_timeout_seconds: int = 30
    
    # Feature Flags - Streamlined for hackathon scope  
    enable_batch_processing: bool = False
    
    # MCP Service URLs - Original architecture
    utah_mcp_url: str = "http://localhost:8010"
    eu_mcp_url: str = "http://localhost:8011"
    california_mcp_url: str = "http://localhost:8012"
    florida_mcp_url: str = "http://localhost:8013"
    brazil_mcp_url: str = "http://localhost:8014"
    
    # TRD Architecture - 2-MCP system
    legal_mcp_url: str = "http://localhost:8010"
    requirements_mcp_url: str = "http://localhost:8011"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

# Global settings instance
settings = Settings()

# MCP service configuration for Team Member 1
MCP_SERVICES = {
    'utah': {
        'url': settings.utah_mcp_url,
        'timeout': 30,
        'retries': 2
    },
    'eu': {
        'url': settings.eu_mcp_url,
        'timeout': 30,
        'retries': 2
    },
    'california': {
        'url': settings.california_mcp_url,
        'timeout': 30,
        'retries': 2
    },
    'florida': {
        'url': settings.florida_mcp_url,
        'timeout': 30,
        'retries': 2
    },
    'brazil': {
        'url': settings.brazil_mcp_url,
        'timeout': 30,
        'retries': 2
    }
}