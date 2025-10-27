import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date
from sqlalchemy.orm import relationship
from fastapi_ecommerce.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan") 
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")

