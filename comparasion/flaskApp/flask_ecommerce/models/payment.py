"""
Modelos para métodos de pagamento e pagamentos no Flask.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from flask_ecommerce.db import db
from .user import User
from .order import Order

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # e.g., 'credit_card', 'pix'
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("payment_methods", lazy=True))

    def __repr__(self):
        return f"<PaymentMethod {self.name} ({self.type})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "name": self.name,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey("payment_method.id"), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default="BRL")
    status = db.Column(db.String(20), default="pending") # e.g., 'pending', 'completed', 'failed'
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", backref=db.backref("payments", lazy=True))
    payment_method = db.relationship("PaymentMethod", backref=db.backref("payments", lazy=True))

    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "payment_method_id": self.payment_method_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "created_at": self.created_at.isoformat(),
        }

