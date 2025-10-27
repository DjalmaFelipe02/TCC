import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from apps.orders.models import Order
from apps.users.models import User
class PaymentMethod(models.Model):
    TYPE_CHOICES = [
        ('credit_card','Cartão de Crédito'),
        ('debit_card','Cartão de Débito'),
        ('paypal','PayPal'),
        ('pix','PIX'),
        ('bank_transfer','Transferência Bancária'),
        ('boleto','Boleto Bancário'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.name} ({self.type})'
class Payment(models.Model):
    STATUS_CHOICES = [('pending','pending'),('completed','completed'),('failed','failed')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='BRL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'Payment {self.id} {self.status}'
