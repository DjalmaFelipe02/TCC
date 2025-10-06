"""
Configuração e gerenciamento do banco de dados.
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings
from .logging import get_logger

logger = get_logger("database")

# Configuração do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

# Metadata para migrations
metadata = MetaData()


class DatabaseManager:
    """Gerenciador do banco de dados."""
    
    @staticmethod
    def create_tables():
        """Cria todas as tabelas no banco de dados."""
        logger.info("Criando tabelas do banco de dados...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso!")
    
    @staticmethod
    def drop_tables():
        """Remove todas as tabelas do banco de dados."""
        logger.warning("Removendo todas as tabelas do banco de dados...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("Tabelas removidas!")
    
    @staticmethod
    def get_session() -> Session:
        """Retorna uma nova sessão do banco de dados."""
        return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter uma sessão do banco de dados.
    Usado como dependency injection no FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Erro na sessão do banco de dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Instância global do gerenciador
db_manager = DatabaseManager()
