"""
Testes unitários para o módulo de produtos - Flask.
"""
import pytest
import json
from decimal import Decimal
from app import create_app
from app.core.database import db
from app.models.user import User
from app.models.product import Product


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
def admin_headers(client):
    """Fixture para criar headers de autenticação de admin."""
    # Criar usuário admin
    admin_data = {
        'username': 'admin',
        'email': 'admin@example.com',
        'full_name': 'Admin User',
        'password': 'adminpass123'
    }
    
    # Registrar admin
    client.post('/api/v1/users/register', 
                data=json.dumps(admin_data),
                content_type='application/json')
    
    # Fazer login
    login_data = {
        'username': 'admin',
        'password': 'adminpass123'
    }
    
    response = client.post('/api/v1/users/login',
                          data=json.dumps(login_data),
                          content_type='application/json')
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_products(app):
    """Fixture para criar produtos de exemplo."""
    with app.app_context():
        products = [
            Product(
                name='Produto 1',
                description='Descrição do produto 1',
                price=Decimal('50.00'),
                stock_quantity=20,
                sku='PROD001',
                category='Categoria A'
            ),
            Product(
                name='Produto 2',
                description='Descrição do produto 2',
                price=Decimal('75.00'),
                stock_quantity=0,
                sku='PROD002',
                category='Categoria B'
            ),
            Product(
                name='Smartphone Samsung',
                description='Celular Android com boa qualidade',
                price=Decimal('800.00'),
                stock_quantity=10,
                sku='PHONE001',
                category='Eletrônicos'
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        return products


class TestProductModel:
    """Testes para o modelo Product."""
    
    def test_create_product(self, app):
        """Testa a criação de um produto."""
        with app.app_context():
            product = Product(
                name='Produto Teste',
                description='Descrição do produto teste',
                price=Decimal('99.99'),
                stock_quantity=10,
                sku='PROD001',
                category='Eletrônicos'
            )
            
            db.session.add(product)
            db.session.commit()
            
            assert product.name == 'Produto Teste'
            assert product.description == 'Descrição do produto teste'
            assert product.price == Decimal('99.99')
            assert product.stock_quantity == 10
            assert product.sku == 'PROD001'
            assert product.category == 'Eletrônicos'
            assert product.is_active is True
            assert product.is_in_stock is True
    
    def test_product_repr(self, app):
        """Testa a representação string do produto."""
        with app.app_context():
            product = Product(name='Produto Teste', sku='PROD001')
            assert repr(product) == '<Product Produto Teste>'
    
    def test_product_is_in_stock_property(self, app):
        """Testa a propriedade is_in_stock."""
        with app.app_context():
            # Produto com estoque
            product_with_stock = Product(
                name='Com Estoque',
                price=Decimal('50.00'),
                stock_quantity=10,
                sku='STOCK001'
            )
            assert product_with_stock.is_in_stock is True
            
            # Produto sem estoque
            product_no_stock = Product(
                name='Sem Estoque',
                price=Decimal('50.00'),
                stock_quantity=0,
                sku='STOCK002'
            )
            assert product_no_stock.is_in_stock is False
    
    def test_product_to_dict(self, app):
        """Testa a conversão do produto para dicionário."""
        with app.app_context():
            product = Product(
                name='Produto Teste',
                description='Descrição teste',
                price=Decimal('99.99'),
                stock_quantity=10,
                sku='PROD001',
                category='Teste'
            )
            
            db.session.add(product)
            db.session.commit()
            
            product_dict = product.to_dict()
            
            assert product_dict['name'] == 'Produto Teste'
            assert product_dict['description'] == 'Descrição teste'
            assert product_dict['price'] == '99.99'
            assert product_dict['stock_quantity'] == 10
            assert product_dict['sku'] == 'PROD001'
            assert product_dict['category'] == 'Teste'
            assert product_dict['is_active'] is True
            assert product_dict['is_in_stock'] is True
            assert 'id' in product_dict


class TestProductAPI:
    """Testes para a API de produtos."""
    
    def test_list_products_public(self, client, sample_products):
        """Testa a listagem pública de produtos."""
        response = client.get('/api/v1/products/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'products' in data
        assert len(data['products']) == 3
    
    def test_get_product_detail(self, client, sample_products):
        """Testa a obtenção de detalhes de um produto."""
        product_id = sample_products[0].id
        response = client.get(f'/api/v1/products/{product_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['product']['name'] == 'Produto 1'
        assert data['product']['sku'] == 'PROD001'
    
    def test_get_nonexistent_product(self, client):
        """Testa a obtenção de produto inexistente."""
        response = client.get('/api/v1/products/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_create_product_as_admin(self, client, admin_headers):
        """Testa a criação de produto como admin."""
        product_data = {
            'name': 'Novo Produto',
            'description': 'Descrição do novo produto',
            'price': '120.00',
            'stock_quantity': 15,
            'sku': 'PROD003',
            'category': 'Nova Categoria'
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['product']['name'] == 'Novo Produto'
        assert data['product']['sku'] == 'PROD003'
    
    def test_create_product_unauthorized(self, client):
        """Testa a criação de produto sem autorização."""
        product_data = {
            'name': 'Produto Não Autorizado',
            'price': '50.00',
            'sku': 'PROD004'
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_create_product_duplicate_sku(self, client, admin_headers, sample_products):
        """Testa a criação de produto com SKU duplicado."""
        product_data = {
            'name': 'Produto Duplicado',
            'price': '50.00',
            'sku': 'PROD001'  # SKU já existe
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_create_product_invalid_data(self, client, admin_headers):
        """Testa a criação de produto com dados inválidos."""
        product_data = {
            'name': 'Produto Inválido',
            'price': '-10.00',  # Preço negativo
            'stock_quantity': -5  # Estoque negativo
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_update_product_as_admin(self, client, admin_headers, sample_products):
        """Testa a atualização de produto como admin."""
        product_id = sample_products[0].id
        update_data = {
            'name': 'Produto 1 Atualizado',
            'price': '60.00'
        }
        
        response = client.put(f'/api/v1/products/{product_id}',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['product']['name'] == 'Produto 1 Atualizado'
        assert data['product']['price'] == '60.00'
    
    def test_update_product_unauthorized(self, client, sample_products):
        """Testa a atualização de produto sem autorização."""
        product_id = sample_products[0].id
        update_data = {'name': 'Tentativa de Atualização'}
        
        response = client.put(f'/api/v1/products/{product_id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_delete_product_as_admin(self, client, admin_headers, sample_products):
        """Testa a exclusão de produto como admin."""
        product_id = sample_products[0].id
        
        response = client.delete(f'/api/v1/products/{product_id}',
                                headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_delete_product_unauthorized(self, client, sample_products):
        """Testa a exclusão de produto sem autorização."""
        product_id = sample_products[0].id
        
        response = client.delete(f'/api/v1/products/{product_id}')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True


class TestProductFilters:
    """Testes para filtros de produtos."""
    
    def test_filter_by_category(self, client, sample_products):
        """Testa o filtro por categoria."""
        response = client.get('/api/v1/products/?category=Categoria A')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
        assert data['products'][0]['category'] == 'Categoria A'
    
    def test_filter_in_stock_only(self, client, sample_products):
        """Testa o filtro apenas produtos em estoque."""
        response = client.get('/api/v1/products/?in_stock_only=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Deve retornar apenas produtos com estoque > 0
        for product in data['products']:
            assert product['is_in_stock'] is True
    
    def test_filter_by_price_range(self, client, sample_products):
        """Testa o filtro por faixa de preço."""
        response = client.get('/api/v1/products/?min_price=60&max_price=100')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        for product in data['products']:
            price = float(product['price'])
            assert 60 <= price <= 100
    
    def test_search_products(self, client, sample_products):
        """Testa a busca de produtos."""
        response = client.get('/api/v1/products/?search=Samsung')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
        assert 'Samsung' in data['products'][0]['name']
    
    def test_search_by_sku(self, client, sample_products):
        """Testa a busca por SKU."""
        response = client.get('/api/v1/products/?search=PHONE001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
        assert data['products'][0]['sku'] == 'PHONE001'


class TestProductCategories:
    """Testes para categorias de produtos."""
    
    def test_list_categories(self, client, sample_products):
        """Testa a listagem de categorias."""
        response = client.get('/api/v1/products/categories')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'categories' in data
        assert len(data['categories']) >= 3
        assert 'Categoria A' in data['categories']
        assert 'Eletrônicos' in data['categories']
    
    def test_products_by_category(self, client, sample_products):
        """Testa a listagem de produtos por categoria."""
        response = client.get('/api/v1/products/category/Eletrônicos')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['category'] == 'Eletrônicos'
        assert len(data['products']) == 1
        assert data['products'][0]['category'] == 'Eletrônicos'
    
    def test_products_by_nonexistent_category(self, client):
        """Testa a listagem de produtos por categoria inexistente."""
        response = client.get('/api/v1/products/category/Inexistente')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['category'] == 'Inexistente'
        assert len(data['products']) == 0


class TestProductSearch:
    """Testes para busca de produtos."""
    
    def test_search_by_name(self, client, sample_products):
        """Testa a busca por nome."""
        response = client.get('/api/v1/products/search/Samsung')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 1
        assert 'Samsung' in data['results'][0]['name']
    
    def test_search_by_description(self, client, sample_products):
        """Testa a busca por descrição."""
        response = client.get('/api/v1/products/search/Android')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert 'Android' in data['results'][0]['description']
    
    def test_search_no_results(self, client, sample_products):
        """Testa a busca sem resultados."""
        response = client.get('/api/v1/products/search/inexistente')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert len(data['results']) == 0
    
    def test_search_with_limit(self, client, sample_products):
        """Testa a busca com limite de resultados."""
        response = client.get('/api/v1/products/search/Produto?limit=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['results']) <= 1


class TestProductStock:
    """Testes para gerenciamento de estoque."""
    
    def test_update_stock_as_admin(self, client, admin_headers, sample_products):
        """Testa a atualização de estoque como admin."""
        product_id = sample_products[0].id
        stock_data = {
            'quantity': 10,
            'reason': 'Reposição de estoque'
        }
        
        response = client.patch(f'/api/v1/products/{product_id}/stock',
                               data=json.dumps(stock_data),
                               content_type='application/json',
                               headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stock_change']['change'] == 10
        assert data['stock_change']['current'] == 30  # 20 + 10
    
    def test_update_stock_decrease(self, client, admin_headers, sample_products):
        """Testa a diminuição de estoque."""
        product_id = sample_products[0].id
        stock_data = {
            'quantity': -5,
            'reason': 'Venda'
        }
        
        response = client.patch(f'/api/v1/products/{product_id}/stock',
                               data=json.dumps(stock_data),
                               content_type='application/json',
                               headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stock_change']['change'] == -5
        assert data['stock_change']['current'] == 15  # 20 - 5
    
    def test_update_stock_negative_result(self, client, admin_headers, sample_products):
        """Testa a tentativa de deixar estoque negativo."""
        product_id = sample_products[0].id
        stock_data = {
            'quantity': -30,  # Mais do que o estoque atual (20)
            'reason': 'Tentativa inválida'
        }
        
        response = client.patch(f'/api/v1/products/{product_id}/stock',
                               data=json.dumps(stock_data),
                               content_type='application/json',
                               headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'negativo' in data['message']
    
    def test_update_stock_unauthorized(self, client, sample_products):
        """Testa a atualização de estoque sem autorização."""
        product_id = sample_products[0].id
        stock_data = {
            'quantity': 10,
            'reason': 'Tentativa não autorizada'
        }
        
        response = client.patch(f'/api/v1/products/{product_id}/stock',
                               data=json.dumps(stock_data),
                               content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True


class TestProductLowStock:
    """Testes para produtos com estoque baixo."""
    
    def test_low_stock_default_threshold(self, client, admin_headers, sample_products):
        """Testa a listagem de produtos com estoque baixo (threshold padrão)."""
        response = client.get('/api/v1/products/low-stock',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['threshold'] == 5
        # Deve incluir produtos com estoque <= 5 (incluindo o produto com estoque 0)
        assert data['count'] >= 1
    
    def test_low_stock_custom_threshold(self, client, admin_headers, sample_products):
        """Testa a listagem com threshold customizado."""
        response = client.get('/api/v1/products/low-stock?threshold=15',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['threshold'] == 15
        # Deve incluir produtos com estoque <= 15
        assert data['count'] >= 2
    
    def test_low_stock_unauthorized(self, client):
        """Testa o acesso não autorizado à API de estoque baixo."""
        response = client.get('/api/v1/products/low-stock')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] is True


class TestProductValidation:
    """Testes para validação de dados de produto."""
    
    def test_required_fields_validation(self, client, admin_headers):
        """Testa a validação de campos obrigatórios."""
        product_data = {
            'description': 'Produto sem nome'
            # Faltando name, price, sku
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_price_validation(self, client, admin_headers):
        """Testa a validação do preço."""
        product_data = {
            'name': 'Produto Teste',
            'price': 'invalid_price',  # Preço inválido
            'sku': 'INVALID001'
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
    
    def test_stock_quantity_validation(self, client, admin_headers):
        """Testa a validação da quantidade em estoque."""
        product_data = {
            'name': 'Produto Teste',
            'price': '50.00',
            'stock_quantity': 'invalid_quantity',  # Quantidade inválida
            'sku': 'INVALID002'
        }
        
        response = client.post('/api/v1/products/',
                              data=json.dumps(product_data),
                              content_type='application/json',
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
