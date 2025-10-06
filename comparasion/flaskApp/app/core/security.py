"""
Utilitários de segurança para autenticação e autorização Flask.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .logging import get_logger

logger = get_logger("security")

# Instância global do JWT Manager
jwt = JWTManager()


class SecurityManager:
    """Gerenciador de segurança da aplicação Flask."""
    
    @staticmethod
    def init_app(app):
        """Inicializa o gerenciador de segurança com a aplicação Flask."""
        jwt.init_app(app)
        
        # Configuração de callbacks do JWT
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({"error": "Token expirado"}), 401
        
        @jwt.invalid_token_loader
        def invalid_token_callback(error):
            return jsonify({"error": "Token inválido"}), 401
        
        @jwt.unauthorized_loader
        def missing_token_callback(error):
            return jsonify({"error": "Token de autorização necessário"}), 401
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        return check_password_hash(hashed_password, plain_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera hash da senha."""
        return generate_password_hash(password)
    
    @staticmethod
    def create_access_token(identity: str, expires_delta: Optional[timedelta] = None) -> str:
        """Cria um token JWT de acesso."""
        if expires_delta:
            expires = expires_delta
        else:
            expires = timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
        
        token = create_access_token(identity=identity, expires_delta=expires)
        logger.info(f"Token criado para usuário: {identity}")
        return token
    
    @staticmethod
    def get_current_user() -> str:
        """Retorna o usuário atual autenticado."""
        return get_jwt_identity()


def require_auth(f: Callable) -> Callable:
    """Decorator para exigir autenticação em rotas."""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f: Callable) -> Callable:
    """Decorator para exigir privilégios de administrador."""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        # Aqui você implementaria a lógica para verificar se o usuário é admin
        # Por exemplo, consultando o banco de dados
        # Por simplicidade, assumimos que usuários com 'admin' no nome são admins
        if 'admin' not in current_user.lower():
            return jsonify({"error": "Acesso negado. Privilégios de administrador necessários."}), 403
        return f(*args, **kwargs)
    return decorated_function


class RateLimiter:
    """Implementação simples de rate limiting."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """Verifica se a requisição está dentro do limite."""
        now = datetime.now()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove requisições antigas
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).seconds < window
        ]
        
        # Verifica se está dentro do limite
        if len(self.requests[key]) >= limit:
            return False
        
        # Adiciona a requisição atual
        self.requests[key].append(now)
        return True


def rate_limit(limit: int = 100, window: int = 60):
    """Decorator para rate limiting."""
    limiter = RateLimiter()
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Usa o IP como chave para rate limiting
            key = request.remote_addr
            
            if not limiter.is_allowed(key, limit, window):
                return jsonify({
                    "error": "Rate limit excedido",
                    "message": f"Máximo {limit} requisições por {window} segundos"
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Instância global do gerenciador de segurança
security_manager = SecurityManager()
