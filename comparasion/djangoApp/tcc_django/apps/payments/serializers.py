"""
Serializers para o app de pagamentos - Django REST Framework.
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

from .models import PaymentMethod, Payment, PaymentTransaction, Refund, PaymentWebhook
from ..orders.models import Order


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer para métodos de pagamento.
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'type_display', 'name', 'is_default', 'is_active',
            'card_last_four', 'card_brand', 'card_expiry_month', 'card_expiry_year',
            'account_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'account_info': {'write_only': True}
        }
    
    def validate(self, attrs):
        """Validação específica por tipo de método."""
        method_type = attrs.get('type')
        
        if method_type in ['credit_card', 'debit_card']:
            required_fields = ['card_last_four', 'card_brand', 'card_expiry_month', 'card_expiry_year']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: f"Campo obrigatório para {method_type}"
                    })
        
        return attrs


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de métodos de pagamento.
    """
    # Campos temporários para cartão (não salvos no banco)
    card_number = serializers.CharField(write_only=True, required=False)
    card_cvv = serializers.CharField(write_only=True, required=False)
    cardholder_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'type', 'name', 'is_default',
            'card_number', 'card_cvv', 'cardholder_name',
            'card_expiry_month', 'card_expiry_year',
            'account_info'
        ]
    
    def validate_card_number(self, value):
        """Valida número do cartão."""
        if value:
            # Remove espaços e caracteres especiais
            card_number = ''.join(filter(str.isdigit, value))
            
            if len(card_number) < 13 or len(card_number) > 19:
                raise serializers.ValidationError("Número do cartão inválido")
            
            return card_number
        return value
    
    def validate(self, attrs):
        """Validação específica por tipo."""
        method_type = attrs.get('type')
        
        if method_type in ['credit_card', 'debit_card']:
            required_fields = ['card_number', 'card_expiry_month', 'card_expiry_year']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: f"Campo obrigatório para {method_type}"
                    })
        
        return attrs
    
    def create(self, validated_data):
        """Cria método de pagamento processando dados do cartão."""
        # Extrair dados temporários
        card_number = validated_data.pop('card_number', '')
        card_cvv = validated_data.pop('card_cvv', '')
        cardholder_name = validated_data.pop('cardholder_name', '')
        
        # Processar dados do cartão
        if card_number:
            validated_data['card_last_four'] = card_number[-4:]
            validated_data['card_brand'] = self._detect_card_brand(card_number)
        
        # Associar ao usuário
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)
    
    def _detect_card_brand(self, card_number):
        """Detecta a bandeira do cartão baseado no número."""
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith('5') or card_number.startswith('2'):
            return 'Mastercard'
        elif card_number.startswith('3'):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        else:
            return 'Outros'


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para transações de pagamento.
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'type', 'type_display', 'amount', 'status', 'status_display',
            'external_id', 'description', 'notes',
            'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer principal para pagamentos.
    """
    payment_method_info = PaymentMethodSerializer(source='payment_method', read_only=True)
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Propriedades calculadas
    is_successful = serializers.ReadOnlyField()
    can_be_refunded = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'payment_method', 'payment_method_info',
            'amount', 'currency', 'status', 'status_display',
            'external_id', 'gateway', 'description', 'metadata',
            'is_successful', 'can_be_refunded', 'can_be_cancelled',
            'transactions',
            'created_at', 'updated_at', 'processed_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processed_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de pagamentos.
    """
    order_id = serializers.UUIDField(write_only=True)
    payment_method_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'order_id', 'payment_method_id', 'amount', 'description'
        ]
    
    def validate_order_id(self, value):
        """Valida se o pedido existe e pertence ao usuário."""
        user = self.context['request'].user
        
        try:
            order = Order.objects.get(id=value)
            if not user.is_superuser and order.user != user:
                raise serializers.ValidationError("Pedido não encontrado")
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Pedido não encontrado")
    
    def validate_payment_method_id(self, value):
        """Valida se o método de pagamento existe e pertence ao usuário."""
        user = self.context['request'].user
        
        try:
            payment_method = PaymentMethod.objects.get(id=value, user=user, is_active=True)
            return payment_method
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Método de pagamento não encontrado")
    
    def validate(self, attrs):
        """Validação geral do pagamento."""
        order = attrs['order_id']
        amount = attrs.get('amount')
        
        # Verificar se o pedido pode receber pagamento
        if order.status not in ['pending', 'confirmed']:
            raise serializers.ValidationError({
                'order_id': 'Pedido não pode receber pagamento no status atual'
            })
        
        # Verificar se o valor está correto
        if amount and amount != order.total_amount:
            raise serializers.ValidationError({
                'amount': 'Valor do pagamento deve ser igual ao valor do pedido'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Cria um novo pagamento."""
        order = validated_data.pop('order_id')
        payment_method = validated_data.pop('payment_method_id')
        
        # Se amount não foi fornecido, usar o valor do pedido
        if 'amount' not in validated_data:
            validated_data['amount'] = order.total_amount
        
        validated_data.update({
            'order': order,
            'payment_method': payment_method,
            'currency': 'BRL',
            'gateway': 'internal'  # Gateway interno simplificado
        })
        
        payment = Payment.objects.create(**validated_data)
        
        # Criar transação inicial
        PaymentTransaction.objects.create(
            payment=payment,
            type='charge',
            amount=payment.amount,
            status='pending',
            description='Cobrança inicial'
        )
        
        return payment


class RefundSerializer(serializers.ModelSerializer):
    """
    Serializer para reembolsos.
    """
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    is_partial = serializers.ReadOnlyField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason', 'reason_display',
            'status', 'status_display', 'description', 'notes',
            'requested_by', 'requested_by_username', 'is_partial',
            'created_at', 'updated_at', 'processed_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processed_at', 'completed_at'
        ]


class RefundCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de reembolsos.
    """
    payment_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Refund
        fields = ['payment_id', 'amount', 'reason', 'description']
    
    def validate_payment_id(self, value):
        """Valida se o pagamento existe e pode ser reembolsado."""
        try:
            payment = Payment.objects.get(id=value)
            if not payment.can_be_refunded:
                raise serializers.ValidationError("Pagamento não pode ser reembolsado")
            return payment
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Pagamento não encontrado")
    
    def validate(self, attrs):
        """Validação do reembolso."""
        payment = attrs['payment_id']
        amount = attrs.get('amount')
        
        if amount and amount > payment.amount:
            raise serializers.ValidationError({
                'amount': 'Valor do reembolso não pode ser maior que o valor do pagamento'
            })
        
        # Verificar reembolsos anteriores
        total_refunded = sum(
            refund.amount for refund in payment.refunds.filter(status='completed')
        )
        
        if amount and (total_refunded + amount) > payment.amount:
            available = payment.amount - total_refunded
            raise serializers.ValidationError({
                'amount': f'Valor disponível para reembolso: {available}'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Cria um novo reembolso."""
        payment = validated_data.pop('payment_id')
        
        # Se amount não foi fornecido, reembolsar o valor total disponível
        if 'amount' not in validated_data:
            total_refunded = sum(
                refund.amount for refund in payment.refunds.filter(status='completed')
            )
            validated_data['amount'] = payment.amount - total_refunded
        
        validated_data.update({
            'payment': payment,
            'requested_by': self.context['request'].user
        })
        
        return super().create(validated_data)


class PaymentStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de pagamentos.
    """
    total_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    completed_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    refunded_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_refunded = serializers.DecimalField(max_digits=12, decimal_places=2)
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_payment_value = serializers.DecimalField(max_digits=10, decimal_places=2)
