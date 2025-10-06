"""
Views da API REST para usuários - Django.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User
from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    UserUpdateSerializer,
    LoginSerializer,
    UserListSerializer
)
from ...core.permissions import IsOwnerOrAdmin, IsAdminUser
import logging

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    View para registro de novos usuários.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Registra um novo usuário."""
        serializer = UserCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Gerar tokens JWT
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                
                logger.info(f"Novo usuário registrado: {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Usuário criado com sucesso',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(access_token),
                        'refresh': str(refresh),
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao registrar usuário: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    View para autenticação de usuários.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Autentica um usuário e retorna tokens JWT."""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username_or_email = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            # Buscar usuário por username ou email
            try:
                user = User.objects.get(
                    Q(username=username_or_email) | Q(email=username_or_email)
                )
            except User.DoesNotExist:
                return Response({
                    'error': True,
                    'message': 'Credenciais inválidas'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verificar senha
            if not user.check_password(password):
                return Response({
                    'error': True,
                    'message': 'Credenciais inválidas'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verificar se usuário está ativo
            if not user.is_active:
                return Response({
                    'error': True,
                    'message': 'Conta desativada'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Gerar tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            logger.info(f"Login realizado: {user.username}")
            
            return Response({
                'success': True,
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'token_type': 'Bearer',
                'expires_in': 1800,  # 30 minutos
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de usuários.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['created_at', 'username', 'email']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Retorna as permissões apropriadas baseadas na ação."""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Cria um novo usuário."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                logger.info(f"Usuário criado via API: {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Usuário criado com sucesso',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erro ao criar usuário: {e}")
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
        """Lista usuários com paginação."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'users': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'users': serializer.data,
            'count': queryset.count()
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Busca um usuário específico."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                'success': True,
                'user': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return Response({
                'error': True,
                'message': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        """Atualiza um usuário."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                logger.info(f"Usuário atualizado: {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Usuário atualizado com sucesso',
                    'user': UserSerializer(user).data
                })
                
            except Exception as e:
                logger.error(f"Erro ao atualizar usuário: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Deleta um usuário."""
        try:
            instance = self.get_object()
            
            # Não permitir deletar a si mesmo
            if instance == request.user:
                return Response({
                    'error': True,
                    'message': 'Não é possível deletar sua própria conta'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            username = instance.username
            instance.delete()
            
            logger.info(f"Usuário deletado: {username} por {request.user.username}")
            
            return Response({
                'success': True,
                'message': 'Usuário deletado com sucesso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao deletar usuário: {e}")
            return Response({
                'error': True,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Retorna o perfil do usuário atual."""
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Atualiza o perfil do usuário atual."""
        partial = request.method == 'PATCH'
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                logger.info(f"Perfil atualizado: {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Perfil atualizado com sucesso',
                    'user': UserSerializer(user).data
                })
                
            except Exception as e:
                logger.error(f"Erro ao atualizar perfil: {e}")
                return Response({
                    'error': True,
                    'message': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Dados inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def search(self, request):
        """Busca usuários por texto."""
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        if not query:
            return Response({
                'error': True,
                'message': 'Parâmetro de busca é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(full_name__icontains=query)
        )[:limit]
        
        serializer = UserListSerializer(users, many=True)
        
        logger.info(f"Busca de usuários realizada: '{query}' por {request.user.username}")
        
        return Response({
            'success': True,
            'query': query,
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Retorna estatísticas de usuários."""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(is_superuser=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        
        return Response({
            'success': True,
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'admin_users': admin_users,
                'verified_users': verified_users,
                'unverified_users': total_users - verified_users
            }
        })
