"""
Modelos de usuário para a aplicação Django.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions_set",
        related_query_name="custom_user_permission",
    )

    """
    Modelo de usuário personalizado baseado no AbstractUser do Django.
    """
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Enter a valid email address.')
    )
    full_name = models.CharField(
        _('full name'),
        max_length=150,
        help_text=_('Full name of the user.')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Phone number of the user.')
    )
    birth_date = models.DateField(
        _('birth date'),
        null=True,
        blank=True,
        help_text=_('Birth date of the user.')
    )
    
    # Campos adicionais
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    # Configurações do modelo
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def get_full_name(self):
        """Retorna o nome completo do usuário."""
        return self.full_name
    
    def get_short_name(self):
        """Retorna o primeiro nome do usuário."""
        return self.full_name.split()[0] if self.full_name else self.username
    
    @property
    def is_profile_complete(self):
        """Verifica se o perfil do usuário está completo."""
        return all([
            self.full_name,
            self.email,
            self.phone,
        ])


class UserProfile(models.Model):
    """
    Modelo para informações adicionais do perfil do usuário.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    bio = models.TextField(
        _('biography'),
        max_length=500,
        blank=True,
        help_text=_('Brief description about the user.')
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Profile picture of the user.')
    )
    website = models.URLField(
        _('website'),
        blank=True,
        help_text=_('Personal website of the user.')
    )
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('Location of the user.')
    )
    
    # Configurações de privacidade
    show_email = models.BooleanField(
        _('show email'),
        default=False,
        help_text=_('Whether to show email in public profile.')
    )
    show_phone = models.BooleanField(
        _('show phone'),
        default=False,
        help_text=_('Whether to show phone in public profile.')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
