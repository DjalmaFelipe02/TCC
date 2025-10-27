import uuid
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel

from fastapi_ecommerce.schemas.product import ProductInDB

class OrderItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemInDB(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    product: ProductInDB

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: uuid.UUID
    address: str
    total_amount: Decimal = Decimal('0.00')

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    address: Optional[str] = None
    items: Optional[List[OrderItemCreate]] = None

class OrderInDB(OrderBase):
    id: uuid.UUID
    created_at: datetime
    items: List[OrderItemInDB]

    class Config:
        orm_mode = True

