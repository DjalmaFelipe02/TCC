from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal

from fastapi_ecommerce.database import get_db
from fastapi_ecommerce.models import Order as OrderModel, OrderItem as OrderItemModel, Product as ProductModel, User as UserModel
from fastapi_ecommerce.schemas import OrderCreate, OrderUpdate, OrderInDB, OrderItemCreate

router = APIRouter()

@router.get("/", response_model=List[OrderInDB])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(OrderModel).options(joinedload(OrderModel.items).joinedload(OrderItemModel.product)).all()
    return orders

@router.get("/{order_id}", response_model=OrderInDB)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).options(
        joinedload(OrderModel.items).joinedload(OrderItemModel.product)
    ).filter(OrderModel.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

@router.post("/", response_model=OrderInDB, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(UserModel).filter(UserModel.id == order_data.user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        db_order = OrderModel(
            user_id=order_data.user_id,
            address=order_data.address,
            total_amount=Decimal("0.00")
        )
        db.add(db_order)
        db.flush()

        total_amount = Decimal("0.00")
        for item_data in order_data.items:
            product = db.query(ProductModel).filter(ProductModel.id == item_data.product_id).first()
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Product with ID {item_data.product_id} not found"
                )
            
            if item_data.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Quantity must be positive"
                )

            # Validação de estoque
            if product.stock < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock}, Requested: {item_data.quantity}"
                )

            db_order_item = OrderItemModel(
                order_id=db_order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity
            )
            db.add(db_order_item)
            
            # Atualiza estoque
            product.stock -= item_data.quantity
            total_amount += product.price * item_data.quantity
        
        db_order.total_amount = total_amount
        db.commit()
        db.refresh(db_order)
        return db_order
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )

@router.patch("/{order_id}", response_model=OrderInDB)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    try:
        db_order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if db_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        if order_update.address is not None:
            db_order.address = order_update.address

        if order_update.items is not None:
            # Restaura estoque dos itens antigos
            old_items = db.query(OrderItemModel).filter(OrderItemModel.order_id == order_id).all()
            for old_item in old_items:
                product = db.query(ProductModel).filter(ProductModel.id == old_item.product_id).first()
                if product:
                    product.stock += old_item.quantity
            
            # Deleta itens antigos
            db.query(OrderItemModel).filter(OrderItemModel.order_id == order_id).delete()
            db.flush()

            total_amount = Decimal("0.00")
            for item_data in order_update.items:
                product = db.query(ProductModel).filter(ProductModel.id == item_data.product_id).first()
                if product is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail=f"Product with ID {item_data.product_id} not found"
                    )
                
                if item_data.quantity <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail="Quantity must be positive"
                    )

                # Validação de estoque
                if product.stock < item_data.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock}, Requested: {item_data.quantity}"
                    )

                db_order_item = OrderItemModel(
                    order_id=db_order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity
                )
                db.add(db_order_item)
                
                # Atualiza estoque
                product.stock -= item_data.quantity
                total_amount += product.price * item_data.quantity
                
            db_order.total_amount = total_amount

        db.commit()
        db.refresh(db_order)
        return db_order
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order: {str(e)}"
        )

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        db_order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if db_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        # Restaura estoque ao deletar pedido
        order_items = db.query(OrderItemModel).filter(OrderItemModel.order_id == order_id).all()
        for item in order_items:
            product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
            if product:
                product.stock += item.quantity
        
        db.delete(db_order)
        db.commit()
        return None
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting order: {str(e)}"
        )