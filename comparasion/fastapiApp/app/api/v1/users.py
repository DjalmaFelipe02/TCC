"""
Endpoints da API REST para usuários - FastAPI.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from ...core.database import get_db
from ...core.security import get_current_user, security_manager
from ...models.user import User
from ...core.logging import get_logger

logger = get_logger("users_api")
router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer()


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class UserCreate(BaseModel):
    """Modelo para criação de usuário."""
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário único")
    email: EmailStr = Field(..., description="Email do usuário")
    full_name: str = Field(..., min_length=2, max_length=100, description="Nome completo")
    password: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")


class UserUpdate(BaseModel):
    """Modelo para atualização de usuário."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Modelo de resposta do usuário."""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Modelo para login de usuário."""
    username: str = Field(..., description="Nome de usuário ou email")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    """Modelo de resposta do token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ============================================================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cria uma nova conta de usuário no sistema"
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário."""
    try:
        # Verificar se username já existe
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de usuário já existe"
            )
        
        # Verificar se email já existe
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
        
        # Criar novo usuário
        hashed_password = security_manager.get_password_hash(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Novo usuário registrado: {new_user.username}")
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de usuário",
    description="Autentica um usuário e retorna token de acesso"
)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Autentica um usuário e retorna token JWT."""
    try:
        # Buscar usuário por username ou email
        user = db.query(User).filter(
            (User.username == login_data.username) | 
            (User.email == login_data.username)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Verificar senha
        if not security_manager.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Verificar se usuário está ativo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada"
            )
        
        # Criar token
        token_data = {"sub": user.username, "user_id": user.id}
        access_token = security_manager.create_access_token(token_data)
        
        logger.info(f"Login realizado: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=1800,  # 30 minutos
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


# ============================================================================
# ENDPOINTS DE USUÁRIOS
# ============================================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil do usuário atual",
    description="Retorna informações do usuário autenticado"
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna o perfil do usuário atual."""
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar perfil do usuário: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Atualizar perfil",
    description="Atualiza informações do usuário autenticado"
)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza o perfil do usuário atual."""
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Atualizar campos fornecidos
        update_data = user_update.dict(exclude_unset=True)
        
        # Verificar se email já existe (se fornecido)
        if "email" in update_data:
            existing_email = db.query(User).filter(
                User.email == update_data["email"],
                User.id != user.id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já está em uso"
                )
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Perfil atualizado: {user.username}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuários",
    description="Lista todos os usuários (requer privilégios de admin)"
)
async def list_users(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista usuários (apenas para admins)."""
    try:
        # Verificar se é admin (simplificado)
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        # Construir query
        query = db.query(User)
        
        # Aplicar filtro de busca se fornecido
        if search:
            query = query.filter(
                (User.full_name.contains(search)) |
                (User.email.contains(search)) |
                (User.username.contains(search))
            )
        
        # Aplicar paginação
        users = query.offset(skip).limit(limit).all()
        
        logger.info(f"Lista de usuários solicitada por admin: {user.username}")
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Buscar usuário por ID",
    description="Retorna informações de um usuário específico"
)
async def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Busca um usuário por ID."""
    try:
        # Verificar se é o próprio usuário ou admin
        requesting_user = db.query(User).filter(User.id == current_user["user_id"]).first()
        
        if current_user["user_id"] != user_id and not requesting_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar usuário",
    description="Remove um usuário do sistema (apenas admins)"
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta um usuário (apenas admins)."""
    try:
        # Verificar se é admin
        requesting_user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not requesting_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Privilégios de administrador necessários."
            )
        
        # Não permitir deletar a si mesmo
        if current_user["user_id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível deletar sua própria conta"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        db.delete(user)
        db.commit()
        
        logger.info(f"Usuário deletado: {user.username} por {requesting_user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar usuário {user_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
