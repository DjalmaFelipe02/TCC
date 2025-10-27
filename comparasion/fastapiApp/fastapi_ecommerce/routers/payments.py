from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from fastapi_ecommerce.database import SessionLocal
from fastapi_ecommerce.models import PaymentMethod as PaymentMethodModel, Payment as PaymentModel, User as UserModel, Order as OrderModel
from fastapi_ecommerce.schemas import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodInDB, PaymentCreate, PaymentUpdate, PaymentInDB

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PaymentMethod CRUD
@router.get("/methods", response_model=List[PaymentMethodInDB])
def list_payment_methods(db: Session = Depends(get_db)):
    methods = db.query(PaymentMethodModel).all()
    return methods

@router.get("/methods/{method_id}", response_model=PaymentMethodInDB)
def get_payment_method(method_id: str, db: Session = Depends(get_db)):
    method = db.query(PaymentMethodModel).filter(PaymentMethodModel.id == method_id).first()
    if method is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return method

@router.post("/methods", response_model=PaymentMethodInDB, status_code=status.HTTP_201_CREATED)
def create_payment_method(method: PaymentMethodCreate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == method.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_method = PaymentMethodModel(**method.dict())
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method

@router.put("/methods/{method_id}", response_model=PaymentMethodInDB)
def update_payment_method(method_id: str, method_update: PaymentMethodUpdate, db: Session = Depends(get_db)):
    db_method = db.query(PaymentMethodModel).filter(PaymentMethodModel.id == method_id).first()
    if db_method is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    
    for key, value in method_update.dict(exclude_unset=True).items():
        setattr(db_method, key, value)
    
    db.commit()
    db.refresh(db_method)
    return db_method

@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(method_id: str, db: Session = Depends(get_db)):
    db_method = db.query(PaymentMethodModel).filter(PaymentMethodModel.id == method_id).first()
    if db_method is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    
    db.delete(db_method)
    db.commit()
    return {"message": "Payment method deleted"}

# Payment CRUD
@router.get("/", response_model=List[PaymentInDB])
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(PaymentModel).all()
    return payments

@router.get("/{payment_id}", response_model=PaymentInDB)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.post("/", response_model=PaymentInDB, status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == payment.order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if payment.payment_method_id:
        payment_method = db.query(PaymentMethodModel).filter(PaymentMethodModel.id == payment.payment_method_id).first()
        if payment_method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    db_payment = PaymentModel(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.put("/{payment_id}", response_model=PaymentInDB)
def update_payment(payment_id: str, payment_update: PaymentUpdate, db: Session = Depends(get_db)):
    db_payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    for key, value in payment_update.dict(exclude_unset=True).items():
        if key == "payment_date" and value is not None:
            setattr(db_payment, key, datetime.fromisoformat(value)) # Convert string to datetime object
        else:
            setattr(db_payment, key, value)
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: str, db: Session = Depends(get_db)):
    db_payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    db.delete(db_payment)
    db.commit()
    return {"message": "Payment deleted"}

