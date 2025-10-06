"""
Configuração de logging para a aplicação FastAPI.
"""
import logging
import sys
from typing import Dict, Any
from .config import settings


class ColoredFormatter(logging.Formatter):
    """Formatter personalizado com cores para diferentes níveis de log."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """Configura o sistema de logging da aplicação."""
    
    # Configuração do logger principal
    logger = logging.getLogger("tcc_fastapi")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Formatter com cores
    formatter = ColoredFormatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Configuração para uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(console_handler)
    
    # Configuração para uvicorn.access
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado com o nome especificado."""
    return logging.getLogger(f"tcc_fastapi.{name}")


# Configuração automática ao importar o módulo
setup_logging()
