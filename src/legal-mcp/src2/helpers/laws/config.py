"""
Configuration management for the Geo-Regulation AI System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # LLM API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = "AIzaSyCPRpKXzjOTlb3SDyC8TbWbPTYGL9nGzwU"
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/geolegal"
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    api_key: str = "demo-key-2025"
    log_level: str = "INFO"
    environment: str = "development"
    
    # Performance
    max_concurrent_analyses: int = 10
    cache_ttl_seconds: int = 3600
    llm_timeout_seconds: int = 30
    
    # Feature Flags - Team Members will enable these
    enable_caching: bool = False
    enable_real_mcps: bool = False
    enable_batch_processing: bool = False
    enable_workflow_viz: bool = False
    
    # MCP Service URLs - Team Member 1 configures
    utah_mcp_url: str = "http://localhost:8010"
    eu_mcp_url: str = "http://localhost:8011"
    california_mcp_url: str = "http://localhost:8012"
    florida_mcp_url: str = "http://localhost:8013"
    brazil_mcp_url: str = "http://localhost:8014"

    model_config = {
        "env_file": ".env", 
        "case_sensitive": False
    }

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