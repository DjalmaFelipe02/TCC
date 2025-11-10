# Imports originais (mantidos)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "*******")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ecommerce_fa") 

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  
    echo=False          
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
   
    from fastapi_ecommerce.models.user import User
    from fastapi_ecommerce.models.product import Category, Product
    from fastapi_ecommerce.models.order import Order, OrderItem
    from fastapi_ecommerce.models.payment import PaymentMethod, Payment
    
    User.orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    User.payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    Order.payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados MySQL inicializado com sucesso!")