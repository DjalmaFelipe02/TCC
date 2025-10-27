from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from apps.products.models import Product
from apps.users.models import User

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True, required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'user', 'address', 'total_amount', 'created_at', 'items']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        total = 0
        for it in items_data:
            prod = it['product']
            qty = it.get('quantity', 1)
            OrderItem.objects.create(order=order, product=prod, quantity=qty)
            total += prod.price * qty
        order.total_amount = total
        order.save()
        return order