"""
Testes unitários para o módulo de usuários - FastAPI.
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from main import app


# Configurar banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override da função get_db para usar banco de teste."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Fixture para loop de eventos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Fixture para criar o cliente de teste."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def async_client():
    """Fixture para cliente assíncrono."""
    Base.metadata.create_all(bind=engine)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Fixture para sessão do banco de dados."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db_session):
    """Fixture para criar usuário de exemplo."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, sample_user):
    """Fixture para headers de autenticação."""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/users/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestUserModel:
    """Testes para o modelo User."""
    
    def test_create_user(self, db_session):
        """Testa a criação de um usuário."""
        user = User(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            hashed_password=get_password_hash("newpass123")
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_verified is False
        assert verify_password("newpass123", user.hashed_password)
    
    def test_user_repr(self, db_session):
        """Testa a representação string do usuário."""
        user = User(username="testuser", email="test@example.com")
        assert repr(user) == "<User testuser>"
    
    def test_user_unique_constraints(self, db_session):
        """Testa as restrições de unicidade."""
        # Criar primeiro usuário
        user1 = User(
            username="uniqueuser",
            email="unique@example.com",
            hashed_password=get_password_hash("pass123")
        )
        db_session.add(user1)
        db_session.commit()
        
        # Tentar criar usuário com mesmo username
        user2 = User(
            username="uniqueuser",  # Username duplicado
            email="different@example.com",
            hashed_password=get_password_hash("pass123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()


class TestUserRegistration:
    """Testes para registro de usuários."""
    
    def test_register_user_success(self, client):
        """Testa o registro bem-sucedido de um usuário."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"
    
    def test_register_user_missing_fields(self, client):
        """Testa o registro com campos obrigatórios faltando."""
        user_data = {
            "username": "incompleteuser"
            # Faltando email e password
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422  # FastAPI retorna 422 para validation errors
    
    def test_register_user_duplicate_username(self, client, sample_user):
        """Testa o registro com username duplicado."""
        user_data = {
            "username": "testuser",  # Username já existe
            "email": "different@example.com",
            "password": "pass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
    
    def test_register_user_duplicate_email(self, client, sample_user):
        """Testa o registro com email duplicado."""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Email já existe
            "password": "pass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
    
    def test_register_user_invalid_email(self, client):
        """Testa o registro com email inválido."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "pass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_register_user_weak_password(self, client):
        """Testa o registro com senha fraca."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"  # Senha muito curta
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422  # FastAPI validation error


class TestUserLogin:
    """Testes para login de usuários."""
    
    def test_login_success(self, client, sample_user):
        """Testa o login bem-sucedido."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_email(self, client, sample_user):
        """Testa o login usando email."""
        login_data = {
            "username": "test@example.com",  # Usando email no campo username
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_login_invalid_credentials(self, client, sample_user):
        """Testa o login com credenciais inválidas."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Credenciais inválidas"
    
    def test_login_nonexistent_user(self, client):
        """Testa o login com usuário inexistente."""
        login_data = {
            "username": "nonexistent",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
    
    def test_login_inactive_user(self, client, db_session):
        """Testa o login com usuário inativo."""
        # Criar usuário inativo
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "pass123"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Conta desativada"


class TestUserProfile:
    """Testes para perfil de usuários."""
    
    def test_get_profile_authenticated(self, client, auth_headers):
        """Testa a obtenção do perfil com usuário autenticado."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_get_profile_unauthenticated(self, client):
        """Testa a obtenção do perfil sem autenticação."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"
    
    def test_update_profile_success(self, client, auth_headers):
        """Testa a atualização bem-sucedida do perfil."""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = client.put("/api/v1/users/update_profile", 
                             json=update_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["full_name"] == "Updated Name"
        assert data["user"]["email"] == "updated@example.com"
    
    def test_update_profile_invalid_email(self, client, auth_headers):
        """Testa a atualização com email inválido."""
        update_data = {
            "email": "invalid-email"
        }
        
        response = client.put("/api/v1/users/update_profile", 
                             json=update_data, 
                             headers=auth_headers)
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_update_profile_duplicate_email(self, client, auth_headers, db_session):
        """Testa a atualização com email duplicado."""
        # Criar outro usuário com email específico
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password=get_password_hash("pass123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        update_data = {
            "email": "other@example.com"  # Email já existe
        }
        
        response = client.put("/api/v1/users/update_profile", 
                             json=update_data, 
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True


class TestUserList:
    """Testes para listagem de usuários."""
    
    def test_list_users_unauthorized(self, client, auth_headers):
        """Testa a listagem de usuários sem permissão de admin."""
        response = client.get("/api/v1/users/", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True
    
    def test_list_users_unauthenticated(self, client):
        """Testa a listagem de usuários sem autenticação."""
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 401


class TestPasswordChange:
    """Testes para alteração de senha."""
    
    def test_change_password_success(self, client, auth_headers):
        """Testa a alteração bem-sucedida de senha."""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newtestpass123"
        }
        
        response = client.put("/api/v1/users/change_password", 
                             json=password_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Senha alterada com sucesso"
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Testa a alteração de senha com senha atual incorreta."""
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newtestpass123"
        }
        
        response = client.put("/api/v1/users/change_password", 
                             json=password_data, 
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Senha atual incorreta"
    
    def test_change_password_weak_new_password(self, client, auth_headers):
        """Testa a alteração para senha fraca."""
        password_data = {
            "current_password": "testpass123",
            "new_password": "123"  # Senha muito fraca
        }
        
        response = client.put("/api/v1/users/change_password", 
                             json=password_data, 
                             headers=auth_headers)
        
        assert response.status_code == 422  # FastAPI validation error


class TestTokenValidation:
    """Testes para validação de tokens JWT."""
    
    def test_invalid_token(self, client):
        """Testa o acesso com token inválido."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_expired_token(self, client):
        """Testa o acesso com token expirado."""
        # Este teste seria mais complexo, precisaria gerar um token expirado
        # Por simplicidade, testamos com token malformado
        headers = {"Authorization": "Bearer expired.token.here"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_missing_token(self, client):
        """Testa o acesso sem token."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_malformed_token_header(self, client):
        """Testa o acesso com header de token malformado."""
        headers = {"Authorization": "InvalidFormat token_here"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401


class TestUserSearch:
    """Testes para busca de usuários."""
    
    def test_search_users_unauthorized(self, client, auth_headers):
        """Testa a busca de usuários sem permissão de admin."""
        response = client.get("/api/v1/users/search?q=test", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True


class TestUserValidation:
    """Testes para validação de dados de usuário."""
    
    def test_username_validation(self, client):
        """Testa a validação do username."""
        # Username muito curto
        user_data = {
            "username": "ab",  # Menos de 3 caracteres
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_username_special_characters(self, client):
        """Testa username com caracteres especiais."""
        user_data = {
            "username": "user@name",  # Caracteres especiais não permitidos
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_email_format_validation(self, client):
        """Testa a validação do formato do email."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user.example.com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "username": f"user_{email.replace('@', '_').replace('.', '_')}",
                "email": email,
                "password": "testpass123"
            }
            
            response = client.post("/api/v1/users/register", json=user_data)
            assert response.status_code == 422


class TestUserStats:
    """Testes para estatísticas de usuários."""
    
    def test_user_stats_unauthorized(self, client, auth_headers):
        """Testa as estatísticas de usuários sem permissão de admin."""
        response = client.get("/api/v1/users/stats", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True


class TestRefreshToken:
    """Testes para refresh token."""
    
    def test_refresh_token_success(self, client, sample_user):
        """Testa a renovação bem-sucedida do token."""
        # Fazer login primeiro para obter refresh token
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/users/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Usar refresh token para obter novo access token
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = client.post("/api/v1/users/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Testa a renovação com refresh token inválido."""
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        response = client.post("/api/v1/users/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True


@pytest.mark.asyncio
class TestAsyncUserOperations:
    """Testes para operações assíncronas de usuários."""
    
    async def test_async_user_creation(self, async_client):
        """Testa a criação assíncrona de usuário."""
        user_data = {
            "username": "asyncuser",
            "email": "async@example.com",
            "full_name": "Async User",
            "password": "asyncpass123"
        }
        
        response = await async_client.post("/api/v1/users/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == "asyncuser"
    
    async def test_async_user_login(self, async_client):
        """Testa o login assíncrono."""
        # Primeiro registrar o usuário
        user_data = {
            "username": "asyncloginuser",
            "email": "asynclogin@example.com",
            "password": "asyncpass123"
        }
        
        await async_client.post("/api/v1/users/register", json=user_data)
        
        # Depois fazer login
        login_data = {
            "username": "asyncloginuser",
            "password": "asyncpass123"
        }
        
        response = await async_client.post("/api/v1/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
