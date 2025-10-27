import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

