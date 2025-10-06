"""
Configurações centralizadas da aplicação Flask.
"""
import os
from typing import List


class Config:
    """Configuração base da aplicação Flask."""
    
    # Informações da aplicação
    APP_NAME = "TCC Flask - Padrões de Projeto"
    APP_DESCRIPTION = "API robusta demonstrando padrões de projeto em Flask"
    VERSION = "2.0.0"
    
    # Configurações de segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 1800  # 30 minutos
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tcc_flask.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Configurações de CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8080",
    ]
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurações de rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per minute"
    
    # Configurações de paginação
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Configurações de desenvolvimento
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Configuração para ambiente de testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/tcc_flask_prod'


# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
