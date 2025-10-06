"""
Modelos de produto para a aplicação Django.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid


class Category(models.Model):
    """
    Modelo para categorias de produtos.
    """
    
    name = models.CharField(
        _('name'),
        max_length=100,
        unique=True,
        help_text=_('Name of the category.')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the category.')
    )
    slug = models.SlugField(
        _('slug'),
        unique=True,
        help_text=_('URL-friendly version of the name.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this category is active.')
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
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """
    Modelo de produto.
    """
    
    # Identificação
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Name of the product.')
    )
    description = models.TextField(
        _('description'),
        help_text=_('Detailed description of the product.')
    )
    short_description = models.CharField(
        _('short description'),
        max_length=255,
        blank=True,
        help_text=_('Brief description of the product.')
    )
    
    # Categorização
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('category')
    )
    
    # Preços e estoque
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Price of the product.')
    )
    cost_price = models.DecimalField(
        _('cost price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        help_text=_('Cost price of the product.')
    )
    stock_quantity = models.PositiveIntegerField(
        _('stock quantity'),
        default=0,
        help_text=_('Available quantity in stock.')
    )
    min_stock_level = models.PositiveIntegerField(
        _('minimum stock level'),
        default=5,
        help_text=_('Minimum stock level before alert.')
    )
    
    # Identificadores
    sku = models.CharField(
        _('SKU'),
        max_length=50,
        unique=True,
        help_text=_('Stock Keeping Unit - unique identifier.')
    )
    barcode = models.CharField(
        _('barcode'),
        max_length=50,
        blank=True,
        help_text=_('Product barcode.')
    )
    
    # Características físicas
    weight = models.DecimalField(
        _('weight (kg)'),
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_('Weight of the product in kilograms.')
    )
    dimensions_length = models.DecimalField(
        _('length (cm)'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    dimensions_width = models.DecimalField(
        _('width (cm)'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    dimensions_height = models.DecimalField(
        _('height (cm)'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # Status e configurações
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this product is active and available for sale.')
    )
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('Whether this product is featured.')
    )
    is_digital = models.BooleanField(
        _('digital product'),
        default=False,
        help_text=_('Whether this is a digital product.')
    )
    
    # SEO e URLs
    slug = models.SlugField(
        _('slug'),
        unique=True,
        help_text=_('URL-friendly version of the name.')
    )
    meta_title = models.CharField(
        _('meta title'),
        max_length=60,
        blank=True,
        help_text=_('SEO meta title.')
    )
    meta_description = models.CharField(
        _('meta description'),
        max_length=160,
        blank=True,
        help_text=_('SEO meta description.')
    )
    
    # Auditoria
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        """Verifica se o produto está em estoque."""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Verifica se o estoque está baixo."""
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def profit_margin(self):
        """Calcula a margem de lucro."""
        if self.cost_price and self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def reduce_stock(self, quantity):
        """Reduz o estoque do produto."""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save(update_fields=['stock_quantity'])
            return True
        return False
    
    def increase_stock(self, quantity):
        """Aumenta o estoque do produto."""
        self.stock_quantity += quantity
        self.save(update_fields=['stock_quantity'])


class ProductImage(models.Model):
    """
    Modelo para imagens de produtos.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product')
    )
    image = models.ImageField(
        _('image'),
        upload_to='products/',
        help_text=_('Product image.')
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=255,
        blank=True,
        help_text=_('Alternative text for the image.')
    )
    is_primary = models.BooleanField(
        _('primary image'),
        default=False,
        help_text=_('Whether this is the primary image.')
    )
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
        help_text=_('Display order of the image.')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"
