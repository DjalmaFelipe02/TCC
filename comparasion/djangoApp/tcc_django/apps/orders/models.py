"""
Modelos para o app de pedidos - Django.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Order(models.Model):
    """
    Modelo para pedidos.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('processing', 'Processando'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='Usuário'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor Total'
    )
    shipping_address = models.TextField(verbose_name='Endereço de Entrega')
    shipping_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Custo do Frete'
    )
    tax_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Valor dos Impostos'
    )
    discount_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Valor do Desconto'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmado em')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregue em')
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Pedido {self.id} - {self.user.username}"
    
    @property
    def subtotal(self):
        """Calcula o subtotal dos itens do pedido."""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def final_amount(self):
        """Calcula o valor final do pedido."""
        return self.subtotal + self.shipping_cost + self.tax_amount - self.discount_amount
    
    @property
    def items_count(self):
        """Retorna o número total de itens no pedido."""
        return sum(item.quantity for item in self.items.all())
    
    def can_be_cancelled(self):
        """Verifica se o pedido pode ser cancelado."""
        return self.status in ['pending', 'confirmed']
    
    def can_be_refunded(self):
        """Verifica se o pedido pode ser reembolsado."""
        return self.status in ['delivered']
    
    def update_total(self):
        """Atualiza o valor total do pedido baseado nos itens."""
        self.total_amount = self.final_amount
        self.save(update_fields=['total_amount', 'updated_at'])


class OrderItem(models.Model):
    """
    Modelo para itens de pedido.
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade'
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço Unitário'
    )
    
    # Campos para armazenar informações do produto no momento da compra
    product_name = models.CharField(max_length=200, verbose_name='Nome do Produto')
    product_sku = models.CharField(max_length=50, blank=True, verbose_name='SKU do Produto')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
        unique_together = ['order', 'product']
        indexes = [
            models.Index(fields=['order', 'product']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name} - Pedido {self.order.id}"
    
    @property
    def total_price(self):
        """Calcula o preço total do item."""
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para armazenar informações do produto."""
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_sku:
            self.product_sku = self.product.sku or ''
        if not self.unit_price:
            self.unit_price = self.product.price
        
        super().save(*args, **kwargs)
        
        # Atualizar total do pedido
        self.order.update_total()


class OrderStatusHistory(models.Model):
    """
    Modelo para histórico de status do pedido.
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='status_history',
        verbose_name='Pedido'
    )
    status = models.CharField(
        max_length=20, 
        choices=Order.STATUS_CHOICES,
        verbose_name='Status'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    changed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Alterado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Históricos de Status'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Pedido {self.order.id} - {self.get_status_display()} em {self.created_at}"


class ShippingAddress(models.Model):
    """
    Modelo para endereços de entrega.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='shipping_addresses',
        verbose_name='Usuário'
    )
    name = models.CharField(max_length=100, verbose_name='Nome')
    street = models.CharField(max_length=200, verbose_name='Rua')
    number = models.CharField(max_length=20, verbose_name='Número')
    complement = models.CharField(max_length=100, blank=True, verbose_name='Complemento')
    neighborhood = models.CharField(max_length=100, verbose_name='Bairro')
    city = models.CharField(max_length=100, verbose_name='Cidade')
    state = models.CharField(max_length=2, verbose_name='Estado')
    zip_code = models.CharField(max_length=10, verbose_name='CEP')
    country = models.CharField(max_length=50, default='Brasil', verbose_name='País')
    is_default = models.BooleanField(default=False, verbose_name='Endereço Padrão')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'shipping_addresses'
        verbose_name = 'Endereço de Entrega'
        verbose_name_plural = 'Endereços de Entrega'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['zip_code']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.street}, {self.number} - {self.city}/{self.state}"
    
    @property
    def full_address(self):
        """Retorna o endereço completo formatado."""
        address_parts = [
            f"{self.street}, {self.number}",
            self.complement,
            self.neighborhood,
            f"{self.city}/{self.state}",
            f"CEP: {self.zip_code}",
            self.country
        ]
        return " - ".join(part for part in address_parts if part)
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para garantir apenas um endereço padrão por usuário."""
        if self.is_default:
            # Remove o padrão de outros endereços do mesmo usuário
            ShippingAddress.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
