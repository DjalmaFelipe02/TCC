"""
Aplicação principal Flask - TCC APIs REST.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import time
import logging

from app.core.config import get_config
from app.core.logging import setup_logging, RequestLogger, get_logger
from app.core.database import db_manager, db
from app.core.security import security_manager
from app.api.v1.users import bp as users_bp
from app.api.v1.products import bp as products_bp

# Configurar logging
logger = get_logger("main")


def create_app(config_name=None):
    """Factory function para criar a aplicação Flask."""
    
    # Criar aplicação Flask
    app = Flask(__name__)
    
    # Configurar aplicação
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Configurar logging
    setup_logging(app)
    
    # Configurar extensões
    configure_extensions(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Configurar middleware
    configure_middleware(app)
    
    # Configurar tratamento de erros
    configure_error_handlers(app)
    
    # Configurar eventos
    configure_events(app)
    
    logger.info(f"Aplicação Flask {app.config['APP_NAME']} criada com sucesso!")
    
    return app


def configure_extensions(app):
    """Configura as extensões da aplicação."""
    
    # Banco de dados
    db_manager.init_app(app)
    
    # JWT
    jwt = JWTManager(app)
    security_manager.init_app(app)
    
    # CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    logger.info("Extensões configuradas com sucesso")


def register_blueprints(app):
    """Registra os blueprints da aplicação."""
    
    # API v1
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    
    logger.info("Blueprints registrados com sucesso")


def configure_middleware(app):
    """Configura middleware personalizado."""
    
    # Request logger
    request_logger = RequestLogger()
    request_logger.init_app(app)
    
    @app.before_request
    def before_request():
        """Executado antes de cada requisição."""
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Executado após cada requisição."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response.headers['X-Process-Time'] = str(duration)
        
        return response
    
    logger.info("Middleware configurado com sucesso")


def configure_error_handlers(app):
    """Configura handlers de erro personalizados."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handler para Bad Request."""
        return jsonify({
            'error': True,
            'status_code': 400,
            'message': 'Requisição inválida',
            'details': str(error.description) if error.description else None
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handler para Unauthorized."""
        return jsonify({
            'error': True,
            'status_code': 401,
            'message': 'Não autorizado'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handler para Forbidden."""
        return jsonify({
            'error': True,
            'status_code': 403,
            'message': 'Acesso negado'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handler para Not Found."""
        return jsonify({
            'error': True,
            'status_code': 404,
            'message': 'Recurso não encontrado'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handler para Method Not Allowed."""
        return jsonify({
            'error': True,
            'status_code': 405,
            'message': 'Método não permitido'
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handler para Rate Limit Exceeded."""
        return jsonify({
            'error': True,
            'status_code': 429,
            'message': 'Limite de requisições excedido'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handler para Internal Server Error."""
        logger.error(f"Erro interno: {error}")
        db.session.rollback()
        return jsonify({
            'error': True,
            'status_code': 500,
            'message': 'Erro interno do servidor'
        }), 500
    
    logger.info("Handlers de erro configurados com sucesso")


def configure_events(app):
    """Configura eventos da aplicação."""
    
    # Inicializar banco de dados no contexto da aplicação
    with app.app_context():
        try:
            db_manager.create_tables()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    logger.info("Eventos configurados com sucesso")


# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

def register_main_routes(app):
    """Registra as rotas principais da aplicação."""
    
    @app.route('/', methods=['GET'])
    def root():
        """Endpoint raiz da aplicação."""
        return jsonify({
            'message': f"Bem-vindo ao {app.config['APP_NAME']}!",
            'version': app.config['VERSION'],
            'description': app.config['APP_DESCRIPTION'],
            'api': {
                'users': '/api/v1/users',
                'products': '/api/v1/products',
                'health': '/health'
            },
            'features': [
                'Autenticação JWT',
                'CRUD completo de usuários',
                'CRUD completo de produtos',
                'Paginação e filtros',
                'Logging estruturado',
                'Validação de dados',
                'Tratamento de erros',
                'Rate limiting'
            ]
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint de verificação de saúde."""
        try:
            # Testar conexão com banco de dados
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            logger.error(f"Erro na conexão com banco: {e}")
            db_status = 'error'
        
        return jsonify({
            'status': 'healthy' if db_status == 'connected' else 'unhealthy',
            'service': app.config['APP_NAME'],
            'version': app.config['VERSION'],
            'timestamp': time.time(),
            'database': db_status
        })
    
    @app.route('/api/v1', methods=['GET'])
    def api_info():
        """Informações sobre a API v1."""
        return jsonify({
            'message': 'API REST v1 - Flask',
            'version': '1.0.0',
            'endpoints': {
                'users': {
                    'register': 'POST /api/v1/users/register',
                    'login': 'POST /api/v1/users/login',
                    'profile': 'GET /api/v1/users/me',
                    'update_profile': 'PUT /api/v1/users/me',
                    'list_users': 'GET /api/v1/users/',
                    'get_user': 'GET /api/v1/users/{id}',
                    'delete_user': 'DELETE /api/v1/users/{id}',
                    'search_users': 'GET /api/v1/users/search/{query}'
                },
                'products': {
                    'create': 'POST /api/v1/products/',
                    'list': 'GET /api/v1/products/',
                    'get': 'GET /api/v1/products/{id}',
                    'update': 'PUT /api/v1/products/{id}',
                    'delete': 'DELETE /api/v1/products/{id}',
                    'update_stock': 'PATCH /api/v1/products/{id}/stock',
                    'search': 'GET /api/v1/products/search/{query}',
                    'categories': 'GET /api/v1/products/categories',
                    'by_category': 'GET /api/v1/products/category/{category}',
                    'low_stock': 'GET /api/v1/products/low-stock'
                }
            },
            'authentication': 'JWT Bearer Token',
            'content_type': 'application/json'
        })


# ============================================================================
# CRIAÇÃO DA APLICAÇÃO
# ============================================================================

# Criar aplicação
app = create_app()

# Registrar rotas principais
register_main_routes(app)

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    logger.info(f"Iniciando servidor Flask em http://127.0.0.1:5000")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
