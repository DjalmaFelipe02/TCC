"""
Modelo de pedido para a aplicação FastAPI.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from ..core.database import Base


class OrderStatus(str, Enum):
    """Status possíveis de um pedido."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """Modelo de pedido."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    shipping_cost = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False)
    
    # Informações de entrega
    shipping_address = Column(String(500))
    zip_code = Column(String(20))
    
    # Status do pedido
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    
    # Campos de auditoria
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="orders")
    product = relationship("Product")
    payments = relationship("Payment", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.final_amount})>"
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "shipping_cost": self.shipping_cost,
            "tax_amount": self.tax_amount,
            "final_amount": self.final_amount,
            "shipping_address": self.shipping_address,
            "zip_code": self.zip_code,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def calculate_totals(self, shipping_cost: float = 0.0, tax_rate: float = 0.0):
        """Calcula os totais do pedido."""
        self.total_amount = self.quantity * self.unit_price
        self.shipping_cost = shipping_cost
        self.tax_amount = self.total_amount * tax_rate
        self.final_amount = self.total_amount + self.shipping_cost + self.tax_amount
