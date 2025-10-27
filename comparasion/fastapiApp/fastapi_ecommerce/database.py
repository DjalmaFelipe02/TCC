# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base, relationship
# from fastapi_ecommerce.core.config import DATABASE_URL

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Import all models here to ensure they are registered with Base.metadata
# from fastapi_ecommerce.models.user import User
# from fastapi_ecommerce.models.product import Category, Product
# from fastapi_ecommerce.models.order import Order, OrderItem
# from fastapi_ecommerce.models.payment import PaymentMethod, Payment

# # Define relationships for back_populates that were not defined in models directly
# User.orders = relationship("Order", back_populates="user")
# User.payment_methods = relationship("PaymentMethod", back_populates="user")

# Order.payments = relationship("Payment", back_populates="order")

# ...existing code...
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# keep check_same_thread for SQLite + FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from fastapi_ecommerce.models.user import User
    from fastapi_ecommerce.models.product import Category, Product
    from fastapi_ecommerce.models.order import Order, OrderItem
    from fastapi_ecommerce.models.payment import PaymentMethod, Payment
    User.orders = relationship("Order", back_populates="user")
    User.payment_methods = relationship("PaymentMethod", back_populates="user")

    Order.payments = relationship("Payment", back_populates="order")

    Base.metadata.create_all(bind=engine)
    # Define relationships for back_populates that were not defined in models directly
    