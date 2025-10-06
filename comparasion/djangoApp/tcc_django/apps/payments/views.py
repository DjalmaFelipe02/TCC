"""
Views para o app de pagamentos - Django REST Framework.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from decimal import Decimal

from .models import PaymentMethod, Payment, PaymentTransaction, Refund
from .serializers import (
    PaymentMethodSerializer,
    PaymentMethodCreateSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    RefundSerializer,
    RefundCreateSerializer,
    PaymentStatsSerializer,
    PaymentTransactionSerializer
)
from ...core.permissions import IsOwnerOrAdmin, IsAdminUser
import logging

logger = logging.getLogger(__name__)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet para métodos de pagamento.
    """
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type', 'is_default', 'is_active']
    ordering_fields = ['created_at', 'is_default']
    ordering = ['-is_default', '-created_at']
    
    def get_queryset(self):
        """Retorna apenas métodos de pagamento do usuário atual."""
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return PaymentMethodCreateSerializer
        return PaymentMethodSerializer
    
    def perform_create(self, serializer):
        """Associa o método de pagamento ao usuário atual."""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Cria um novo método de pagamento."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                payment_method = serializer.save()
                
                logger.info(f"Método de pagamento criado: {payment_method.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Método de pagamento criado com sucesso',
                    'payment_method': PaymentMethodSerializer(payment_method).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar método de pagamento: {e}")
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
        """Lista métodos de pagamento do usuário."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'payment_methods': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Define um método de pagamento como padrão."""
        try:
            payment_method = self.get_object()
            payment_method.is_default = True
            payment_method.save()
            
            logger.info(f"Método de pagamento padrão definido: {payment_method.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Método de pagamento definido como padrão',
                'payment_method': PaymentMethodSerializer(payment_method).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao definir método padrão: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desativa um método de pagamento."""
        try:
            payment_method = self.get_object()
            payment_method.is_active = False
            payment_method.save()
            
            logger.info(f"Método de pagamento desativado: {payment_method.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Método de pagamento desativado',
                'payment_method': PaymentMethodSerializer(payment_method).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao desativar método: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para pagamentos.
    """
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'gateway', 'order__user']
    search_fields = ['id', 'external_id', 'order__id']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_permissions(self):
        """Retorna as permissões apropriadas baseadas na ação."""
        if self.action in ['list', 'stats']:
            permission_classes = [IsAdminUser]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra pagamentos baseado no usuário."""
        if self.request.user.is_superuser:
            return Payment.objects.all().select_related('order', 'payment_method').prefetch_related('transactions')
        else:
            return Payment.objects.filter(order__user=self.request.user).select_related('order', 'payment_method').prefetch_related('transactions')
    
    def create(self, request, *args, **kwargs):
        """Cria um novo pagamento."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                payment = serializer.save()
                
                logger.info(f"Pagamento criado: {payment.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Pagamento criado com sucesso',
                    'payment': PaymentSerializer(payment).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar pagamento: {e}")
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
        """Lista pagamentos com paginação."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'payments': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'payments': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_payments(self, request):
        """Retorna pagamentos do usuário atual."""
        queryset = Payment.objects.filter(order__user=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'payments': serializer.data
            })
        
        serializer = PaymentSerializer(queryset, many=True)
        return Response({
            'success': True,
            'payments': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Processa um pagamento (simulação)."""
        try:
            payment = self.get_object()
            
            if payment.status != 'pending':
                return Response({
                    'error': True,
                    'message': 'Apenas pagamentos pendentes podem ser processados'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Simulação de processamento
            import random
            success = random.choice([True, True, True, False])  # 75% de sucesso
            
            if success:
                payment.status = 'completed'
                from django.utils import timezone
                payment.completed_at = timezone.now()
                
                # Criar transação de sucesso
                PaymentTransaction.objects.create(
                    payment=payment,
                    type='charge',
                    amount=payment.amount,
                    status='completed',
                    description='Pagamento processado com sucesso'
                )
            else:
                payment.status = 'failed'
                
                # Criar transação de falha
                PaymentTransaction.objects.create(
                    payment=payment,
                    type='charge',
                    amount=payment.amount,
                    status='failed',
                    description='Falha no processamento do pagamento'
                )
            
            payment.save()
            
            logger.info(f"Pagamento processado: {payment.id} - Status: {payment.status}")
            
            return Response({
                'success': True,
                'message': f'Pagamento {payment.get_status_display().lower()}',
                'payment': PaymentSerializer(payment).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela um pagamento."""
        try:
            payment = self.get_object()
            
            if not payment.can_be_cancelled():
                return Response({
                    'error': True,
                    'message': 'Pagamento não pode ser cancelado no status atual'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            payment.status = 'cancelled'
            payment.save()
            
            # Criar transação de cancelamento
            PaymentTransaction.objects.create(
                payment=payment,
                type='charge',
                amount=payment.amount,
                status='cancelled',
                description='Pagamento cancelado'
            )
            
            logger.info(f"Pagamento cancelado: {payment.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Pagamento cancelado com sucesso',
                'payment': PaymentSerializer(payment).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao cancelar pagamento: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Retorna estatísticas de pagamentos."""
        try:
            payments = Payment.objects.all()
            
            stats = {
                'total_payments': payments.count(),
                'pending_payments': payments.filter(status='pending').count(),
                'completed_payments': payments.filter(status='completed').count(),
                'failed_payments': payments.filter(status='failed').count(),
                'refunded_payments': payments.filter(status='refunded').count(),
            }
            
            # Calcular valores
            completed_payments = payments.filter(status='completed')
            refunds = Refund.objects.filter(status='completed')
            
            stats.update({
                'total_amount': completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'total_refunded': refunds.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'average_payment_value': completed_payments.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
            })
            
            # Calcular taxa de sucesso
            total = stats['total_payments']
            completed = stats['completed_payments']
            stats['success_rate'] = (completed / total * 100) if total > 0 else Decimal('0.00')
            
            serializer = PaymentStatsSerializer(stats)
            
            return Response({
                'success': True,
                'stats': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de pagamentos: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundViewSet(viewsets.ModelViewSet):
    """
    ViewSet para reembolsos.
    """
    queryset = Refund.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'reason', 'payment__order__user']
    search_fields = ['id', 'payment__id', 'payment__order__id']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer
    
    def get_permissions(self):
        """Retorna as permissões apropriadas baseadas na ação."""
        if self.action in ['list', 'approve', 'reject']:
            permission_classes = [IsAdminUser]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['retrieve']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra reembolsos baseado no usuário."""
        if self.request.user.is_superuser:
            return Refund.objects.all().select_related('payment', 'payment__order')
        else:
            return Refund.objects.filter(payment__order__user=self.request.user).select_related('payment', 'payment__order')
    
    def create(self, request, *args, **kwargs):
        """Cria uma solicitação de reembolso."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                refund = serializer.save()
                
                logger.info(f"Reembolso solicitado: {refund.id} por {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Solicitação de reembolso criada com sucesso',
                    'refund': RefundSerializer(refund).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar reembolso: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Aprova um reembolso (apenas admins)."""
        try:
            refund = self.get_object()
            
            if refund.status != 'pending':
                return Response({
                    'error': True,
                    'message': 'Apenas reembolsos pendentes podem ser aprovados'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refund.status = 'completed'
            from django.utils import timezone
            refund.completed_at = timezone.now()
            refund.save()
            
            # Atualizar status do pagamento se necessário
            payment = refund.payment
            total_refunded = sum(r.amount for r in payment.refunds.filter(status='completed'))
            
            if total_refunded >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'
            
            payment.save()
            
            # Criar transação de reembolso
            PaymentTransaction.objects.create(
                payment=payment,
                type='refund',
                amount=refund.amount,
                status='completed',
                description=f'Reembolso aprovado - {refund.get_reason_display()}'
            )
            
            logger.info(f"Reembolso aprovado: {refund.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Reembolso aprovado com sucesso',
                'refund': RefundSerializer(refund).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao aprovar reembolso: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Rejeita um reembolso (apenas admins)."""
        try:
            refund = self.get_object()
            
            if refund.status != 'pending':
                return Response({
                    'error': True,
                    'message': 'Apenas reembolsos pendentes podem ser rejeitados'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refund.status = 'cancelled'
            refund.notes = request.data.get('notes', 'Reembolso rejeitado pelo administrador')
            refund.save()
            
            logger.info(f"Reembolso rejeitado: {refund.id} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Reembolso rejeitado',
                'refund': RefundSerializer(refund).data
            })
            
        except Exception as e:
            logger.error(f"Erro ao rejeitar reembolso: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
