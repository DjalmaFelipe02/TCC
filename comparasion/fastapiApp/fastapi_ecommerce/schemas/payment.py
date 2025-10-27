import uuid
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
from pydantic import BaseModel

class PaymentMethodBase(BaseModel):
    user_id: uuid.UUID
    type: Literal[
        "credit_card",
        "debit_card",
        "paypal",
        "pix",
        "bank_transfer",
        "boleto",
    ]
    name: str
    is_default: bool = False
    is_active: bool = True

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(PaymentMethodBase):
    user_id: Optional[uuid.UUID] = None
    type: Optional[Literal[
        "credit_card",
        "debit_card",
        "paypal",
        "pix",
        "bank_transfer",
        "boleto",
    ]] = None
    name: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class PaymentMethodInDB(PaymentMethodBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

class PaymentBase(BaseModel):
    order_id: uuid.UUID
    payment_method_id: Optional[uuid.UUID] = None
    amount: Decimal
    currency: str = "BRL"
    status: Literal["pending", "completed", "failed"] = "pending"
    payment_date: Optional[datetime] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    order_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = None
    status: Optional[Literal["pending", "completed", "failed"]] = None
    payment_date: Optional[datetime] = None

class PaymentInDB(PaymentBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

