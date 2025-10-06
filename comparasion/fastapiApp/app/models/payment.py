"""
Modelo de pagamento para a aplicação FastAPI.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from ..core.database import Base


class PaymentMethod(str, Enum):
    """Métodos de pagamento disponíveis."""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    PIX = "pix"


class PaymentStatus(str, Enum):
    """Status possíveis de um pagamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    """Modelo de pagamento."""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Método e status do pagamento
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Informações do processamento
    transaction_id = Column(String(100), unique=True, index=True)
    gateway_response = Column(String(1000))  # Resposta do gateway de pagamento
    
    # Campos de auditoria
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, amount={self.amount}, status={self.status})>"
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "currency": self.currency,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "status": self.status.value if self.status else None,
            "transaction_id": self.transaction_id,
            "gateway_response": self.gateway_response,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def mark_as_completed(self, transaction_id: str, gateway_response: str = None):
        """Marca o pagamento como concluído."""
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.gateway_response = gateway_response
        self.processed_at = func.now()
    
    def mark_as_failed(self, gateway_response: str = None):
        """Marca o pagamento como falhou."""
        self.status = PaymentStatus.FAILED
        self.gateway_response = gateway_response
        self.processed_at = func.now()
