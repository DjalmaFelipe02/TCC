"""
Views principais da aplicação Django.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class APIRootView(APIView):
    """
    View raiz da API que fornece informações sobre os endpoints disponíveis.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        """Retorna informações sobre a API."""
        return Response({
            'message': 'Bem-vindo à API TCC Django - Padrões de Projeto',
            'version': getattr(settings, 'APP_VERSION', '2.0.0'),
            'description': getattr(settings, 'APP_DESCRIPTION', ''),
            'endpoints': {
                'auth': {
                    'token': '/api/v1/auth/token/',
                    'refresh': '/api/v1/auth/token/refresh/',
                },
                'resources': {
                    'users': '/api/v1/users/',
                    'products': '/api/v1/products/',
                    'orders': '/api/v1/orders/',
                    'payments': '/api/v1/payments/',
                },
                'patterns': {
                    'abstract_factory': '/api/v1/patterns/abstract-factory/',
                    'strategy': '/api/v1/patterns/strategy/',
                    'facade': '/api/v1/patterns/facade/',
                },
                'admin': '/admin/',
                'health': '/api/v1/health/',
            }
        })


class HealthCheckView(APIView):
    """
    View para verificação de saúde da aplicação.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        """Verifica a saúde da aplicação."""
        health_status = {
            'status': 'healthy',
            'timestamp': request.META.get('HTTP_DATE'),
            'version': getattr(settings, 'APP_VERSION', '2.0.0'),
            'debug': settings.DEBUG,
        }
        
        # Verifica conexão com o banco de dados
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_status['database'] = 'connected'
        except Exception as e:
            logger.error(f"Erro na conexão com o banco de dados: {e}")
            health_status['database'] = 'error'
            health_status['status'] = 'unhealthy'
        
        # Define o status code baseado na saúde
        status_code = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=status_code)
