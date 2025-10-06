"""
Configuração de logging para a aplicação Flask.
"""
import logging
import sys
from typing import Dict, Any
from flask import Flask


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


def setup_logging(app: Flask) -> None:
    """Configura o sistema de logging da aplicação Flask."""
    
    # Remove handlers padrão do Flask
    if app.logger.handlers:
        app.logger.handlers.clear()
    
    # Configuração do logger principal
    logger = logging.getLogger("tcc_flask")
    logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Formatter com cores
    formatter = ColoredFormatter(app.config.get('LOG_FORMAT'))
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    app.logger.addHandler(console_handler)
    
    # Configuração para werkzeug (servidor de desenvolvimento)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(console_handler)
    
    app.logger.info(f"Logging configurado para aplicação {app.config.get('APP_NAME')}")


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado com o nome especificado."""
    return logging.getLogger(f"tcc_flask.{name}")


class RequestLogger:
    """Middleware para logging de requisições."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Inicializa o middleware com a aplicação Flask."""
        app.before_request(self.log_request)
        app.after_request(self.log_response)
    
    def log_request(self):
        """Loga informações da requisição."""
        from flask import request
        logger = get_logger("request")
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")
    
    def log_response(self, response):
        """Loga informações da resposta."""
        from flask import request
        logger = get_logger("response")
        logger.info(f"{request.method} {request.path} - {response.status_code}")
        return response
