"""
Schemas Pydantic com ID Integer
Substitua todo o conteúdo do seu arquivo schemas.py por este
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)

class UserInDB(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    stock: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None

class ProductInDB(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# ORDER SCHEMAS
# ============================================================================

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemInDB(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    user_id: int
    address: str = Field(..., min_length=1, max_length=255)

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderUpdate(BaseModel):
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    items: Optional[List[OrderItemCreate]] = None

class OrderInDB(OrderBase):
    id: int
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemInDB] = []

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PAYMENT METHOD SCHEMAS
# ============================================================================

class PaymentMethodBase(BaseModel):
    user_id: int
    type: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    is_default: bool = False
    is_active: bool = True

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(BaseModel):
    type: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class PaymentMethodInDB(PaymentMethodBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentBase(BaseModel):
    order_id: int
    payment_method_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="BRL", max_length=3)
    status: str = Field(default="pending", max_length=20)

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    payment_method_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = Field(None, max_length=20)
    payment_date: Optional[datetime] = None

class PaymentInDB(PaymentBase):
    id: int
    payment_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)