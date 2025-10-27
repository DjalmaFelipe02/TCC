import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: uuid.UUID

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int = 0
    category_id: Optional[uuid.UUID] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category_id: Optional[uuid.UUID] = None

class ProductInDB(ProductBase):
    id: uuid.UUID
    created_at: datetime
    category: Optional[CategoryInDB] = None

    class Config:
        orm_mode = True

