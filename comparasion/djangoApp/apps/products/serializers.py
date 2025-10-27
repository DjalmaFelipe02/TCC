from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    # converte automaticamente o ID em instância Category
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'category_id', 'created_at']

    def create(self, validated_data):
        cat = validated_data.pop('category_id', None)
        if cat is not None:
            validated_data['category'] = cat
        return super().create(validated_data)

    def update(self, instance, validated_data):
        cat = validated_data.pop('category_id', None)
        if cat is not None:
            instance.category = cat
        return super().update(instance, validated_data)
