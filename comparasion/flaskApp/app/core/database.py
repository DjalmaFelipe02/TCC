"""
Configuração e gerenciamento do banco de dados Flask.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask
from .logging import get_logger

logger = get_logger("database")

# Instâncias globais
db = SQLAlchemy()
migrate = Migrate()


class DatabaseManager:
    """Gerenciador do banco de dados Flask."""
    
    @staticmethod
    def init_app(app: Flask):
        """Inicializa o banco de dados com a aplicação Flask."""
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Configuração de eventos do SQLAlchemy
        with app.app_context():
            logger.info("Criando tabelas do banco de dados...")
            db.create_all()
            logger.info("Tabelas criadas com sucesso!")
        
        logger.info(f"Banco de dados configurado: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    @staticmethod
    def create_tables():
        """Cria todas as tabelas no banco de dados."""
        logger.info("Criando tabelas do banco de dados...")
        db.create_all()
        logger.info("Tabelas criadas com sucesso!")
    
    @staticmethod
    def drop_tables():
        """Remove todas as tabelas do banco de dados."""
        logger.warning("Removendo todas as tabelas do banco de dados...")
        db.drop_all()
        logger.warning("Tabelas removidas!")
    
    @staticmethod
    def get_session():
        """Retorna a sessão atual do banco de dados."""
        return db.session


class BaseModel(db.Model):
    """Modelo base com funcionalidades comuns."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    def save(self):
        """Salva o modelo no banco de dados."""
        try:
            db.session.add(self)
            db.session.commit()
            logger.debug(f"Modelo {self.__class__.__name__} salvo com ID: {self.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar modelo {self.__class__.__name__}: {e}")
            raise
    
    def delete(self):
        """Remove o modelo do banco de dados."""
        try:
            db.session.delete(self)
            db.session.commit()
            logger.debug(f"Modelo {self.__class__.__name__} removido com ID: {self.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao remover modelo {self.__class__.__name__}: {e}")
            raise
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def get_by_id(cls, id):
        """Busca um modelo pelo ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """Retorna todos os registros do modelo."""
        return cls.query.all()


# Instância global do gerenciador
db_manager = DatabaseManager()
