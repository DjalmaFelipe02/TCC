from rest_framework import serializers
from .models import PaymentMethod, Payment
class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta: model=PaymentMethod; fields=['id','user','type','name','is_default','is_active','created_at']
class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model=Payment; fields=['id','order','payment_method','amount','currency','status','payment_date','created_at']
