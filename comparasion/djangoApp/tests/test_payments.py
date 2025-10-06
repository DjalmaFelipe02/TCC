"""
Testes unitários para o app de pagamentos - Django.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from tcc_django.apps.payments.models import PaymentMethod, Payment, PaymentTransaction, Refund
from tcc_django.apps.orders.models import Order
from tcc_django.apps.products.models import Product

User = get_user_model()


class PaymentMethodModelTest(TestCase):
    """
    Testes para o modelo PaymentMethod.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.card_data = {
            'user': self.user,
            'type': 'credit_card',
            'name': 'Cartão Principal',
            'card_last_four': '1234',
            'card_brand': 'Visa',
            'card_expiry_month': 12,
            'card_expiry_year': 2025
        }
    
    def test_create_payment_method(self):
        """Testa a criação de um método de pagamento."""
        payment_method = PaymentMethod.objects.create(**self.card_data)
        
        self.assertEqual(payment_method.user, self.user)
        self.assertEqual(payment_method.type, 'credit_card')
        self.assertEqual(payment_method.card_last_four, '1234')
        self.assertEqual(payment_method.card_brand, 'Visa')
        self.assertTrue(payment_method.is_active)
        self.assertFalse(payment_method.is_default)
    
    def test_payment_method_str_representation(self):
        """Testa a representação string do método de pagamento."""
        payment_method = PaymentMethod.objects.create(**self.card_data)
        expected_str = "Cartão de Crédito **** 1234"
        self.assertEqual(str(payment_method), expected_str)
    
    def test_payment_method_default_unique(self):
        """Testa que apenas um método pode ser padrão por usuário."""
        # Criar primeiro método como padrão
        method1 = PaymentMethod.objects.create(
            **self.card_data,
            is_default=True
        )
        
        # Criar segundo método como padrão
        card_data_2 = self.card_data.copy()
        card_data_2['name'] = 'Cartão Secundário'
        card_data_2['card_last_four'] = '5678'
        method2 = PaymentMethod.objects.create(
            **card_data_2,
            is_default=True
        )
        
        # O primeiro deve ter perdido o status de padrão
        method1.refresh_from_db()
        self.assertFalse(method1.is_default)
        self.assertTrue(method2.is_default)
    
    def test_payment_method_pix(self):
        """Testa a criação de método PIX."""
        pix_data = {
            'user': self.user,
            'type': 'pix',
            'name': 'PIX Principal',
            'account_info': {'key': 'user@example.com'}
        }
        
        payment_method = PaymentMethod.objects.create(**pix_data)
        
        self.assertEqual(payment_method.type, 'pix')
        self.assertEqual(str(payment_method), 'PIX - PIX Principal')


class PaymentModelTest(TestCase):
    """
    Testes para o modelo Payment.
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
            price=Decimal('100.00'),
            stock_quantity=10,
            sku='PROD001'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço Teste'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            type='credit_card',
            name='Cartão Teste',
            card_last_four='1234',
            card_brand='Visa'
        )
        
        self.payment_data = {
            'order': self.order,
            'payment_method': self.payment_method,
            'amount': Decimal('100.00'),
            'currency': 'BRL',
            'status': 'pending'
        }
    
    def test_create_payment(self):
        """Testa a criação de um pagamento."""
        payment = Payment.objects.create(**self.payment_data)
        
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.payment_method, self.payment_method)
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertFalse(payment.is_successful)
        self.assertTrue(payment.can_be_cancelled)
        self.assertFalse(payment.can_be_refunded)
    
    def test_payment_str_representation(self):
        """Testa a representação string do pagamento."""
        payment = Payment.objects.create(**self.payment_data)
        expected_str = f"Pagamento {payment.id} - Pedido {self.order.id} - Pendente"
        self.assertEqual(str(payment), expected_str)
    
    def test_payment_properties(self):
        """Testa as propriedades do pagamento."""
        payment = Payment.objects.create(**self.payment_data)
        
        # Status pending
        self.assertFalse(payment.is_successful)
        self.assertTrue(payment.can_be_cancelled)
        self.assertFalse(payment.can_be_refunded)
        
        # Status completed
        payment.status = 'completed'
        payment.save()
        self.assertTrue(payment.is_successful)
        self.assertFalse(payment.can_be_cancelled)
        self.assertTrue(payment.can_be_refunded)


class PaymentTransactionModelTest(TestCase):
    """
    Testes para o modelo PaymentTransaction.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço Teste'
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('100.00'),
            status='pending'
        )
    
    def test_create_payment_transaction(self):
        """Testa a criação de uma transação de pagamento."""
        transaction = PaymentTransaction.objects.create(
            payment=self.payment,
            type='charge',
            amount=Decimal('100.00'),
            status='completed',
            description='Cobrança processada'
        )
        
        self.assertEqual(transaction.payment, self.payment)
        self.assertEqual(transaction.type, 'charge')
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.status, 'completed')
    
    def test_transaction_str_representation(self):
        """Testa a representação string da transação."""
        transaction = PaymentTransaction.objects.create(
            payment=self.payment,
            type='refund',
            amount=Decimal('50.00'),
            status='completed'
        )
        
        expected_str = "Reembolso - 50.00 - Concluído"
        self.assertEqual(str(transaction), expected_str)


class RefundModelTest(TestCase):
    """
    Testes para o modelo Refund.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='delivered',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço Teste'
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('100.00'),
            status='completed'
        )
    
    def test_create_refund(self):
        """Testa a criação de um reembolso."""
        refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            reason='customer_request',
            status='pending',
            requested_by=self.user
        )
        
        self.assertEqual(refund.payment, self.payment)
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.reason, 'customer_request')
        self.assertTrue(refund.is_partial)
    
    def test_refund_str_representation(self):
        """Testa a representação string do reembolso."""
        refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('100.00'),
            reason='product_defective',
            status='completed'
        )
        
        expected_str = f"Reembolso {refund.id} - 100.00 - Concluído"
        self.assertEqual(str(refund), expected_str)
    
    def test_refund_is_partial_property(self):
        """Testa a propriedade is_partial do reembolso."""
        # Reembolso parcial
        partial_refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            reason='customer_request'
        )
        self.assertTrue(partial_refund.is_partial)
        
        # Reembolso total
        full_refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('100.00'),
            reason='product_defective'
        )
        self.assertFalse(full_refund.is_partial)


class PaymentMethodAPITest(APITestCase):
    """
    Testes para a API de métodos de pagamento.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            type='credit_card',
            name='Cartão Teste',
            card_last_four='1234',
            card_brand='Visa',
            card_expiry_month=12,
            card_expiry_year=2025
        )
        
        self.payment_methods_url = '/api/v1/payment-methods/'
        self.payment_method_detail_url = f'/api/v1/payment-methods/{self.payment_method.id}/'
    
    def authenticate_user(self):
        """Autentica o usuário para os testes."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_payment_method_credit_card(self):
        """Testa a criação de método de pagamento cartão de crédito."""
        self.authenticate_user()
        
        card_data = {
            'type': 'credit_card',
            'name': 'Novo Cartão',
            'card_number': '4111111111111111',
            'card_expiry_month': 6,
            'card_expiry_year': 2026,
            'card_cvv': '123',
            'cardholder_name': 'João Silva'
        }
        
        response = self.client.post(self.payment_methods_url, card_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['payment_method']['card_last_four'], '1111')
        self.assertEqual(response.data['payment_method']['card_brand'], 'Visa')
    
    def test_create_payment_method_pix(self):
        """Testa a criação de método de pagamento PIX."""
        self.authenticate_user()
        
        pix_data = {
            'type': 'pix',
            'name': 'PIX Principal',
            'account_info': {'key': 'user@example.com'}
        }
        
        response = self.client.post(self.payment_methods_url, pix_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['payment_method']['type'], 'pix')
    
    def test_create_payment_method_invalid_card(self):
        """Testa a criação com dados de cartão inválidos."""
        self.authenticate_user()
        
        invalid_data = {
            'type': 'credit_card',
            'name': 'Cartão Inválido',
            'card_number': '123',  # Número inválido
            'card_expiry_month': 6,
            'card_expiry_year': 2026
        }
        
        response = self.client.post(self.payment_methods_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_list_payment_methods(self):
        """Testa a listagem de métodos de pagamento do usuário."""
        self.authenticate_user()
        
        response = self.client.get(self.payment_methods_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['payment_methods']), 1)
    
    def test_set_default_payment_method(self):
        """Testa a definição de método de pagamento padrão."""
        self.authenticate_user()
        
        set_default_url = f'/api/v1/payment-methods/{self.payment_method.id}/set_default/'
        response = self.client.post(set_default_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se foi definido como padrão
        self.payment_method.refresh_from_db()
        self.assertTrue(self.payment_method.is_default)
    
    def test_deactivate_payment_method(self):
        """Testa a desativação de método de pagamento."""
        self.authenticate_user()
        
        deactivate_url = f'/api/v1/payment-methods/{self.payment_method.id}/deactivate/'
        response = self.client.post(deactivate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se foi desativado
        self.payment_method.refresh_from_db()
        self.assertFalse(self.payment_method.is_active)


class PaymentAPITest(APITestCase):
    """
    Testes para a API de pagamentos.
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
        
        self.product = Product.objects.create(
            name='Produto Teste',
            price=Decimal('100.00'),
            stock_quantity=10,
            sku='PROD001'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status='confirmed',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço Teste'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            type='credit_card',
            name='Cartão Teste',
            card_last_four='1234',
            card_brand='Visa'
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            status='pending'
        )
        
        self.payments_url = '/api/v1/payments/'
        self.payment_detail_url = f'/api/v1/payments/{self.payment.id}/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_payment(self):
        """Testa a criação de um pagamento."""
        self.authenticate_user(self.user)
        
        payment_data = {
            'order_id': str(self.order.id),
            'payment_method_id': str(self.payment_method.id),
            'description': 'Pagamento de teste'
        }
        
        response = self.client.post(self.payments_url, payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('payment', response.data)
    
    def test_create_payment_invalid_order(self):
        """Testa a criação de pagamento com pedido inválido."""
        self.authenticate_user(self.user)
        
        payment_data = {
            'order_id': '99999999-9999-9999-9999-999999999999',
            'payment_method_id': str(self.payment_method.id)
        }
        
        response = self.client.post(self.payments_url, payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_list_payments_as_admin(self):
        """Testa a listagem de pagamentos como admin."""
        self.authenticate_user(self.admin_user)
        
        response = self.client.get(self.payments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('payments', response.data)
    
    def test_my_payments(self):
        """Testa a listagem de pagamentos do usuário atual."""
        self.authenticate_user(self.user)
        
        my_payments_url = '/api/v1/payments/my_payments/'
        response = self.client.get(my_payments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['payments']), 1)
    
    def test_process_payment(self):
        """Testa o processamento de um pagamento."""
        self.authenticate_user(self.user)
        
        process_url = f'/api/v1/payments/{self.payment.id}/process/'
        response = self.client.post(process_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.payment.refresh_from_db()
        self.assertIn(self.payment.status, ['completed', 'failed'])
    
    def test_cancel_payment(self):
        """Testa o cancelamento de um pagamento."""
        self.authenticate_user(self.user)
        
        cancel_url = f'/api/v1/payments/{self.payment.id}/cancel/'
        response = self.client.post(cancel_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'cancelled')
    
    def test_payment_stats_as_admin(self):
        """Testa as estatísticas de pagamentos como admin."""
        self.authenticate_user(self.admin_user)
        
        stats_url = '/api/v1/payments/stats/'
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('stats', response.data)
        self.assertIn('total_payments', response.data['stats'])


class RefundAPITest(APITestCase):
    """
    Testes para a API de reembolsos.
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
        
        self.order = Order.objects.create(
            user=self.user,
            status='delivered',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço Teste'
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('100.00'),
            status='completed'
        )
        
        self.refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            reason='customer_request',
            status='pending',
            requested_by=self.user
        )
        
        self.refunds_url = '/api/v1/refunds/'
        self.refund_detail_url = f'/api/v1/refunds/{self.refund.id}/'
    
    def authenticate_user(self, user):
        """Autentica um usuário para os testes."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_refund(self):
        """Testa a criação de uma solicitação de reembolso."""
        self.authenticate_user(self.user)
        
        refund_data = {
            'payment_id': str(self.payment.id),
            'amount': '30.00',
            'reason': 'product_defective',
            'description': 'Produto chegou com defeito'
        }
        
        response = self.client.post(self.refunds_url, refund_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('refund', response.data)
    
    def test_create_refund_invalid_amount(self):
        """Testa a criação de reembolso com valor inválido."""
        self.authenticate_user(self.user)
        
        refund_data = {
            'payment_id': str(self.payment.id),
            'amount': '200.00',  # Maior que o valor do pagamento
            'reason': 'customer_request'
        }
        
        response = self.client.post(self.refunds_url, refund_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
    
    def test_approve_refund_as_admin(self):
        """Testa a aprovação de reembolso como admin."""
        self.authenticate_user(self.admin_user)
        
        approve_url = f'/api/v1/refunds/{self.refund.id}/approve/'
        response = self.client.post(approve_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.status, 'completed')
    
    def test_reject_refund_as_admin(self):
        """Testa a rejeição de reembolso como admin."""
        self.authenticate_user(self.admin_user)
        
        reject_url = f'/api/v1/refunds/{self.refund.id}/reject/'
        reject_data = {'notes': 'Motivo insuficiente'}
        
        response = self.client.post(reject_url, reject_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar se o status foi alterado
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.status, 'cancelled')
    
    def test_approve_refund_as_regular_user(self):
        """Testa a tentativa de aprovação como usuário comum."""
        self.authenticate_user(self.user)
        
        approve_url = f'/api/v1/refunds/{self.refund.id}/approve/'
        response = self.client.post(approve_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['error'])


class PaymentFilterTest(APITestCase):
    """
    Testes para filtros da API de pagamentos.
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
        
        self.order1 = Order.objects.create(
            user=self.user1,
            status='confirmed',
            total_amount=Decimal('100.00'),
            shipping_address='Endereço 1'
        )
        
        self.order2 = Order.objects.create(
            user=self.user1,
            status='confirmed',
            total_amount=Decimal('200.00'),
            shipping_address='Endereço 1'
        )
        
        # Criar pagamentos com diferentes status
        Payment.objects.create(
            order=self.order1,
            amount=Decimal('100.00'),
            status='completed',
            gateway='stripe'
        )
        
        Payment.objects.create(
            order=self.order2,
            amount=Decimal('200.00'),
            status='pending',
            gateway='paypal'
        )
        
        self.payments_url = '/api/v1/payments/'
    
    def authenticate_admin(self):
        """Autentica o admin para os testes."""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_filter_payments_by_status(self):
        """Testa o filtro de pagamentos por status."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.payments_url}?status=completed')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['payments']), 1)
        self.assertEqual(response.data['payments'][0]['status'], 'completed')
    
    def test_filter_payments_by_gateway(self):
        """Testa o filtro de pagamentos por gateway."""
        self.authenticate_admin()
        
        response = self.client.get(f'{self.payments_url}?gateway=stripe')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['payments']), 1)
        self.assertEqual(response.data['payments'][0]['gateway'], 'stripe')
    
    def test_search_payments(self):
        """Testa a busca de pagamentos."""
        self.authenticate_admin()
        
        # Buscar por ID do pedido
        response = self.client.get(f'{self.payments_url}?search={self.order1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['payments']), 1)


class PaymentIntegrationTest(APITestCase):
    """
    Testes de integração para o fluxo completo de pagamentos.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Produto Teste',
            price=Decimal('100.00'),
            stock_quantity=10,
            sku='PROD001'
        )
    
    def authenticate_user(self):
        """Autentica o usuário para os testes."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_complete_payment_flow(self):
        """Testa o fluxo completo de pagamento."""
        self.authenticate_user()
        
        # 1. Criar método de pagamento
        payment_method_data = {
            'type': 'credit_card',
            'name': 'Cartão Teste',
            'card_number': '4111111111111111',
            'card_expiry_month': 12,
            'card_expiry_year': 2025,
            'card_cvv': '123'
        }
        
        response = self.client.post('/api/v1/payment-methods/', payment_method_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment_method_id = response.data['payment_method']['id']
        
        # 2. Criar pedido
        order_data = {
            'shipping_address': 'Rua Teste, 123',
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['order']['id']
        
        # 3. Criar pagamento
        payment_data = {
            'order_id': order_id,
            'payment_method_id': payment_method_id
        }
        
        response = self.client.post('/api/v1/payments/', payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment_id = response.data['payment']['id']
        
        # 4. Processar pagamento
        process_url = f'/api/v1/payments/{payment_id}/process/'
        response = self.client.post(process_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Verificar se o pagamento foi processado
        payment = Payment.objects.get(id=payment_id)
        self.assertIn(payment.status, ['completed', 'failed'])
        
        # 6. Se completado, criar reembolso
        if payment.status == 'completed':
            refund_data = {
                'payment_id': payment_id,
                'amount': '50.00',
                'reason': 'customer_request'
            }
            
            response = self.client.post('/api/v1/refunds/', refund_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
