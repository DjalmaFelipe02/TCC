"""
Endpoints da API REST para produtos - FastAPI.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.product import Product
from ...models.user import User
from ...core.logging import get_logger

logger = get_logger("products_api")
router = APIRouter(prefix="/products", tags=["Products"])


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class ProductCreate(BaseModel):
    """Modelo para criação de produto."""
    name: str = Field(..., min_length=2, max_length=200, description="Nome do produto")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    price: Decimal = Field(..., gt=0, description="Preço do produto")
    stock_quantity: int = Field(0, ge=0, description="Quantidade em estoque")
    sku: Optional[str] = Field(None, max_length=50, description="Código SKU único")
    category: Optional[str] = Field(None, max_length=100, description="Categoria do produto")


class ProductUpdate(BaseModel):
    """Modelo para atualização de produto."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Modelo de resposta do produto."""
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    sku: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    is_in_stock: bool

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Modelo de resposta para lista de produtos."""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int


class StockUpdate(BaseModel):
    """Modelo para atualização de estoque."""
    quantity: int = Field(..., description="Quantidade a adicionar (positivo) ou remover (negativo)")
    reason: Optional[str] = Field(None, description="Motivo da alteração")


# ============================================================================
# ENDPOINTS DE PRODUTOS
# ============================================================================

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto",
    description="Cria um novo produto no sistema"
)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo produto."""
    try:
        # Verificar se é admin
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        # Verificar se SKU já existe (se fornecido)
        if product_data.sku:
            existing_sku = db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU já existe"
                )
        
        # Criar produto
        new_product = Product(**product_data.dict())
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        logger.info(f"Produto criado: {new_product.name} por {user.username}")
        
        return new_product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Listar produtos",
    description="Lista produtos com paginação e filtros"
)
async def list_products(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou descrição"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    active_only: bool = Query(True, description="Apenas produtos ativos"),
    in_stock_only: bool = Query(False, description="Apenas produtos em estoque"),
    db: Session = Depends(get_db)
):
    """Lista produtos com filtros e paginação."""
    try:
        # Construir query base
        query = db.query(Product)
        
        # Aplicar filtros
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)
        
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            query = query.filter(
                (Product.name.contains(search)) |
                (Product.description.contains(search))
            )
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        # Calcular número de páginas
        pages = (total + per_page - 1) // per_page
        
        logger.info(f"Lista de produtos solicitada - Página {page}, Total: {total}")
        
        return ProductListResponse(
            products=products,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/categories",
    response_model=List[str],
    summary="Listar categorias",
    description="Retorna lista de categorias disponíveis"
)
async def list_categories(db: Session = Depends(get_db)):
    """Lista todas as categorias de produtos."""
    try:
        categories = db.query(Product.category).filter(
            Product.category.isnot(None),
            Product.is_active == True
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return sorted(category_list)
        
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Buscar produto por ID",
    description="Retorna informações detalhadas de um produto"
)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Busca um produto por ID."""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar produto {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Atualizar produto",
    description="Atualiza informações de um produto"
)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um produto."""
    try:
        # Verificar se é admin
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        # Verificar SKU único (se fornecido)
        update_data = product_update.dict(exclude_unset=True)
        if "sku" in update_data and update_data["sku"]:
            existing_sku = db.query(Product).filter(
                Product.sku == update_data["sku"],
                Product.id != product_id
            ).first()
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU já existe"
                )
        
        # Atualizar campos
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        logger.info(f"Produto atualizado: {product.name} por {user.username}")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {product_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar produto",
    description="Remove um produto do sistema"
)
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta um produto."""
    try:
        # Verificar se é admin
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        db.delete(product)
        db.commit()
        
        logger.info(f"Produto deletado: {product.name} por {user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar produto {product_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse,
    summary="Atualizar estoque",
    description="Atualiza a quantidade em estoque de um produto"
)
async def update_stock(
    product_id: int,
    stock_update: StockUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza o estoque de um produto."""
    try:
        # Verificar se é admin
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        # Calcular novo estoque
        new_stock = product.stock_quantity + stock_update.quantity
        
        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estoque não pode ser negativo"
            )
        
        # Atualizar estoque
        old_stock = product.stock_quantity
        product.stock_quantity = new_stock
        
        db.commit()
        db.refresh(product)
        
        logger.info(
            f"Estoque atualizado: {product.name} - "
            f"{old_stock} → {new_stock} ({stock_update.quantity:+d}) "
            f"por {user.username}"
        )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar estoque do produto {product_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/search/{query}",
    response_model=List[ProductResponse],
    summary="Buscar produtos",
    description="Busca produtos por nome, descrição ou SKU"
)
async def search_products(
    query: str,
    limit: int = Query(10, ge=1, le=50, description="Limite de resultados"),
    db: Session = Depends(get_db)
):
    """Busca produtos por texto."""
    try:
        products = db.query(Product).filter(
            (Product.name.contains(query)) |
            (Product.description.contains(query)) |
            (Product.sku.contains(query)),
            Product.is_active == True
        ).limit(limit).all()
        
        logger.info(f"Busca realizada: '{query}' - {len(products)} resultados")
        
        return products
        
    except Exception as e:
        logger.error(f"Erro na busca de produtos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
