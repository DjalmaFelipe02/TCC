"""
Middleware personalizado para a aplicação Django.
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de requisições e respostas.
    """
    
    def process_request(self, request):
        """Processa a requisição antes de chegar à view."""
        request.start_time = time.time()
        
        # Log da requisição
        logger.info(
            f"REQUEST: {request.method} {request.path} - "
            f"User: {getattr(request.user, 'username', 'Anonymous')} - "
            f"IP: {self.get_client_ip(request)}"
        )
        
        return None
    
    def process_response(self, request, response):
        """Processa a resposta antes de enviar ao cliente."""
        # Calcula o tempo de processamento
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log da resposta
            logger.info(
                f"RESPONSE: {request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Processa exceções não tratadas."""
        logger.error(
            f"EXCEPTION: {request.method} {request.path} - "
            f"Error: {str(exception)} - "
            f"Type: {type(exception).__name__}"
        )
        
        # Em modo de produção, retorna uma resposta JSON genérica
        if not settings.DEBUG:
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': 'Ocorreu um erro interno no servidor.'
            }, status=500)
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Obtém o IP real do cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar headers de segurança.
    """
    
    def process_response(self, request, response):
        """Adiciona headers de segurança à resposta."""
        # Headers de segurança
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (básico)
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self';"
            )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware simples para rate limiting.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}  # Em produção, use Redis ou Memcached
        super().__init__(get_response)
    
    def process_request(self, request):
        """Verifica se a requisição está dentro do limite."""
        # Implementação básica - em produção use uma solução mais robusta
        client_ip = LoggingMiddleware.get_client_ip(request)
        current_time = time.time()
        
        # Limpa requisições antigas (mais de 1 minuto)
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
        else:
            self.requests[client_ip] = []
        
        # Verifica o limite (100 requisições por minuto)
        if len(self.requests[client_ip]) >= 100:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse({
                'error': 'Rate Limit Exceeded',
                'message': 'Muitas requisições. Tente novamente em alguns minutos.'
            }, status=429)
        
        # Adiciona a requisição atual
        self.requests[client_ip].append(current_time)
        
        return None
