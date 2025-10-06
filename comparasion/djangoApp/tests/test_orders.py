"""
Testes unitários para o app de pedidos - Django.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from tcc_django.apps.orders.models import Order, OrderItem, OrderStatusHistory, ShippingAddress
from tcc_django.apps.products.models import Product

User = get_user_model()


class OrderModelTest(TestCase):
    """
    Testes para o modelo Order.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Produto Teste',
            price=Decimal('50.00'),
            stock_quantity=10,
            sku='PROD001'
        )
        
        self.order_data = {
            'user': self.user,
            'status': 'pending',
            'total_amount': Decimal('60.00'),
            'shipping_address': 'Rua Teste, 123 - Cidade/Estado',
            'shipping_cost': Decimal('10.00'),
            'tax_amount': Decimal('0.00'),
            'discount_amount': Decimal('0.00')
        }
    
    def test_create_order(self):
        """Testa a criação de um pedido."""
        order = Order.objects.create(**self.order_data)
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('60.00'))
        self.assertEqual(order.shipping_cost, Decimal('10.00'))
        self.assertTrue(order.can_be_cancelled())
        self.assertFalse(order.can_be_refunded())
    
    def test_order_str_representation(self):
        """Testa a representação string do pedido."""
        order = Order.objects.create(**self.order_data)
        expected_str = f"Pedido {order.id} - {self.user.username}"
        self.assertEqual(str(order), expected_str)
    
    def test_order_subtotal_property(self):
        """Testa a propriedade subtotal do pedido."""
        order = Order.objects.create(**self.order_data)
        
        # Criar itens do pedido
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('50.00')
        )
        
        self.assertEqual(order.subtotal, Decimal('100.00'))
    
    def test_order_final_amount_property(self):
        """Testa a propriedade final_amount do pedido."""
        order = Order.objects.create(**self.order_data)
        
        # Criar item do pedido
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )
        
        # final_amount = subtotal + shipping_cost + tax_amount - discount_amount
        # 50.00 + 10.00 + 0.00 - 0.00 = 60.00
        self.assertEqual(order.final_amount, Decimal('60.00'))
    
    def test_order_items_count_property(self):
        """Testa a propriedade items_count do pedido."""
        order = Order.objects.create(**self.order_data)
        
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
            unit_price=Decimal('50.00')
        )
        
        self.assertEqual(order.items_count, 3)
    
    def test_order_status_transitions(self):
        """Testa as transições de status do pedido."""
        order = Order.objects.create(**self.order_data)
        
        # Status inicial: pending - pode ser cancelado
        self.assertTrue(order.can_be_cancelled())
        self.assertFalse(order.can_be_refunded())
        
        # Status: delivered - pode ser reembolsado
        order.status = 'delivered'
        order.save()
        self.assertFalse(order.can_be_cancelled())
        self.assertTrue(order.can_be_refunded())
        
        # Status: cancelled - não pode ser cancelado nem reembolsado
        order.status = 'cancelled'
        order.save()
        self.assertFalse(order.can_be_cancelled())
        self.assertFalse(order.can_be_refunded())


class OrderItemModelTest(TestCase):
    """
    Testes para o modelo OrderItem.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Produto Teste',
            price=Decimal('25.00'),
            stock_quantity=10,
            sku='PROD001'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            total_amount=Decimal('50.00'),
            shipping_address='Endereço Teste'
        )
    
    def test_create_order_item(self):
        """Testa a criação de um item de pedido."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('25.00')
        )
        
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal('25.00'))
        self.assertEqual(item.total_price, Decimal('50.00'))
    
    def test_order_item_auto_fill_product_info(self):
        """Testa o preenchimento automático das informações do produto."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1
        )
        
        # Deve preencher automaticamente
        self.assertEqual(item.product_name, 'Produto Teste')
        self.assertEqual(item.unit_price, Decimal('25.00'))
    
    def test_order_item_str_representation(self):
        """Testa a representação string do item de pedido."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('25.00')
        )
        
        expected_str = f"2x {self.product.name} - Pedido {self.order.id}"
        self.assertEqual(str(item), expected_str)


class ShippingAddressModelTest(TestCase):
    """
    Testes para o modelo ShippingAddress.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.address_data = {
            'user': self.user,
            'name': 'João Silva',
            'street': 'Rua das Flores',
            'number': '123',
            'complement': 'Apto 45',
            'neighborhood': 'Centro',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01234-567',
            'country': 'Brasil'
        }
    
    def test_create_shipping_address(self):
        """Testa a criação de um endereço de entrega."""
        address = ShippingAddress.objects.create(**self.address_data)
        
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.name, 'João Silva')
        self.assertEqual(address.city, 'São Paulo')
        self.assertEqual(address.state, 'SP')
        self.assertFalse(address.is_default)
    
    def test_shipping_address_str_representation(self):
        """Testa a representação string do endereço."""
        address = ShippingAddress.objects.create(**self.address_data)
        expected_str = "João Silva - Rua das Flores, 123 - São Paulo/SP"
        self.assertEqual(str(address), expected_str)
    
    def test_shipping_address_full_address_property(self):
        """Testa a propriedade full_address."""
        address = ShippingAddress.objects.create(**self.address_data)
        full_address = address.full_address
        
        self.assertIn('Rua das Flores, 123', full_address)
        self.assertIn('Apto 45', full_address)
        self.assertIn('Centro', full_address)
        self.assertIn('São Paulo/SP', full_address)
        self.assertIn('01234-567', full_address)
    
    def test_shipping_address_default_unique(self):
        """Testa que apenas um endereço pode ser padrão por usuário."""
        # Criar primeiro endereço como padrão
        address1 = ShippingAddress.objects.create(
            **self.address_data,
            is_default=True
        )
        
        # Criar segundo endereço como padrão
        address_data_2 = self.address_data.copy()
        address_data_2['name'] = 'Maria Silva'
        address2 = ShippingAddress.objects.create(
            **address_data_2,
            is_default=True
        )
        
        # O primeiro deve ter perdido o status de padrão
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)


class OrderAPITest(APITestCase):
    """
    Testes para a API de pedidos.
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
        
        # Criar produtos
        self.product1 = Product.objects.create(
            name='Produto 1',
            price=Decimal('50.00'),
            stock_quantity=20,
            sku='PROD001'
        )
        
        self.product2 = Product.objects.create(
            name='Produto 2',
            price=Decimal('30.00'),
            stock_quantity=15,
            sku='PROD002'
        )
        
        # Criar endereço de entrega
        self.shipping_address = ShippingAddress.objects.create(
            user=self.user,
            name='João Silva',
            street='Rua Teste',
            number='123',
            neighborhood='Centro',
            city='São Paulo',
            state='SP',
            zip_code='01234-567',
            is_default=True
        )
        
        # Criar pedido de teste
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            total_amount=Decimal('60.00'),
            shipping_address=self.shipping_address.full_address
        )
        
        # URLs
        self.orders_url = '/api/v1/orders/'
        self.order_detail_url = f'/api/v1/orders/{self.order.id}/'
        self.my_orders_url = '/api/v1/orders/my_orders/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_order_success(self):
        """Testa a criação bem-sucedida de um pedido."""
        self.authenticate_user(self.user)
        
        order_data = {
            'shipping_address_id': str(self.shipping_address.id),
            'notes': 'Pedido de teste',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 2
                },
                {
                    'product': self.product2.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(self.orders_url, order_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('order', response.data)
        
        # Verificar se o pedido foi criado
        order = Order.objects.get(id=response.data['order']['id'])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 2)
    
    def test_create_order_invalid_product(self):
        """Testa a criação de pedido com produto inválido."""
        self.authenticate_user(self.user)
        
        order_data = {
            'items': [
                {
                    'product': 99999,  # Produto inexistente
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(self.orders_url, order_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_create_order_insufficient_stock(self):
        """Testa a criação de pedido com estoque insuficiente."""
        self.authenticate_user(self.user)
        
        order_data = {
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 100  # Mais do que o estoque disponível
                }
            ]
        }
        
        response = self.client.post(self.orders_url, order_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_list_orders_as_admin(self):
        """Testa a listagem de pedidos como admin."""
        self.authenticate_user(self.admin_user)
        
        response = self.client.get(self.orders_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('orders', response.data)
    
    def test_list_orders_as_regular_user(self):
        """Testa a listagem de pedidos como usuário comum."""
        self.authenticate_user(self.user)
        
        response = self.client.get(self.orders_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_my_orders(self):
        """Testa a listagem de pedidos do usuário atual."""
        self.authenticate_user(self.user)
        
        response = self.client.get(self.my_orders_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('orders', response.data)
        self.assertEqual(len(response.data['orders']), 1)
    
    def test_get_order_detail(self):
        """Testa a obtenção de detalhes de um pedido."""
        self.authenticate_user(self.user)
        
        response = self.client.get(self.order_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['order']['id'], str(self.order.id))
    
    def test_cancel_order_success(self):
        """Testa o cancelamento bem-sucedido de um pedido."""
        self.authenticate_user(self.user)
        
        cancel_url = f'/api/v1/orders/{self.order.id}/cancel/'
        response = self.client.post(cancel_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
    
    def test_cancel_order_invalid_status(self):
        """Testa o cancelamento de pedido com status inválido."""
        self.authenticate_user(self.user)
        
        # Alterar status para um que não pode ser cancelado
        self.order.status = 'delivered'
        self.order.save()
        
        cancel_url = f'/api/v1/orders/{self.order.id}/cancel/'
        response = self.client.post(cancel_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_confirm_order_as_admin(self):
        """Testa a confirmação de pedido como admin."""
        self.authenticate_user(self.admin_user)
        
        confirm_url = f'/api/v1/orders/{self.order.id}/confirm/'
        response = self.client.post(confirm_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        self.assertIsNotNone(self.order.confirmed_at)
    
    def test_confirm_order_as_regular_user(self):
        """Testa a confirmação de pedido como usuário comum."""
        self.authenticate_user(self.user)
        
        confirm_url = f'/api/v1/orders/{self.order.id}/confirm/'
        response = self.client.post(confirm_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])
    
    def test_order_stats_as_admin(self):
        """Testa as estatísticas de pedidos como admin."""
        self.authenticate_user(self.admin_user)
        
        stats_url = '/api/v1/orders/stats/'
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('stats', response.data)
        self.assertIn('total_orders', response.data['stats'])
    
    def test_order_history(self):
        """Testa o histórico de status do pedido."""
        self.authenticate_user(self.user)
        
        # Criar histórico
        OrderStatusHistory.objects.create(
            order=self.order,
            status='pending',
            notes='Pedido criado',
            changed_by=self.user
        )
        
        history_url = f'/api/v1/orders/{self.order.id}/history/'
        response = self.client.get(history_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('history', response.data)
        self.assertGreater(response.data['count'], 0)


class ShippingAddressAPITest(APITestCase):
    """
    Testes para a API de endereços de entrega.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.address = ShippingAddress.objects.create(
            user=self.user,
            name='João Silva',
            street='Rua Teste',
            number='123',
            neighborhood='Centro',
            city='São Paulo',
            state='SP',
            zip_code='01234567'
        )
        
        self.addresses_url = '/api/v1/shipping-addresses/'
        self.address_detail_url = f'/api/v1/shipping-addresses/{self.address.id}/'
    
    def authenticate_user(self):
        """Autentica o usuário para os testes."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_shipping_address(self):
        """Testa a criação de endereço de entrega."""
        self.authenticate_user()
        
        address_data = {
            'name': 'Maria Silva',
            'street': 'Rua Nova',
            'number': '456',
            'neighborhood': 'Bairro Novo',
            'city': 'Rio de Janeiro',
            'state': 'RJ',
            'zip_code': '20000-000'
        }
        
        response = self.client.post(self.addresses_url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['address']['name'], 'Maria Silva')
    
    def test_create_address_invalid_zip_code(self):
        """Testa a criação com CEP inválido."""
        self.authenticate_user()
        
        address_data = {
            'name': 'Teste',
            'street': 'Rua Teste',
            'number': '123',
            'city': 'Cidade',
            'state': 'SP',
            'zip_code': '123'  # CEP inválido
        }
        
        response = self.client.post(self.addresses_url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_list_shipping_addresses(self):
        """Testa a listagem de endereços do usuário."""
        self.authenticate_user()
        
        response = self.client.get(self.addresses_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['addresses']), 1)
    
    def test_set_default_address(self):
        """Testa a definição de endereço padrão."""
        self.authenticate_user()
        
        set_default_url = f'/api/v1/shipping-addresses/{self.address.id}/set_default/'
        response = self.client.post(set_default_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se foi definido como padrão
        self.address.refresh_from_db()
        self.assertTrue(self.address.is_default)
    
    def test_update_shipping_address(self):
        """Testa a atualização de endereço de entrega."""
        self.authenticate_user()
        
        update_data = {
            'name': 'João Silva Atualizado',
            'city': 'Brasília'
        }
        
        response = self.client.put(self.address_detail_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se foi atualizado
        self.address.refresh_from_db()
        self.assertEqual(self.address.name, 'João Silva Atualizado')
        self.assertEqual(self.address.city, 'Brasília')
    
    def test_delete_shipping_address(self):
        """Testa a exclusão de endereço de entrega."""
        self.authenticate_user()
        
        response = self.client.delete(self.address_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se foi deletado
        with self.assertRaises(ShippingAddress.DoesNotExist):
            ShippingAddress.objects.get(id=self.address.id)


class OrderFilterTest(APITestCase):
    """
    Testes para filtros da API de pedidos.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Criar pedidos com diferentes status
        Order.objects.create(
            user=self.user1,
            status='pending',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço 1'
        )
        
        Order.objects.create(
            user=self.user1,
            status='confirmed',
            total_amount=Decimal('200.00'),
            shipping_address='Endereço 1'
        )
        
        Order.objects.create(
            user=self.user2,
            status='delivered',
            total_amount=Decimal('150.00'),
            shipping_address='Endereço 2'
        )
        
        self.orders_url = '/api/v1/orders/'
    
    def authenticate_admin(self):
        """Autentica o admin para os testes."""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_filter_orders_by_status(self):
        """Testa o filtro de pedidos por status."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.orders_url}?status=pending')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['orders']), 1)
        self.assertEqual(response.data['orders'][0]['status'], 'pending')
    
    def test_filter_orders_by_user(self):
        """Testa o filtro de pedidos por usuário."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.orders_url}?user={self.user1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['orders']), 2)
    
    def test_search_orders(self):
        """Testa a busca de pedidos."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.orders_url}?search=user1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['orders']), 2)
