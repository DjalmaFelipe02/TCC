"""
Modelo de pedido para a aplicação Flask.
"""
from enum import Enum
from ..core.database import db, BaseModel


class OrderStatus(Enum):
    """Status possíveis de um pedido."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    """Modelo de pedido."""
    
    __tablename__ = "orders"
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    
    # Informações de entrega
    shipping_address = db.Column(db.String(500))
    zip_code = db.Column(db.String(20))
    
    # Status do pedido
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Relacionamentos
    product = db.relationship("Product", backref="orders")
    payments = db.relationship("Payment", backref="order", lazy=True)
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.final_amount})>"
    
    def calculate_totals(self, shipping_cost: float = 0.0, tax_rate: float = 0.0):
        """Calcula os totais do pedido."""
        self.total_amount = self.quantity * self.unit_price
        self.shipping_cost = shipping_cost
        self.tax_amount = self.total_amount * tax_rate
        self.final_amount = self.total_amount + self.shipping_cost + self.tax_amount
        self.save()
    
    def update_status(self, new_status: OrderStatus):
        """Atualiza o status do pedido."""
        self.status = new_status
        self.save()
    
    @classmethod
    def get_by_user(cls, user_id: int):
        """Busca pedidos por usuário."""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_by_status(cls, status: OrderStatus):
        """Busca pedidos por status."""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def create_order(cls, user_id: int, product_id: int, quantity: int, 
                    unit_price: float, shipping_address: str = None, zip_code: str = None):
        """Cria um novo pedido."""
        order = cls(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            shipping_address=shipping_address,
            zip_code=zip_code
        )
        
        # Calcula os totais iniciais
        order.calculate_totals()
        return order
