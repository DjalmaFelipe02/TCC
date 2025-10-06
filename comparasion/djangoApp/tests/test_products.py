"""
Testes unitários para o app de produtos - Django.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from tcc_django.apps.products.models import Product

User = get_user_model()


class ProductModelTest(TestCase):
    """
    Testes para o modelo Product.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.product_data = {
            'name': 'Produto Teste',
            'description': 'Descrição do produto teste',
            'price': Decimal('99.99'),
            'stock_quantity': 10,
            'sku': 'PROD001',
            'category': 'Eletrônicos'
        }
    
    def test_create_product(self):
        """Testa a criação de um produto."""
        product = Product.objects.create(**self.product_data)
        
        self.assertEqual(product.name, 'Produto Teste')
        self.assertEqual(product.description, 'Descrição do produto teste')
        self.assertEqual(product.price, Decimal('99.99'))
        self.assertEqual(product.stock_quantity, 10)
        self.assertEqual(product.sku, 'PROD001')
        self.assertEqual(product.category, 'Eletrônicos')
        self.assertTrue(product.is_active)
        self.assertTrue(product.is_in_stock)
    
    def test_product_str_representation(self):
        """Testa a representação string do produto."""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(str(product), 'Produto Teste')
    
    def test_product_is_in_stock_property(self):
        """Testa a propriedade is_in_stock."""
        # Produto com estoque
        product_with_stock = Product.objects.create(**self.product_data)
        self.assertTrue(product_with_stock.is_in_stock)
        
        # Produto sem estoque
        product_data_no_stock = self.product_data.copy()
        product_data_no_stock['stock_quantity'] = 0
        product_data_no_stock['sku'] = 'PROD002'
        product_no_stock = Product.objects.create(**product_data_no_stock)
        self.assertFalse(product_no_stock.is_in_stock)
    
    def test_product_sku_unique(self):
        """Testa se o SKU é único."""
        Product.objects.create(**self.product_data)
        
        # Tentar criar produto com mesmo SKU
        duplicate_data = self.product_data.copy()
        duplicate_data['name'] = 'Produto Duplicado'
        
        with self.assertRaises(Exception):
            Product.objects.create(**duplicate_data)
    
    def test_product_price_validation(self):
        """Testa a validação do preço."""
        # Preço negativo deve falhar
        invalid_data = self.product_data.copy()
        invalid_data['price'] = Decimal('-10.00')
        invalid_data['sku'] = 'PROD003'
        
        with self.assertRaises(Exception):
            product = Product(**invalid_data)
            product.full_clean()
    
    def test_product_stock_validation(self):
        """Testa a validação do estoque."""
        # Estoque negativo deve falhar
        invalid_data = self.product_data.copy()
        invalid_data['stock_quantity'] = -5
        invalid_data['sku'] = 'PROD004'
        
        with self.assertRaises(Exception):
            product = Product(**invalid_data)
            product.full_clean()


class ProductAPITest(APITestCase):
    """
    Testes para a API de produtos.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        # Criar usuários
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
        
        # Criar produtos de teste
        self.product1 = Product.objects.create(
            name='Produto 1',
            description='Descrição do produto 1',
            price=Decimal('50.00'),
            stock_quantity=20,
            sku='PROD001',
            category='Categoria A'
        )
        
        self.product2 = Product.objects.create(
            name='Produto 2',
            description='Descrição do produto 2',
            price=Decimal('75.00'),
            stock_quantity=0,
            sku='PROD002',
            category='Categoria B'
        )
        
        # URLs
        self.products_url = '/api/v1/products/'
        self.product_detail_url = f'/api/v1/products/{self.product1.id}/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_products_public(self):
        """Testa a listagem pública de produtos."""
        response = self.client.get(self.products_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('products', response.data)
        self.assertEqual(len(response.data['products']), 2)
    
    def test_list_products_with_filters(self):
        """Testa a listagem de produtos com filtros."""
        # Filtrar por categoria
        response = self.client.get(f'{self.products_url}?category=Categoria A')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['category'], 'Categoria A')
        
        # Filtrar apenas produtos em estoque
        response = self.client.get(f'{self.products_url}?in_stock_only=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertTrue(response.data['products'][0]['is_in_stock'])
    
    def test_search_products(self):
        """Testa a busca de produtos."""
        response = self.client.get(f'{self.products_url}?search=Produto 1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['name'], 'Produto 1')
    
    def test_get_product_detail(self):
        """Testa a obtenção de detalhes de um produto."""
        response = self.client.get(self.product_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['product']['name'], 'Produto 1')
        self.assertEqual(response.data['product']['sku'], 'PROD001')
    
    def test_get_nonexistent_product(self):
        """Testa a obtenção de produto inexistente."""
        response = self.client.get('/api/v1/products/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['error'])
    
    def test_create_product_as_admin(self):
        """Testa a criação de produto como admin."""
        self.authenticate_user(self.admin_user)
        
        product_data = {
            'name': 'Novo Produto',
            'description': 'Descrição do novo produto',
            'price': '120.00',
            'stock_quantity': 15,
            'sku': 'PROD003',
            'category': 'Nova Categoria'
        }
        
        response = self.client.post(self.products_url, product_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['product']['name'], 'Novo Produto')
        
        # Verificar se o produto foi criado no banco
        product = Product.objects.get(sku='PROD003')
        self.assertEqual(product.name, 'Novo Produto')
    
    def test_create_product_as_regular_user(self):
        """Testa a criação de produto como usuário comum."""
        self.authenticate_user(self.user)
        
        product_data = {
            'name': 'Produto Não Autorizado',
            'price': '50.00',
            'sku': 'PROD004'
        }
        
        response = self.client.post(self.products_url, product_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_create_product_duplicate_sku(self):
        """Testa a criação de produto com SKU duplicado."""
        self.authenticate_user(self.admin_user)
        
        product_data = {
            'name': 'Produto Duplicado',
            'price': '50.00',
            'sku': 'PROD001'  # SKU já existe
        }
        
        response = self.client.post(self.products_url, product_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_update_product_as_admin(self):
        """Testa a atualização de produto como admin."""
        self.authenticate_user(self.admin_user)
        
        update_data = {
            'name': 'Produto 1 Atualizado',
            'price': '60.00'
        }
        
        response = self.client.put(self.product_detail_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['product']['name'], 'Produto 1 Atualizado')
        
        # Verificar se foi atualizado no banco
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Produto 1 Atualizado')
        self.assertEqual(self.product1.price, Decimal('60.00'))
    
    def test_update_product_as_regular_user(self):
        """Testa a atualização de produto como usuário comum."""
        self.authenticate_user(self.user)
        
        update_data = {'name': 'Tentativa de Atualização'}
        
        response = self.client.put(self.product_detail_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_delete_product_as_admin(self):
        """Testa a exclusão de produto como admin."""
        self.authenticate_user(self.admin_user)
        
        response = self.client.delete(self.product_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o produto foi deletado
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=self.product1.id)
    
    def test_delete_product_as_regular_user(self):
        """Testa a exclusão de produto como usuário comum."""
        self.authenticate_user(self.user)
        
        response = self.client.delete(self.product_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])


class ProductStockAPITest(APITestCase):
    """
    Testes para a API de gerenciamento de estoque.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.product = Product.objects.create(
            name='Produto Estoque',
            price=Decimal('100.00'),
            stock_quantity=50,
            sku='STOCK001'
        )
        
        self.stock_url = f'/api/v1/products/{self.product.id}/stock/'
    
    def authenticate_admin(self):
        """Autentica o admin para os testes."""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_update_stock_increase(self):
        """Testa o aumento de estoque."""
        self.authenticate_admin()
        
        stock_data = {
            'quantity': 20,
            'reason': 'Reposição de estoque'
        }
        
        response = self.client.patch(self.stock_url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['stock_change']['current'], 70)
        self.assertEqual(response.data['stock_change']['change'], 20)
        
        # Verificar no banco
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 70)
    
    def test_update_stock_decrease(self):
        """Testa a diminuição de estoque."""
        self.authenticate_admin()
        
        stock_data = {
            'quantity': -10,
            'reason': 'Venda'
        }
        
        response = self.client.patch(self.stock_url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['stock_change']['current'], 40)
        self.assertEqual(response.data['stock_change']['change'], -10)
        
        # Verificar no banco
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 40)
    
    def test_update_stock_negative_result(self):
        """Testa a tentativa de deixar estoque negativo."""
        self.authenticate_admin()
        
        stock_data = {
            'quantity': -60,  # Mais do que o estoque atual (50)
            'reason': 'Tentativa inválida'
        }
        
        response = self.client.patch(self.stock_url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertIn('negativo', response.data['message'])


class ProductCategoriesAPITest(APITestCase):
    """
    Testes para a API de categorias de produtos.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        # Criar produtos com diferentes categorias
        Product.objects.create(
            name='Produto A',
            price=Decimal('50.00'),
            category='Eletrônicos',
            sku='CATA001'
        )
        
        Product.objects.create(
            name='Produto B',
            price=Decimal('30.00'),
            category='Livros',
            sku='CATB001'
        )
        
        Product.objects.create(
            name='Produto C',
            price=Decimal('80.00'),
            category='Eletrônicos',
            sku='CATC001'
        )
        
        self.categories_url = '/api/v1/products/categories/'
    
    def test_list_categories(self):
        """Testa a listagem de categorias."""
        response = self.client.get(self.categories_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('categories', response.data)
        self.assertEqual(len(response.data['categories']), 2)
        self.assertIn('Eletrônicos', response.data['categories'])
        self.assertIn('Livros', response.data['categories'])
    
    def test_products_by_category(self):
        """Testa a listagem de produtos por categoria."""
        category_url = '/api/v1/products/category/Eletrônicos/'
        response = self.client.get(category_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['category'], 'Eletrônicos')
        self.assertEqual(len(response.data['products']), 2)


class ProductSearchAPITest(APITestCase):
    """
    Testes para a API de busca de produtos.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        # Criar produtos para busca
        Product.objects.create(
            name='Smartphone Samsung',
            description='Celular Android com boa qualidade',
            price=Decimal('800.00'),
            sku='PHONE001',
            category='Eletrônicos'
        )
        
        Product.objects.create(
            name='iPhone Apple',
            description='Smartphone iOS premium',
            price=Decimal('1200.00'),
            sku='PHONE002',
            category='Eletrônicos'
        )
        
        Product.objects.create(
            name='Livro Python',
            description='Guia completo de programação Python',
            price=Decimal('50.00'),
            sku='BOOK001',
            category='Livros'
        )
    
    def test_search_by_name(self):
        """Testa a busca por nome."""
        search_url = '/api/v1/products/search/iPhone/'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'iPhone Apple')
    
    def test_search_by_description(self):
        """Testa a busca por descrição."""
        search_url = '/api/v1/products/search/Android/'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Smartphone Samsung')
    
    def test_search_by_sku(self):
        """Testa a busca por SKU."""
        search_url = '/api/v1/products/search/BOOK001/'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['sku'], 'BOOK001')
    
    def test_search_no_results(self):
        """Testa a busca sem resultados."""
        search_url = '/api/v1/products/search/inexistente/'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_search_with_limit(self):
        """Testa a busca com limite de resultados."""
        search_url = '/api/v1/products/search/Smartphone/?limit=1'
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ProductLowStockAPITest(APITestCase):
    """
    Testes para a API de produtos com estoque baixo.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Criar produtos com diferentes níveis de estoque
        Product.objects.create(
            name='Produto Estoque Alto',
            price=Decimal('50.00'),
            stock_quantity=100,
            sku='HIGH001'
        )
        
        Product.objects.create(
            name='Produto Estoque Baixo 1',
            price=Decimal('30.00'),
            stock_quantity=3,
            sku='LOW001'
        )
        
        Product.objects.create(
            name='Produto Estoque Baixo 2',
            price=Decimal('80.00'),
            stock_quantity=1,
            sku='LOW002'
        )
        
        self.low_stock_url = '/api/v1/products/low-stock/'
    
    def authenticate_admin(self):
        """Autentica o admin para os testes."""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_low_stock_default_threshold(self):
        """Testa a listagem de produtos com estoque baixo (threshold padrão)."""
        self.authenticate_admin()
        
        response = self.client.get(self.low_stock_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['threshold'], 5)
        self.assertEqual(response.data['count'], 2)  # Apenas os produtos com estoque <= 5
    
    def test_low_stock_custom_threshold(self):
        """Testa a listagem com threshold customizado."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.low_stock_url}?threshold=2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['threshold'], 2)
        self.assertEqual(response.data['count'], 1)  # Apenas 1 produto com estoque <= 2
    
    def test_low_stock_unauthorized(self):
        """Testa o acesso não autorizado à API de estoque baixo."""
        response = self.client.get(self.low_stock_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
