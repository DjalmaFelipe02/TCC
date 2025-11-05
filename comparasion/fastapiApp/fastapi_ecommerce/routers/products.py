from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_ecommerce.database import get_db
from fastapi_ecommerce.models import Category as CategoryModel, Product as ProductModel
from fastapi_ecommerce.schemas import CategoryCreate, CategoryUpdate, CategoryInDB, ProductCreate, ProductUpdate, ProductInDB

router = APIRouter()

# ============================================================================
# Category CRUD - DEVE VIR PRIMEIRO para evitar conflito com /{product_id}
# ============================================================================

@router.get("/categories", response_model=List[CategoryInDB])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(CategoryModel).all()
    return categories

@router.post("/categories", response_model=CategoryInDB, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = CategoryModel(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/{category_id}", response_model=CategoryInDB)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.patch("/categories/{category_id}", response_model=CategoryInDB)
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    for key, value in category_update.dict(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# ============================================================================
# Product CRUD - VEM DEPOIS para não conflitar com /categories
# ============================================================================

@router.get("/", response_model=List[ProductInDB])
def list_products(db: Session = Depends(get_db)):
    products = db.query(ProductModel).all()
    return products

@router.post("/", response_model=ProductInDB, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        # Verifica se category_id foi fornecido
        if product.category_id:
            category = db.query(CategoryModel).filter(
                CategoryModel.id == product.category_id
            ).first()
            
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Category not found with ID: {product.category_id}"
                )

        db_product = ProductModel(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )

@router.get("/{product_id}", response_model=ProductInDB)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.patch("/{product_id}", response_model=ProductInDB)
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Verifica se category_id está sendo atualizado
    if product_update.category_id:
        category = db.query(CategoryModel).filter(CategoryModel.id == product_update.category_id).first()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Category not found with ID: {product_update.category_id}"
            )

    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return None