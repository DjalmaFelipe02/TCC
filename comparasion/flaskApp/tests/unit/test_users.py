"""
Testes unitários para o módulo de usuários - Flask.
"""
import pytest
import json
from app import create_app
from app.core.database import db
from app.models.user import User
from werkzeug.security import check_password_hash


@pytest.fixture
def app():
    """Fixture para criar a aplicação Flask para testes."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture para criar o cliente de teste."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Fixture para criar headers de autenticação."""
    # Criar usuário de teste
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'full_name': 'Test User',
        'password': 'testpass123'
    }
    
    # Registrar usuário
    client.post('/api/v1/users/register', 
                data=json.dumps(user_data),
                content_type='application/json')
    
    # Fazer login
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    response = client.post('/api/v1/users/login',
                          data=json.dumps(login_data),
                          content_type='application/json')
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}


class TestUserModel:
    """Testes para o modelo User."""
    
    def test_create_user(self, app):
        """Testa a criação de um usuário."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User'
            )
            user.set_password('testpass123')
            
            db.session.add(user)
            db.session.commit()
            
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.full_name == 'Test User'
            assert user.is_active is True
            assert user.is_verified is False
            assert check_password_hash(user.password_hash, 'testpass123')
    
    def test_user_repr(self, app):
        """Testa a representação string do usuário."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            assert repr(user) == '<User testuser>'
    
    def test_check_password(self, app):
        """Testa a verificação de senha."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass123')
            
            assert user.check_password('testpass123') is True
            assert user.check_password('wrongpass') is False
    
    def test_user_to_dict(self, app):
        """Testa a conversão do usuário para dicionário."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User'
            )
            user.set_password('testpass123')
            
            user_dict = user.to_dict()
            
            assert user_dict['username'] == 'testuser'
            assert user_dict['email'] == 'test@example.com'
            assert user_dict['full_name'] == 'Test User'
            assert 'password_hash' not in user_dict
            assert 'id' in user_dict


class TestUserRegistration:
    """Testes para registro de usuários."""
    
    def test_register_user_success(self, client):
        """Testa o registro bem-sucedido de um usuário."""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'newpass123'
        }
        
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert 'access_token' in data
        assert data['user']['username'] == 'newuser'
    
    def test_register_user_missing_fields(self, client):
        """Testa o registro com campos obrigatórios faltando."""
        user_data = {
            'username': 'incompleteuser'
            # Faltando email e password
        }
        
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_register_user_duplicate_username(self, client):
        """Testa o registro com username duplicado."""
        user_data = {
            'username': 'duplicateuser',
            'email': 'user1@example.com',
            'password': 'pass123'
        }
        
        # Primeiro registro
        client.post('/api/v1/users/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Segundo registro com mesmo username
        user_data['email'] = 'user2@example.com'
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_register_user_duplicate_email(self, client):
        """Testa o registro com email duplicado."""
        user_data = {
            'username': 'user1',
            'email': 'duplicate@example.com',
            'password': 'pass123'
        }
        
        # Primeiro registro
        client.post('/api/v1/users/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Segundo registro com mesmo email
        user_data['username'] = 'user2'
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_register_user_invalid_email(self, client):
        """Testa o registro com email inválido."""
        user_data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'pass123'
        }
        
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True


class TestUserLogin:
    """Testes para login de usuários."""
    
    def test_login_success(self, client):
        """Testa o login bem-sucedido."""
        # Registrar usuário primeiro
        user_data = {
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'loginpass123'
        }
        
        client.post('/api/v1/users/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Tentar fazer login
        login_data = {
            'username': 'loginuser',
            'password': 'loginpass123'
        }
        
        response = client.post('/api/v1/users/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data
        assert 'user' in data
    
    def test_login_with_email(self, client):
        """Testa o login usando email."""
        # Registrar usuário primeiro
        user_data = {
            'username': 'emailuser',
            'email': 'email@example.com',
            'password': 'emailpass123'
        }
        
        client.post('/api/v1/users/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Fazer login com email
        login_data = {
            'username': 'email@example.com',  # Usando email no campo username
            'password': 'emailpass123'
        }
        
        response = client.post('/api/v1/users/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_login_invalid_credentials(self, client):
        """Testa o login com credenciais inválidas."""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        
        response = client.post('/api/v1/users/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_login_missing_fields(self, client):
        """Testa o login com campos faltando."""
        login_data = {
            'username': 'testuser'
            # Faltando password
        }
        
        response = client.post('/api/v1/users/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True


class TestUserProfile:
    """Testes para perfil de usuários."""
    
    def test_get_profile_authenticated(self, client, auth_headers):
        """Testa a obtenção do perfil com usuário autenticado."""
        response = client.get('/api/v1/users/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == 'testuser'
    
    def test_get_profile_unauthenticated(self, client):
        """Testa a obtenção do perfil sem autenticação."""
        response = client.get('/api/v1/users/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_update_profile_success(self, client, auth_headers):
        """Testa a atualização bem-sucedida do perfil."""
        update_data = {
            'full_name': 'Updated Name',
            'email': 'updated@example.com'
        }
        
        response = client.put('/api/v1/users/update_profile',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['full_name'] == 'Updated Name'
        assert data['user']['email'] == 'updated@example.com'
    
    def test_update_profile_invalid_email(self, client, auth_headers):
        """Testa a atualização com email inválido."""
        update_data = {
            'email': 'invalid-email'
        }
        
        response = client.put('/api/v1/users/update_profile',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True


class TestUserList:
    """Testes para listagem de usuários."""
    
    def test_list_users_unauthorized(self, client, auth_headers):
        """Testa a listagem de usuários sem permissão de admin."""
        response = client.get('/api/v1/users/', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_list_users_unauthenticated(self, client):
        """Testa a listagem de usuários sem autenticação."""
        response = client.get('/api/v1/users/')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True


class TestUserSearch:
    """Testes para busca de usuários."""
    
    def test_search_users_unauthorized(self, client, auth_headers):
        """Testa a busca de usuários sem permissão de admin."""
        response = client.get('/api/v1/users/search?q=test', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] is True


class TestPasswordChange:
    """Testes para alteração de senha."""
    
    def test_change_password_success(self, client, auth_headers):
        """Testa a alteração bem-sucedida de senha."""
        password_data = {
            'current_password': 'testpass123',
            'new_password': 'newtestpass123'
        }
        
        response = client.put('/api/v1/users/change_password',
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Testa a alteração de senha com senha atual incorreta."""
        password_data = {
            'current_password': 'wrongpass',
            'new_password': 'newtestpass123'
        }
        
        response = client.put('/api/v1/users/change_password',
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_change_password_missing_fields(self, client, auth_headers):
        """Testa a alteração de senha com campos faltando."""
        password_data = {
            'current_password': 'testpass123'
            # Faltando new_password
        }
        
        response = client.put('/api/v1/users/change_password',
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True


class TestUserValidation:
    """Testes para validação de dados de usuário."""
    
    def test_username_validation(self, client):
        """Testa a validação do username."""
        # Username muito curto
        user_data = {
            'username': 'ab',  # Menos de 3 caracteres
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_password_validation(self, client):
        """Testa a validação da senha."""
        # Senha muito curta
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'  # Menos de 6 caracteres
        }
        
        response = client.post('/api/v1/users/register',
                              data=json.dumps(user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True


class TestTokenValidation:
    """Testes para validação de tokens JWT."""
    
    def test_invalid_token(self, client):
        """Testa o acesso com token inválido."""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        response = client.get('/api/v1/users/me', headers=headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_missing_token(self, client):
        """Testa o acesso sem token."""
        response = client.get('/api/v1/users/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_malformed_token_header(self, client):
        """Testa o acesso com header de token malformado."""
        headers = {'Authorization': 'InvalidFormat token_here'}
        
        response = client.get('/api/v1/users/me', headers=headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
