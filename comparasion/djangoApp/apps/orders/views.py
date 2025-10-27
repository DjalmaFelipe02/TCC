from rest_framework import viewsets, generics
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from rest_framework.permissions import AllowAny

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    lookup_field = 'id'
    lookup_value_regex = r'[0-9a-fA-F\-]+'  # aceita UUID com hífens

class OrderItemsByOrderAPIView(generics.ListCreateAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderItem.objects.filter(order_id=order_id)

    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        serializer.save(order_id=order_id)
