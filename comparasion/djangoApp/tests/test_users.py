"""
Testes unitários para o app de usuários - Django.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class UserModelTest(TestCase):
    """
    Testes para o modelo User.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Testa a criação de um usuário."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.full_name, 'Test User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)
    
    def test_create_superuser(self):
        """Testa a criação de um superusuário."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(user.username, 'admin')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
    
    def test_user_str_representation(self):
        """Testa a representação string do usuário."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')
    
    def test_user_email_unique(self):
        """Testa se o email é único."""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',  # Email duplicado
                password='testpass123'
            )
    
    def test_user_username_unique(self):
        """Testa se o username é único."""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser',  # Username duplicado
                email='test2@example.com',
                password='testpass123'
            )


class UserRegistrationAPITest(APITestCase):
    """
    Testes para a API de registro de usuários.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        self.register_url = '/api/v1/users/register/'
        self.valid_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
    
    def test_register_user_success(self):
        """Testa o registro bem-sucedido de um usuário."""
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Verificar se o usuário foi criado no banco
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.full_name, 'New User')
    
    def test_register_user_invalid_data(self):
        """Testa o registro com dados inválidos."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'  # Email inválido
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertIn('details', response.data)
    
    def test_register_user_password_mismatch(self):
        """Testa o registro com senhas que não coincidem."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_register_user_duplicate_username(self):
        """Testa o registro com username duplicado."""
        # Criar usuário primeiro
        User.objects.create_user(
            username='newuser',
            email='existing@example.com',
            password='pass123'
        )
        
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_register_user_duplicate_email(self):
        """Testa o registro com email duplicado."""
        # Criar usuário primeiro
        User.objects.create_user(
            username='existing',
            email='newuser@example.com',
            password='pass123'
        )
        
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])


class UserLoginAPITest(APITestCase):
    """
    Testes para a API de login de usuários.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        self.login_url = '/api/v1/users/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
    
    def test_login_with_username_success(self):
        """Testa o login bem-sucedido com username."""
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
    
    def test_login_with_email_success(self):
        """Testa o login bem-sucedido com email."""
        login_data = {
            'username': 'test@example.com',  # Usando email no campo username
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_login_invalid_credentials(self):
        """Testa o login com credenciais inválidas."""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['message'], 'Credenciais inválidas')
    
    def test_login_inactive_user(self):
        """Testa o login com usuário inativo."""
        self.user.is_active = False
        self.user.save()
        
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['message'], 'Conta desativada')
    
    def test_login_nonexistent_user(self):
        """Testa o login com usuário inexistente."""
        login_data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data['error'])


class UserProfileAPITest(APITestCase):
    """
    Testes para a API de perfil de usuários.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # URLs
        self.profile_url = '/api/v1/users/me/'
        self.update_profile_url = '/api/v1/users/update_profile/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_profile_authenticated(self):
        """Testa a obtenção do perfil com usuário autenticado."""
        self.authenticate_user(self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_get_profile_unauthenticated(self):
        """Testa a obtenção do perfil sem autenticação."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile_success(self):
        """Testa a atualização bem-sucedida do perfil."""
        self.authenticate_user(self.user)
        
        update_data = {
            'full_name': 'Updated Name',
            'email': 'updated@example.com'
        }
        
        response = self.client.put(self.update_profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se os dados foram atualizados
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_update_profile_duplicate_email(self):
        """Testa a atualização com email duplicado."""
        # Criar outro usuário com email específico
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        
        self.authenticate_user(self.user)
        
        update_data = {
            'email': 'other@example.com'  # Email já existe
        }
        
        response = self.client.put(self.update_profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])


class UserListAPITest(APITestCase):
    """
    Testes para a API de listagem de usuários.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.list_url = '/api/v1/users/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_users_as_admin(self):
        """Testa a listagem de usuários como admin."""
        self.authenticate_user(self.admin_user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('users', response.data)
        self.assertGreaterEqual(len(response.data['users']), 2)  # Pelo menos admin e testuser
    
    def test_list_users_as_regular_user(self):
        """Testa a listagem de usuários como usuário comum."""
        self.authenticate_user(self.user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_list_users_unauthenticated(self):
        """Testa a listagem de usuários sem autenticação."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_search_users(self):
        """Testa a busca de usuários."""
        self.authenticate_user(self.admin_user)
        
        # Criar usuários para busca
        User.objects.create_user(
            username='searchuser',
            email='search@example.com',
            full_name='Search User',
            password='pass123'
        )
        
        search_url = '/api/v1/users/search/?q=search'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertGreater(response.data['count'], 0)
    
    def test_user_stats(self):
        """Testa as estatísticas de usuários."""
        self.authenticate_user(self.admin_user)
        
        stats_url = '/api/v1/users/stats/'
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('stats', response.data)
        self.assertIn('total_users', response.data['stats'])
        self.assertIn('active_users', response.data['stats'])


class UserDeletionAPITest(APITestCase):
    """
    Testes para a API de exclusão de usuários.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='pass123'
        )
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_delete_user_as_admin(self):
        """Testa a exclusão de usuário como admin."""
        self.authenticate_user(self.admin_user)
        
        delete_url = f'/api/v1/users/{self.target_user.id}/'
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o usuário foi deletado
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.target_user.id)
    
    def test_delete_user_as_regular_user(self):
        """Testa a exclusão de usuário como usuário comum."""
        self.authenticate_user(self.user)
        
        delete_url = f'/api/v1/users/{self.target_user.id}/'
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_delete_self_as_admin(self):
        """Testa a tentativa de auto-exclusão como admin."""
        self.authenticate_user(self.admin_user)
        
        delete_url = f'/api/v1/users/{self.admin_user.id}/'
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertIn('própria conta', response.data['message'])
    
    def test_delete_nonexistent_user(self):
        """Testa a exclusão de usuário inexistente."""
        self.authenticate_user(self.admin_user)
        
        delete_url = '/api/v1/users/99999/'
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['error'])
