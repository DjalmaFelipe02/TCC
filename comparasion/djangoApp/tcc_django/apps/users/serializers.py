"""
Serializers para usuários - Django REST Framework.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal para usuários.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 
            'is_active', 'is_superuser', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de usuários.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 
            'is_active', 'is_superuser', 'created_at'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de usuários.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'full_name', 
            'password', 'password_confirm'
        ]
    
    def validate_username(self, value):
        """Valida se o username é único."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Nome de usuário já existe.")
        return value
    
    def validate_email(self, value):
        """Valida se o email é único."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email já está em uso.")
        return value
    
    def validate_password(self, value):
        """Valida a senha usando os validadores do Django."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Valida se as senhas coincidem."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs
    
    def create(self, validated_data):
        """Cria um novo usuário."""
        # Remove password_confirm dos dados
        validated_data.pop('password_confirm', None)
        
        # Cria o usuário
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de usuários.
    """
    class Meta:
        model = User
        fields = ['full_name', 'email', 'is_active']
    
    def validate_email(self, value):
        """Valida se o email é único (exceto para o próprio usuário)."""
        user = self.instance
        if user and User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email já está em uso.")
        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuários.
    """
    username = serializers.CharField(
        help_text="Nome de usuário ou email"
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Senha do usuário"
    )


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer para alteração de senha.
    """
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Senha atual"
    )
    new_password = serializers.CharField(
        min_length=6,
        style={'input_type': 'password'},
        help_text="Nova senha"
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Confirmação da nova senha"
    )
    
    def validate_old_password(self, value):
        """Valida se a senha atual está correta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value
    
    def validate_new_password(self, value):
        """Valida a nova senha."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Valida se as novas senhas coincidem."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'As senhas não coincidem.'
            })
        return attrs
    
    def save(self):
        """Altera a senha do usuário."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil completo do usuário.
    """
    full_name = serializers.CharField(max_length=150)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name',
            'is_active', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'is_active', 'is_verified', 
            'created_at', 'updated_at'
        ]
