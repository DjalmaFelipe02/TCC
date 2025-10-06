"""
Configurações centralizadas da aplicação FastAPI.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Informações da API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TCC FastAPI - Padrões de Projeto"
    PROJECT_DESCRIPTION: str = "API robusta demonstrando padrões de projeto em FastAPI"
    VERSION: str = "2.0.0"
    
    # Configurações do servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Configurações de segurança
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Configurações de CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    
    # Configurações do banco de dados
    DATABASE_URL: str = "sqlite:///./tcc_fastapi.db"
    
    # Configurações de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurações de rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # segundos
    
    # Configurações de paginação
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global das configurações
settings = Settings()
