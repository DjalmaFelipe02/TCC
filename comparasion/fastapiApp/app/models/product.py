"""
Modelo de produto para a aplicação FastAPI.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Product(Base):
    """Modelo de produto."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    sku = Column(String(50), unique=True, index=True)
    category = Column(String(100), index=True)
    is_active = Column(Boolean, default=True)
    
    # Campos de auditoria
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "sku": self.sku,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_in_stock(self) -> bool:
        """Verifica se o produto está em estoque."""
        return self.stock_quantity > 0
    
    def reduce_stock(self, quantity: int) -> bool:
        """Reduz o estoque do produto."""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False
    
    def increase_stock(self, quantity: int):
        """Aumenta o estoque do produto."""
        self.stock_quantity += quantity
