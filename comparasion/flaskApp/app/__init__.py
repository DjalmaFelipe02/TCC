"""
Pacote principal da aplicação Flask.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.core.config import get_config
from app.core.database import db

def create_app(config_name='development'):
    """Factory function para criar a aplicação Flask."""
    app = Flask(__name__)
    
    # Configuração
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Extensões
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Registrar blueprints
    from app.api.v1.users import users_bp
    from app.api.v1.products import products_bp
    
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    
    # Criar tabelas
    with app.app_context():
        db.create_all()
    
    return app
