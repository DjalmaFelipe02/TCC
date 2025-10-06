"""
Endpoints da API REST para produtos - Flask.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from sqlalchemy.exc import IntegrityError

from ...core.database import db
from ...core.security import require_auth, require_admin
from ...models.product import Product
from ...models.user import User
from ...core.logging import get_logger

logger = get_logger("products_api")
bp = Blueprint('products', __name__, url_prefix='/api/v1/products')


# ============================================================================
# SCHEMAS DE VALIDAÇÃO
# ============================================================================

class ProductCreateSchema(Schema):
    """Schema para criação de produto."""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str()
    price = fields.Decimal(required=True, validate=validate.Range(min=0))
    stock_quantity = fields.Int(validate=validate.Range(min=0), load_default=0)
    sku = fields.Str(validate=validate.Length(max=50))
    category = fields.Str(validate=validate.Length(max=100))


class ProductUpdateSchema(Schema):
    """Schema para atualização de produto."""
    name = fields.Str(validate=validate.Length(min=2, max=200))
    description = fields.Str()
    price = fields.Decimal(validate=validate.Range(min=0))
    stock_quantity = fields.Int(validate=validate.Range(min=0))
    sku = fields.Str(validate=validate.Length(max=50))
    category = fields.Str(validate=validate.Length(max=100))
    is_active = fields.Bool()


class StockUpdateSchema(Schema):
    """Schema para atualização de estoque."""
    quantity = fields.Int(required=True)
    reason = fields.Str()


# Instâncias dos schemas
product_create_schema = ProductCreateSchema()
product_update_schema = ProductUpdateSchema()
stock_update_schema = StockUpdateSchema()


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def product_to_dict(product):
    """Converte produto para dicionário."""
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price) if product.price else 0,
        'stock_quantity': product.stock_quantity,
        'sku': product.sku,
        'category': product.category,
        'is_active': product.is_active,
        'is_in_stock': product.is_in_stock,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'updated_at': product.updated_at.isoformat() if product.updated_at else None
    }


def paginate_query(query, page, per_page):
    """Aplica paginação a uma query."""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages
    }


# ============================================================================
# ENDPOINTS DE PRODUTOS
# ============================================================================

@bp.route('/', methods=['POST'])
@require_admin
def create_product():
    """Cria um novo produto."""
    try:
        # Validar dados de entrada
        data = product_create_schema.load(request.get_json())
        
        # Verificar se SKU já existe (se fornecido)
        if data.get('sku'):
            existing_product = Product.get_by_sku(data['sku'])
            if existing_product:
                return jsonify({
                    'error': True,
                    'message': 'SKU já existe'
                }), 400
        
        # Criar produto
        product = Product.create_product(**data)
        
        current_username = get_jwt_identity()
        logger.info(f"Produto criado: {product.name} por {current_username}")
        
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'product': product_to_dict(product)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/', methods=['GET'])
def list_products():
    """Lista produtos com filtros e paginação."""
    try:
        # Parâmetros de query
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        in_stock_only = request.args.get('in_stock_only', 'false').lower() == 'true'
        
        # Construir query
        query = Product.query
        
        # Aplicar filtros
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)
        
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            query = query.filter(
                db.or_(
                    Product.name.contains(search),
                    Product.description.contains(search)
                )
            )
        
        # Aplicar paginação
        pagination = paginate_query(query, page, per_page)
        
        logger.info(f"Lista de produtos solicitada - Página {page}, Total: {pagination['total']}")
        
        return jsonify({
            'success': True,
            'products': [product_to_dict(product) for product in pagination['items']],
            'pagination': {
                'total': pagination['total'],
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'pages': pagination['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/categories', methods=['GET'])
def list_categories():
    """Lista todas as categorias de produtos."""
    try:
        categories = db.session.query(Product.category).filter(
            Product.category.isnot(None),
            Product.is_active == True
        ).distinct().all()
        
        category_list = sorted([cat[0] for cat in categories if cat[0]])
        
        return jsonify({
            'success': True,
            'categories': category_list,
            'count': len(category_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Busca um produto por ID."""
    try:
        product = Product.get_by_id(product_id)
        
        if not product:
            return jsonify({
                'error': True,
                'message': 'Produto não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'product': product_to_dict(product)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar produto {product_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:product_id>', methods=['PUT'])
@require_admin
def update_product(product_id):
    """Atualiza um produto."""
    try:
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({
                'error': True,
                'message': 'Produto não encontrado'
            }), 404
        
        # Validar dados de entrada
        data = product_update_schema.load(request.get_json())
        
        # Verificar SKU único (se fornecido)
        if 'sku' in data and data['sku']:
            existing_product = Product.get_by_sku(data['sku'])
            if existing_product and existing_product.id != product_id:
                return jsonify({
                    'error': True,
                    'message': 'SKU já existe'
                }), 400
        
        # Atualizar campos
        for field, value in data.items():
            setattr(product, field, value)
        
        product.save()
        
        current_username = get_jwt_identity()
        logger.info(f"Produto atualizado: {product.name} por {current_username}")
        
        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'product': product_to_dict(product)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {product_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:product_id>', methods=['DELETE'])
@require_admin
def delete_product(product_id):
    """Deleta um produto."""
    try:
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({
                'error': True,
                'message': 'Produto não encontrado'
            }), 404
        
        product_name = product.name
        product.delete()
        
        current_username = get_jwt_identity()
        logger.info(f"Produto deletado: {product_name} por {current_username}")
        
        return jsonify({
            'success': True,
            'message': 'Produto deletado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao deletar produto {product_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:product_id>/stock', methods=['PATCH'])
@require_admin
def update_stock(product_id):
    """Atualiza o estoque de um produto."""
    try:
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({
                'error': True,
                'message': 'Produto não encontrado'
            }), 404
        
        # Validar dados de entrada
        data = stock_update_schema.load(request.get_json())
        
        # Calcular novo estoque
        new_stock = product.stock_quantity + data['quantity']
        
        if new_stock < 0:
            return jsonify({
                'error': True,
                'message': 'Estoque não pode ser negativo'
            }), 400
        
        # Atualizar estoque
        old_stock = product.stock_quantity
        product.stock_quantity = new_stock
        product.save()
        
        current_username = get_jwt_identity()
        logger.info(
            f"Estoque atualizado: {product.name} - "
            f"{old_stock} → {new_stock} ({data['quantity']:+d}) "
            f"por {current_username}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Estoque atualizado com sucesso',
            'product': product_to_dict(product),
            'stock_change': {
                'previous': old_stock,
                'current': new_stock,
                'change': data['quantity'],
                'reason': data.get('reason')
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar estoque do produto {product_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/search/<query>', methods=['GET'])
def search_products(query):
    """Busca produtos por texto."""
    try:
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        products = Product.search_products(query)[:limit]
        
        logger.info(f"Busca de produtos realizada: '{query}' - {len(products)} resultados")
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [product_to_dict(product) for product in products],
            'count': len(products)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de produtos: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/category/<category>', methods=['GET'])
def get_products_by_category(category):
    """Lista produtos por categoria."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = Product.query.filter(
            Product.category == category,
            Product.is_active == True
        )
        
        pagination = paginate_query(query, page, per_page)
        
        logger.info(f"Produtos da categoria '{category}' solicitados - {pagination['total']} encontrados")
        
        return jsonify({
            'success': True,
            'category': category,
            'products': [product_to_dict(product) for product in pagination['items']],
            'pagination': {
                'total': pagination['total'],
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'pages': pagination['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos da categoria {category}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/low-stock', methods=['GET'])
@require_admin
def get_low_stock_products():
    """Lista produtos com estoque baixo."""
    try:
        threshold = request.args.get('threshold', 5, type=int)
        
        products = Product.query.filter(
            Product.stock_quantity <= threshold,
            Product.is_active == True
        ).all()
        
        current_username = get_jwt_identity()
        logger.info(f"Produtos com estoque baixo solicitados por {current_username}")
        
        return jsonify({
            'success': True,
            'threshold': threshold,
            'products': [product_to_dict(product) for product in products],
            'count': len(products)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos com estoque baixo: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handler para erros de validação."""
    return jsonify({
        'error': True,
        'message': 'Dados inválidos',
        'details': error.messages
    }), 400


@bp.errorhandler(404)
def handle_not_found(error):
    """Handler para recursos não encontrados."""
    return jsonify({
        'error': True,
        'message': 'Produto não encontrado'
    }), 404


@bp.errorhandler(500)
def handle_internal_error(error):
    """Handler para erros internos."""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        'error': True,
        'message': 'Erro interno do servidor'
    }), 500
