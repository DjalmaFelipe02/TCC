"""
Serializers para o app de pedidos - Django REST Framework.
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress
from ..products.models import Product
from ..users.serializers import UserListSerializer


class ShippingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer para endereços de entrega.
    """
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'name', 'street', 'number', 'complement',
            'neighborhood', 'city', 'state', 'zip_code', 'country',
            'is_default', 'full_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_zip_code(self, value):
        """Valida o formato do CEP."""
        import re
        # Remove caracteres não numéricos
        zip_code = re.sub(r'\D', '', value)
        
        if len(zip_code) != 8:
            raise serializers.ValidationError("CEP deve ter 8 dígitos.")
        
        return f"{zip_code[:5]}-{zip_code[5:]}"
    
    def validate_state(self, value):
        """Valida o código do estado."""
        if len(value) != 2:
            raise serializers.ValidationError("Estado deve ter 2 caracteres.")
        return value.upper()


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer para itens de pedido.
    """
    product_name = serializers.ReadOnlyField()
    product_sku = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    unit_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'unit_price',
            'product_name', 'product_sku', 'total_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de itens de pedido.
    """
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
    
    def validate_product(self, value):
        """Valida se o produto existe e está ativo."""
        if not value.is_active:
            raise serializers.ValidationError("Produto não está disponível.")
        return value
    
    def validate_quantity(self, value):
        """Valida a quantidade solicitada."""
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero.")
        return value
    
    def validate(self, attrs):
        """Valida se há estoque suficiente."""
        product = attrs['product']
        quantity = attrs['quantity']
        
        if product.stock_quantity < quantity:
            raise serializers.ValidationError({
                'quantity': f"Estoque insuficiente. Disponível: {product.stock_quantity}"
            })
        
        return attrs


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para histórico de status do pedido.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'status', 'status_display', 'notes',
            'changed_by', 'changed_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer principal para pedidos.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    user_info = UserListSerializer(source='user', read_only=True)
    
    # Campos calculados
    subtotal = serializers.ReadOnlyField()
    final_amount = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()
    
    # Campos de status
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_be_cancelled = serializers.ReadOnlyField()
    can_be_refunded = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_info', 'status', 'status_display',
            'total_amount', 'subtotal', 'final_amount',
            'shipping_address', 'shipping_cost', 'tax_amount', 'discount_amount',
            'notes', 'items_count', 'can_be_cancelled', 'can_be_refunded',
            'items', 'status_history',
            'created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at'
        ]
        read_only_fields = [
            'id', 'user', 'total_amount', 'created_at', 'updated_at',
            'confirmed_at', 'shipped_at', 'delivered_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de pedidos.
    """
    user_info = UserListSerializer(source='user', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_info', 'status', 'status_display',
            'total_amount', 'items_count', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de pedidos.
    """
    items = OrderItemCreateSerializer(many=True, write_only=True)
    shipping_address_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_address_id', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        """Valida os itens do pedido."""
        if not value:
            raise serializers.ValidationError("Pedido deve ter pelo menos um item.")
        
        # Verificar produtos duplicados
        product_ids = [item['product'].id for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Produtos duplicados não são permitidos.")
        
        return value
    
    def validate(self, attrs):
        """Validação geral do pedido."""
        user = self.context['request'].user
        
        # Se shipping_address_id foi fornecido, usar esse endereço
        if 'shipping_address_id' in attrs:
            try:
                shipping_address = ShippingAddress.objects.get(
                    id=attrs['shipping_address_id'],
                    user=user
                )
                attrs['shipping_address'] = shipping_address.full_address
            except ShippingAddress.DoesNotExist:
                raise serializers.ValidationError({
                    'shipping_address_id': 'Endereço de entrega não encontrado.'
                })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Cria um novo pedido com seus itens."""
        items_data = validated_data.pop('items')
        validated_data.pop('shipping_address_id', None)
        
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Calcular valores iniciais
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            subtotal += product.price * quantity
        
        # Calcular frete e impostos (simplificado)
        shipping_cost = Decimal('10.00') if subtotal < Decimal('100.00') else Decimal('0.00')
        tax_amount = subtotal * Decimal('0.05')  # 5% de imposto
        
        validated_data.update({
            'shipping_cost': shipping_cost,
            'tax_amount': tax_amount,
            'total_amount': subtotal + shipping_cost + tax_amount
        })
        
        # Criar o pedido
        order = Order.objects.create(**validated_data)
        
        # Criar os itens do pedido
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Criar histórico inicial
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Pedido criado',
            changed_by=user
        )
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de pedidos.
    """
    class Meta:
        model = Order
        fields = ['status', 'notes', 'shipping_address']
    
    def validate_status(self, value):
        """Valida mudanças de status."""
        if self.instance:
            current_status = self.instance.status
            
            # Definir transições válidas
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': ['refunded'],
                'cancelled': [],
                'refunded': []
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Não é possível alterar status de '{current_status}' para '{value}'"
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Atualiza o pedido e cria histórico de mudanças."""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Atualizar o pedido
        instance = super().update(instance, validated_data)
        
        # Se o status mudou, criar histórico
        if old_status != new_status:
            user = self.context['request'].user
            
            OrderStatusHistory.objects.create(
                order=instance,
                status=new_status,
                notes=f"Status alterado de '{old_status}' para '{new_status}'",
                changed_by=user
            )
            
            # Atualizar timestamps específicos
            from django.utils import timezone
            now = timezone.now()
            
            if new_status == 'confirmed':
                instance.confirmed_at = now
            elif new_status == 'shipped':
                instance.shipped_at = now
            elif new_status == 'delivered':
                instance.delivered_at = now
            
            instance.save(update_fields=['confirmed_at', 'shipped_at', 'delivered_at'])
        
        return instance


class OrderStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de pedidos.
    """
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    confirmed_orders = serializers.IntegerField()
    processing_orders = serializers.IntegerField()
    shipped_orders = serializers.IntegerField()
    delivered_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    refunded_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
