
# from flask import Blueprint, request, jsonify, abort
# from flask_ecommerce.db import db
# from flask_ecommerce.models import Category, Product

# products_bp = Blueprint("products", __name__)

# # Category CRUD
# @products_bp.route("/categories", methods=["GET"])
# def list_categories():
#     categories = Category.query.all()
#     return jsonify([c.to_dict() for c in categories])

# @products_bp.route("/categories/<string:category_id>", methods=["GET"])
# def get_category(category_id):
#     category = Category.query.get(category_id)
#     if category is None:
#         abort(404, description="Category not found")
#     return jsonify(category.to_dict())

# @products_bp.route("/categories", methods=["POST"])
# def create_category():
#     data = request.get_json() or {}
#     if not data.get("name"):
#         abort(400, description="Category name is required")
    
#     category = Category(
#         name=data["name"],
#         description=data.get("description")
#     )
#     db.session.add(category)
#     db.session.commit()
#     return jsonify(category.to_dict()), 201

# @products_bp.route("/categories/<string:category_id>", methods=["PUT"])
# def update_category(category_id):
#     category = Category.query.get(category_id)
#     if category is None:
#         abort(404, description="Category not found")

#     data = request.get_json() or {}
#     category.name = data.get("name", category.name)
#     category.description = data.get("description", category.description)
#     db.session.commit()
#     return jsonify(category.to_dict())

# @products_bp.route("/categories/<string:category_id>", methods=["DELETE"])
# def delete_category(category_id):
#     category = Category.query.get(category_id)
#     if category is None:
#         abort(404, description="Category not found")
#     db.session.delete(category)
#     db.session.commit()
#     return jsonify({"message": "Category deleted"}), 204

# # Product CRUD
# @products_bp.route("/", methods=["GET"])
# def list_products():
#     products = Product.query.all()
#     return jsonify([p.to_dict() for p in products])

# @products_bp.route("/<string:product_id>", methods=["GET"])
# def get_product(product_id):
#     product = Product.query.get(product_id)
#     if product is None:
#         abort(404, description="Product not found")
#     return jsonify(product.to_dict())

# @products_bp.route("/", methods=["POST"])
# def create_product():
#     data = request.get_json() or {}
#     if not data.get("name") or not data.get("price"):
#         abort(400, description="Product name and price are required")
    
#     product = Product(
#         name=data["name"],
#         description=data.get("description"),
#         price=data["price"],
#         stock=data.get("stock", 0),
#         category_id=data.get("category_id")
#     )
#     db.session.add(product)
#     db.session.commit()
#     return jsonify(product.to_dict()), 201

# @products_bp.route("/<string:product_id>", methods=["PUT"])
# def update_product(product_id):
#     product = Product.query.get(product_id)
#     if product is None:
#         abort(404, description="Product not found")

#     data = request.get_json() or {}
#     product.name = data.get("name", product.name)
#     product.description = data.get("description", product.description)
#     product.price = data.get("price", product.price)
#     product.stock = data.get("stock", product.stock)
#     product.category_id = data.get("category_id", product.category_id)
#     db.session.commit()
#     return jsonify(product.to_dict())

# @products_bp.route("/<string:product_id>", methods=["DELETE"])
# def delete_product(product_id):
#     product = Product.query.get(product_id)
#     if product is None:
#         abort(404, description="Product not found")
#     db.session.delete(product)
#     db.session.commit()
#     return jsonify({"message": "Product deleted"}), 204
from flask import Blueprint, request, jsonify, abort
from ..db import db
from ..models.product import Product, Category

products_bp = Blueprint("products", __name__)

def _cat_to_dict(c: Category):
    return {"id": c.id, "name": c.name, "description": c.description}

def _prod_to_dict(p: Product):
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price) if p.price is not None else None,
        "stock": p.stock,
        "category": _cat_to_dict(p.category) if p.category else None,
        "created_at": getattr(p, "created_at", None),
    }

@products_bp.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.all()
    return jsonify([_cat_to_dict(c) for c in cats]), 200

@products_bp.route("/categories", methods=["POST"])
def create_category():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"detail": "name required"}), 400
    c = Category(name=data["name"], description=data.get("description"))
    db.session.add(c)
    db.session.commit()
    return jsonify(_cat_to_dict(c)), 201

@products_bp.route("/", methods=["GET"])
def list_products():
    prods = Product.query.all()
    return jsonify([_prod_to_dict(p) for p in prods]), 200

@products_bp.route("/", methods=["POST"])
def create_product():
    data = request.get_json() or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"detail": "name and price required"}), 400
    cat = None
    if data.get("category_id"):
        cat = Category.query.get(data["category_id"])
        if not cat:
            return jsonify({"detail": "category not found"}), 400
    p = Product(name=data["name"], description=data.get("description"), price=data["price"], stock=data.get("stock", 0))
    if cat:
        p.category = cat
    db.session.add(p)
    db.session.commit()
    return jsonify(_prod_to_dict(p)), 201

@products_bp.route("/<product_id>/", methods=["GET"])
@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify(_prod_to_dict(p)), 200

@products_bp.route("/<product_id>/", methods=["PATCH", "PUT"])
@products_bp.route("/<product_id>", methods=["PATCH", "PUT"])
def update_product(product_id):
    p = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    for k in ("name", "description", "price", "stock"):
        if k in data:
            setattr(p, k, data[k])
    if "category_id" in data:
        p.category = Category.query.get(data["category_id"]) if data["category_id"] else None
    db.session.commit()
    return jsonify(_prod_to_dict(p)), 200

@products_bp.route("/<product_id>/", methods=["DELETE"])
@products_bp.route("/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return ("", 204)