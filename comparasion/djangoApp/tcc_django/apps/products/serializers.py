"""
Serializers para o app de produtos - Django.
"""
from rest_framework import serializers
from .models import Product, Category


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Product.
    """
    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "stock_quantity", 
            "sku", "category", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Category.
    """
    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]

