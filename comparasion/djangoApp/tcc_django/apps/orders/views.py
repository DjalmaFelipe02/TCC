"""
Views para o app de pedidos - Django REST Framework.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from decimal import Decimal

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderStatsSerializer,
    ShippingAddressSerializer,
    OrderStatusHistorySerializer
)
from ...core.permissions import IsOwnerOrAdmin, IsAdminUser
import logging

logger = logging.getLogger(__name__)


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet para endereços de entrega.
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_default', 'city', 'state']
    ordering_fields = ['created_at', 'is_default']
    ordering = ['-is_default', '-created_at']
    
    def get_queryset(self):
        """Retorna apenas endereços do usuário atual."""
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associa o endereço ao usuário atual."""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Cria um novo endereço de entrega."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                address = serializer.save()
                
                logger.info(f"Endereço criado: {address.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Endereço criado com sucesso',
                    'address': ShippingAddressSerializer(address).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar endereço: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        """Lista endereços do usuário."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'addresses': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Define um endereço como padrão."""
        try:
            address = self.get_object()
            address.is_default = True
            address.save()
            
            logger.info(f"Endereço padrão definido: {address.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Endereço definido como padrão',
                'address': ShippingAddressSerializer(address).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao definir endereço padrão: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para pedidos.
    """
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['id', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    def get_permissions(self):
        """Retorna as permissões apropriadas baseadas na ação."""
        if self.action in ['list', 'stats']:
            permission_classes = [IsAdminUser]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra pedidos baseado no usuário."""
        if self.request.user.is_superuser:
            return Order.objects.all().select_related('user').prefetch_related('items', 'status_history')
        else:
            return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items', 'status_history')
    
    def create(self, request, *args, **kwargs):
        """Cria um novo pedido."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                order = serializer.save()
                
                logger.info(f"Pedido criado: {order.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Pedido criado com sucesso',
                    'order': OrderSerializer(order).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar pedido: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        """Lista pedidos com paginação."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'orders': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'orders': serializer.data,
            'count': queryset.count()
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Busca um pedido específico."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                'success': True,
                'order': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar pedido: {e}")
            return Response({
                'error': True,
                'message': 'Pedido não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        """Atualiza um pedido."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                order = serializer.save()
                
                logger.info(f"Pedido atualizado: {order.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Pedido atualizado com sucesso',
                    'order': OrderSerializer(order).data
                })
                
            except Exception as e:
                logger.error(f"Erro ao atualizar pedido: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_orders(self, request):
        """Retorna pedidos do usuário atual."""
        queryset = Order.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'orders': serializer.data
            })
        
        serializer = OrderListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'orders': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela um pedido."""
        try:
            order = self.get_object()
            
            if not order.can_be_cancelled():
                return Response({
                    'error': True,
                    'message': 'Pedido não pode ser cancelado no status atual'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Atualizar status
            order.status = 'cancelled'
            order.save()
            
            # Criar histórico
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                notes='Pedido cancelado pelo usuário',
                changed_by=request.user
            )
            
            logger.info(f"Pedido cancelado: {order.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Pedido cancelado com sucesso',
                'order': OrderSerializer(order).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao cancelar pedido: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def confirm(self, request, pk=None):
        """Confirma um pedido (apenas admins)."""
        try:
            order = self.get_object()
            
            if order.status != 'pending':
                return Response({
                    'error': True,
                    'message': 'Apenas pedidos pendentes podem ser confirmados'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Atualizar status
            order.status = 'confirmed'
            from django.utils import timezone
            order.confirmed_at = timezone.now()
            order.save()
            
            # Criar histórico
            OrderStatusHistory.objects.create(
                order=order,
                status='confirmed',
                notes='Pedido confirmado pelo administrador',
                changed_by=request.user
            )
            
            logger.info(f"Pedido confirmado: {order.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Pedido confirmado com sucesso',
                'order': OrderSerializer(order).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao confirmar pedido: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Retorna estatísticas de pedidos."""
        try:
            orders = Order.objects.all()
            
            stats = {
                'total_orders': orders.count(),
                'pending_orders': orders.filter(status='pending').count(),
                'confirmed_orders': orders.filter(status='confirmed').count(),
                'processing_orders': orders.filter(status='processing').count(),
                'shipped_orders': orders.filter(status='shipped').count(),
                'delivered_orders': orders.filter(status='delivered').count(),
                'cancelled_orders': orders.filter(status='cancelled').count(),
                'refunded_orders': orders.filter(status='refunded').count(),
            }
            
            # Calcular receita total
            revenue_data = orders.exclude(status__in=['cancelled', 'refunded']).aggregate(
                total_revenue=Sum('total_amount'),
                average_order_value=Avg('total_amount')
            )
            
            stats.update({
                'total_revenue': revenue_data['total_revenue'] or Decimal('0.00'),
                'average_order_value': revenue_data['average_order_value'] or Decimal('0.00')
            })
            
            serializer = OrderStatsSerializer(stats)
            
            return Response({
                'success': True,
                'stats': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Retorna o histórico de status do pedido."""
        try:
            order = self.get_object()
            history = order.status_history.all()
            serializer = OrderStatusHistorySerializer(history, many=True)
            
            return Response({
                'success': True,
                'history': serializer.data,
                'count': history.count()
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
