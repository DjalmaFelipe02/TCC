from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuração do engine com otimizações para SQLite
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,  # Necessário para FastAPI com SQLite
        "timeout": 30  # Timeout para evitar locks
    },
    pool_pre_ping=True,  # Verifica conexões antes de usar
    echo=False  # Mude para True para debug de SQL
)

# Configuração do SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # ← CRÍTICO: Evita problemas de sessão entre requests
)

Base = declarative_base()

# ============================================================================
# Dependency get_db() - IMPORTAR ESTA FUNÇÃO EM TODOS OS ROUTERS
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

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas"""
    from fastapi_ecommerce.models.user import User
    from fastapi_ecommerce.models.product import Category, Product
    from fastapi_ecommerce.models.order import Order, OrderItem
    from fastapi_ecommerce.models.payment import PaymentMethod, Payment
    
    # Define relationships dinâmicos (se necessário)
    # Nota: Idealmente esses relationships deveriam estar nos models
    User.orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    User.payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    Order.payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso!")