"""
Views da API REST para produtos - Django.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from ...core.permissions import IsAdminUser
import logging

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de produtos.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "stock_quantity", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Retorna as permissões apropriadas baseadas na ação."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """Cria um novo produto."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                product = serializer.save()
                logger.info(f"Produto criado: {product.name}")
                return Response({
                    "success": True,
                    "message": "Produto criado com sucesso",
                    "product": serializer.data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Erro ao criar produto: {e}")
                return Response({
                    "error": True,
                    "message": "Erro interno do servidor"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            "error": True,
            "message": "Dados inválidos",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CategoryListView(APIView):
    """
    View para listar todas as categorias de produtos.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Retorna uma lista de todas as categorias de produtos."""
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response({
            "success": True,
            "categories": serializer.data
        })


class ProductSearchView(APIView):
    """
    View para buscar produtos.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Busca produtos por nome, descrição ou SKU."""
        query = request.query_params.get("q", "")
        if not query:
            return Response({
                "error": True,
                "message": "O parâmetro de busca \"q\" é obrigatório."
            }, status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query)
        )
        serializer = ProductSerializer(products, many=True)
        return Response({
            "success": True,
            "results": serializer.data
        })

