# Imports originais (mantidos)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os # <-- Adicionado para boas práticas (variáveis de ambiente)

# ============================================================================
# 1. MUDANÇA: CONFIGURAÇÃO DO MYSQL
# ============================================================================

# É uma boa prática de segurança NÃO deixar senhas no código.
# Use variáveis de ambiente.
# Se elas não existirem, ele usa os valores padrão (ex: 'localhost', 'root')
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "3237")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "fastapi_ecommerce_db") # Escolha um nome

# Nova DATABASE_URL para MySQL com o driver PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ============================================================================
# 2. MUDANÇA: ATUALIZAÇÃO DO ENGINE
# ============================================================================

# O 'connect_args' do SQLite ("check_same_thread") NÃO é mais necessário.
# O MySQL gerencia múltiplas threads por padrão.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Boa prática, mantém
    echo=False           # Mantenha False em produção
)

# ============================================================================
# 3. NENHUMA MUDANÇA NECESSÁRIA DAQUI PARA BAIXO
# ============================================================================
# Todo o resto do seu código funciona perfeitamente como está.

# Configuração do SessionLocal (IDÊNTICO)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base (IDÊNTICO)
Base = declarative_base()

# ============================================================================
# Dependency get_db() (IDÊNTICO)
# ============================================================================

def get_db():
    """
    Dependency que fornece uma sessão do banco de dados.
    Use como: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================================
# init_db() (IDÊNTICO)
# ============================================================================
# Esta função agora vai criar as tabelas no SEU BANCO MYSQL
# quando for chamada.

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas"""
    from fastapi_ecommerce.models.user import User
    from fastapi_ecommerce.models.product import Category, Product
    from fastapi_ecommerce.models.order import Order, OrderItem
    from fastapi_ecommerce.models.payment import PaymentMethod, Payment
    
    # Define relationships dinâmicos (se necessário)
    User.orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    User.payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    Order.payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados MySQL inicializado com sucesso!")