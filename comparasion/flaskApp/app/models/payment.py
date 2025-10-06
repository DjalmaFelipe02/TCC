"""
Modelo de pagamento para a aplicação Flask.
"""
from enum import Enum
from datetime import datetime
from ..core.database import db, BaseModel


class PaymentMethod(Enum):
    """Métodos de pagamento disponíveis."""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    PIX = "pix"


class PaymentStatus(Enum):
    """Status possíveis de um pagamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(BaseModel):
    """Modelo de pagamento."""
    
    __tablename__ = "payments"
    
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="BRL")
    
    # Método e status do pagamento
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Informações do processamento
    transaction_id = db.Column(db.String(100), unique=True, index=True)
    gateway_response = db.Column(db.String(1000))  # Resposta do gateway de pagamento
    
    # Campos de auditoria
    processed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, amount={self.amount}, status={self.status})>"
    
    def mark_as_completed(self, transaction_id: str, gateway_response: str = None):
        """Marca o pagamento como concluído."""
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.gateway_response = gateway_response
        self.processed_at = datetime.utcnow()
        self.save()
    
    def mark_as_failed(self, gateway_response: str = None):
        """Marca o pagamento como falhou."""
        self.status = PaymentStatus.FAILED
        self.gateway_response = gateway_response
        self.processed_at = datetime.utcnow()
        self.save()
    
    def mark_as_refunded(self, gateway_response: str = None):
        """Marca o pagamento como reembolsado."""
        self.status = PaymentStatus.REFUNDED
        self.gateway_response = gateway_response
        self.processed_at = datetime.utcnow()
        self.save()
    
    @classmethod
    def get_by_order(cls, order_id: int):
        """Busca pagamentos por pedido."""
        return cls.query.filter_by(order_id=order_id).all()
    
    @classmethod
    def get_by_status(cls, status: PaymentStatus):
        """Busca pagamentos por status."""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def get_by_transaction_id(cls, transaction_id: str):
        """Busca um pagamento pelo ID da transação."""
        return cls.query.filter_by(transaction_id=transaction_id).first()
    
    @classmethod
    def create_payment(cls, order_id: int, amount: float, payment_method: PaymentMethod, 
                      currency: str = "BRL"):
        """Cria um novo pagamento."""
        payment = cls(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            currency=currency
        )
        payment.save()
        return payment
