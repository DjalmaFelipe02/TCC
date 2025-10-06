"""
Permissões customizadas para a aplicação Django.
"""
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão customizada que permite apenas ao proprietário do objeto ou admin acessar.
    """
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura são permitidas para qualquer requisição,
        # então sempre permitimos requisições GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita são apenas para o proprietário do objeto ou admin.
        return obj.user == request.user or request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """
    Permissão customizada que permite apenas a usuários admin.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão customizada que permite apenas ao proprietário editar.
    """
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura são permitidas para qualquer requisição,
        # então sempre permitimos requisições GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita são apenas para o proprietário do objeto.
        return obj.user == request.user


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Permissão customizada que permite leitura para todos e escrita apenas para usuários autenticados.
    """
    
    def has_permission(self, request, view):
        # Permissões de leitura são permitidas para qualquer requisição,
        # então sempre permitimos requisições GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissões de escrita são apenas para usuários autenticados.
        return bool(request.user and request.user.is_authenticated)
