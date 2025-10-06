"""
Modelos para o app de pagamentos - Django.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """
    Modelo para métodos de pagamento.
    """
    TYPE_CHOICES = [
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('paypal', 'PayPal'),
        ('pix', 'PIX'),
        ('bank_transfer', 'Transferência Bancária'),
        ('boleto', 'Boleto Bancário'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payment_methods',
        verbose_name='Usuário'
    )
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name='Tipo'
    )
    name = models.CharField(max_length=100, verbose_name='Nome do Método')
    is_default = models.BooleanField(default=False, verbose_name='Método Padrão')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Campos específicos para cartões
    card_last_four = models.CharField(max_length=4, blank=True, verbose_name='Últimos 4 dígitos')
    card_brand = models.CharField(max_length=20, blank=True, verbose_name='Bandeira do Cartão')
    card_expiry_month = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mês de Expiração'
    )
    card_expiry_year = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(2024)],
        verbose_name='Ano de Expiração'
    )
    
    # Campos específicos para outros métodos
    account_info = models.JSONField(default=dict, blank=True, verbose_name='Informações da Conta')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Método de Pagamento'
        verbose_name_plural = 'Métodos de Pagamento'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['type', 'is_active']),
        ]
    
    def __str__(self):
        if self.type in ['credit_card', 'debit_card']:
            return f"{self.get_type_display()} **** {self.card_last_four}"
        return f"{self.get_type_display()} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para garantir apenas um método padrão por usuário."""
        if self.is_default:
            # Remove o padrão de outros métodos do mesmo usuário
            PaymentMethod.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Modelo para pagamentos.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('partially_refunded', 'Parcialmente Reembolsado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        'orders.Order', 
        on_delete=models.CASCADE, 
        related_name='payments',
        verbose_name='Pedido'
    )
    payment_method = models.ForeignKey(
        PaymentMethod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Método de Pagamento'
    )
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor'
    )
    currency = models.CharField(max_length=3, default='BRL', verbose_name='Moeda')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    
    # Identificadores externos
    external_id = models.CharField(max_length=100, blank=True, verbose_name='ID Externo')
    gateway = models.CharField(max_length=50, blank=True, verbose_name='Gateway de Pagamento')
    
    # Informações adicionais
    description = models.TextField(blank=True, verbose_name='Descrição')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadados')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_id']),
            models.Index(fields=['gateway', 'external_id']),
        ]
    
    def __str__(self):
        return f"Pagamento {self.id} - Pedido {self.order.id} - {self.get_status_display()}"
    
    @property
    def is_successful(self):
        """Verifica se o pagamento foi bem-sucedido."""
        return self.status == 'completed'
    
    @property
    def can_be_refunded(self):
        """Verifica se o pagamento pode ser reembolsado."""
        return self.status in ['completed']
    
    @property
    def can_be_cancelled(self):
        """Verifica se o pagamento pode ser cancelado."""
        return self.status in ['pending', 'processing']


class PaymentTransaction(models.Model):
    """
    Modelo para transações de pagamento (histórico detalhado).
    """
    TYPE_CHOICES = [
        ('charge', 'Cobrança'),
        ('refund', 'Reembolso'),
        ('partial_refund', 'Reembolso Parcial'),
        ('chargeback', 'Chargeback'),
        ('fee', 'Taxa'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name='Pagamento'
    )
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name='Tipo'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor'
    )
    status = models.CharField(
        max_length=20, 
        choices=Payment.STATUS_CHOICES,
        verbose_name='Status'
    )
    
    # Identificadores externos
    external_id = models.CharField(max_length=100, blank=True, verbose_name='ID Externo')
    gateway_response = models.JSONField(default=dict, blank=True, verbose_name='Resposta do Gateway')
    
    # Informações adicionais
    description = models.TextField(blank=True, verbose_name='Descrição')
    notes = models.TextField(blank=True, verbose_name='Observações')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transação de Pagamento'
        verbose_name_plural = 'Transações de Pagamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'type']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} - {self.get_status_display()}"


class Refund(models.Model):
    """
    Modelo para reembolsos.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]
    
    REASON_CHOICES = [
        ('customer_request', 'Solicitação do Cliente'),
        ('duplicate_charge', 'Cobrança Duplicada'),
        ('fraudulent', 'Fraudulento'),
        ('product_not_received', 'Produto Não Recebido'),
        ('product_defective', 'Produto Defeituoso'),
        ('other', 'Outro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='refunds',
        verbose_name='Pagamento'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor'
    )
    reason = models.CharField(
        max_length=30, 
        choices=REASON_CHOICES,
        verbose_name='Motivo'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    
    # Identificadores externos
    external_id = models.CharField(max_length=100, blank=True, verbose_name='ID Externo')
    
    # Informações adicionais
    description = models.TextField(blank=True, verbose_name='Descrição')
    notes = models.TextField(blank=True, verbose_name='Observações Internas')
    
    # Usuário que solicitou o reembolso
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Solicitado por'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    
    class Meta:
        db_table = 'refunds'
        verbose_name = 'Reembolso'
        verbose_name_plural = 'Reembolsos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['reason']),
        ]
    
    def __str__(self):
        return f"Reembolso {self.id} - {self.amount} - {self.get_status_display()}"
    
    @property
    def is_partial(self):
        """Verifica se é um reembolso parcial."""
        return self.amount < self.payment.amount


class PaymentWebhook(models.Model):
    """
    Modelo para webhooks de pagamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gateway = models.CharField(max_length=50, verbose_name='Gateway')
    event_type = models.CharField(max_length=100, verbose_name='Tipo de Evento')
    external_id = models.CharField(max_length=100, verbose_name='ID Externo')
    
    # Dados do webhook
    payload = models.JSONField(verbose_name='Payload')
    headers = models.JSONField(default=dict, verbose_name='Headers')
    
    # Status do processamento
    processed = models.BooleanField(default=False, verbose_name='Processado')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    
    # Relacionamento com pagamento (se identificado)
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='webhooks',
        verbose_name='Pagamento'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        db_table = 'payment_webhooks'
        verbose_name = 'Webhook de Pagamento'
        verbose_name_plural = 'Webhooks de Pagamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gateway', 'event_type']),
            models.Index(fields=['external_id']),
            models.Index(fields=['processed', 'created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.gateway} - {self.event_type} - {self.external_id}"
