"""
Endpoints da API REST para usuários - Flask.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from marshmallow import Schema, fields, ValidationError, validate
from sqlalchemy.exc import IntegrityError

from ...core.database import db
from ...core.security import require_auth, require_admin, security_manager
from ...models.user import User
from ...core.logging import get_logger

logger = get_logger("users_api")
bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


# ============================================================================
# SCHEMAS DE VALIDAÇÃO
# ============================================================================

class UserCreateSchema(Schema):
    """Schema para criação de usuário."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6))


class UserUpdateSchema(Schema):
    """Schema para atualização de usuário."""
    full_name = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email()
    is_active = fields.Bool()


class UserLoginSchema(Schema):
    """Schema para login de usuário."""
    username = fields.Str(required=True)
    password = fields.Str(required=True)


# Instâncias dos schemas
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
user_login_schema = UserLoginSchema()


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def user_to_dict(user):
    """Converte usuário para dicionário (sem senha)."""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
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
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

@bp.route('/register', methods=['POST'])
def register_user():
    """Registra um novo usuário."""
    try:
        # Validar dados de entrada
        data = user_create_schema.load(request.get_json())
        
        # Verificar se username já existe
        if User.get_by_username(data['username']):
            return jsonify({
                'error': True,
                'message': 'Nome de usuário já existe'
            }), 400
        
        # Verificar se email já existe
        if User.get_by_email(data['email']):
            return jsonify({
                'error': True,
                'message': 'Email já está em uso'
            }), 400
        
        # Criar novo usuário
        user = User.create_user(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            password=data['password']
        )
        
        logger.info(f"Novo usuário registrado: {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'user': user_to_dict(user)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/login', methods=['POST'])
def login_user():
    """Autentica um usuário e retorna token JWT."""
    try:
        # Validar dados de entrada
        data = user_login_schema.load(request.get_json())
        
        # Buscar usuário por username ou email
        user = User.get_by_username(data['username']) or User.get_by_email(data['username'])
        
        if not user:
            return jsonify({
                'error': True,
                'message': 'Credenciais inválidas'
            }), 401
        
        # Verificar senha
        if not user.check_password(data['password']):
            return jsonify({
                'error': True,
                'message': 'Credenciais inválidas'
            }), 401
        
        # Verificar se usuário está ativo
        if not user.is_active:
            return jsonify({
                'error': True,
                'message': 'Conta desativada'
            }), 401
        
        # Criar token
        access_token = create_access_token(identity=user.username)
        
        logger.info(f"Login realizado: {user.username}")
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_in': 1800,  # 30 minutos
            'user': user_to_dict(user)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


# ============================================================================
# ENDPOINTS DE USUÁRIOS
# ============================================================================

@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_profile():
    """Retorna o perfil do usuário atual."""
    try:
        current_username = get_jwt_identity()
        user = User.get_by_username(current_username)
        
        if not user:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user_to_dict(user)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar perfil do usuário: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/me', methods=['PUT'])
@require_auth
def update_current_user_profile():
    """Atualiza o perfil do usuário atual."""
    try:
        current_username = get_jwt_identity()
        user = User.get_by_username(current_username)
        
        if not user:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado'
            }), 404
        
        # Validar dados de entrada
        data = user_update_schema.load(request.get_json())
        
        # Verificar se email já existe (se fornecido)
        if 'email' in data:
            existing_user = User.get_by_email(data['email'])
            if existing_user and existing_user.id != user.id:
                return jsonify({
                    'error': True,
                    'message': 'Email já está em uso'
                }), 400
        
        # Atualizar campos
        for field, value in data.items():
            setattr(user, field, value)
        
        user.save()
        
        logger.info(f"Perfil atualizado: {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Perfil atualizado com sucesso',
            'user': user_to_dict(user)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': True,
            'message': 'Dados inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/', methods=['GET'])
@require_admin
def list_users():
    """Lista usuários (apenas para admins)."""
    try:
        # Parâmetros de query
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        
        # Construir query
        query = User.query
        
        # Aplicar filtro de busca
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.contains(search),
                    User.email.contains(search),
                    User.username.contains(search)
                )
            )
        
        # Aplicar paginação
        pagination = paginate_query(query, page, per_page)
        
        current_username = get_jwt_identity()
        logger.info(f"Lista de usuários solicitada por admin: {current_username}")
        
        return jsonify({
            'success': True,
            'users': [user_to_dict(user) for user in pagination['items']],
            'pagination': {
                'total': pagination['total'],
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'pages': pagination['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user_by_id(user_id):
    """Busca um usuário por ID."""
    try:
        current_username = get_jwt_identity()
        current_user = User.get_by_username(current_username)
        
        # Verificar se é o próprio usuário ou admin
        if current_user.id != user_id and not current_user.is_superuser:
            return jsonify({
                'error': True,
                'message': 'Acesso negado'
            }), 403
        
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user_to_dict(user)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Deleta um usuário (apenas admins)."""
    try:
        current_username = get_jwt_identity()
        current_user = User.get_by_username(current_username)
        
        # Não permitir deletar a si mesmo
        if current_user.id == user_id:
            return jsonify({
                'error': True,
                'message': 'Não é possível deletar sua própria conta'
            }), 400
        
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado'
            }), 404
        
        username = user.username
        user.delete()
        
        logger.info(f"Usuário deletado: {username} por {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Usuário deletado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao deletar usuário {user_id}: {e}")
        return jsonify({
            'error': True,
            'message': 'Erro interno do servidor'
        }), 500


@bp.route('/search/<query>', methods=['GET'])
@require_admin
def search_users(query):
    """Busca usuários por texto (apenas admins)."""
    try:
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        users = User.query.filter(
            db.or_(
                User.full_name.contains(query),
                User.email.contains(query),
                User.username.contains(query)
            )
        ).limit(limit).all()
        
        current_username = get_jwt_identity()
        logger.info(f"Busca de usuários realizada: '{query}' por {current_username}")
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [user_to_dict(user) for user in users],
            'count': len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de usuários: {e}")
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
        'message': 'Recurso não encontrado'
    }), 404


@bp.errorhandler(500)
def handle_internal_error(error):
    """Handler para erros internos."""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        'error': True,
        'message': 'Erro interno do servidor'
    }), 500
