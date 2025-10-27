# """
# Rotas para gerenciamento de pedidos e itens de pedido na API Flask.
# """
# from flask import Blueprint, request, jsonify, abort
# from flask_ecommerce.db import db
# from flask_ecommerce.models import Order, OrderItem, User, Product
# from decimal import Decimal

# orders_bp = Blueprint("orders", __name__)

# @orders_bp.route("/", methods=["GET"])
# def list_orders():
#     orders = Order.query.all()
#     return jsonify([order.to_dict() for order in orders])

# @orders_bp.route("/<string:order_id>", methods=["GET"])
# def get_order(order_id):
#     order = Order.query.get(order_id)
#     if order is None:
#         abort(404, description="Order not found")
#     return jsonify(order.to_dict())

# @orders_bp.route("/", methods=["POST"])
# def create_order():
#     data = request.get_json() or {}
#     user_id = data.get("user_id")
#     address = data.get("address")
#     items_data = data.get("items")

#     if not user_id or not address or not items_data:
#         abort(400, description="User ID, address, and items are required")
    
#     user = User.query.get(user_id)
#     if user is None:
#         abort(404, description="User not found")

#     order = Order(
#         user_id=user_id,
#         address=address
#     )
#     db.session.add(order)
#     db.session.flush() # To get order.id before commit

#     total_amount = Decimal("0.00")
#     for item_data in items_data:
#         product_id = item_data.get("product_id")
#         quantity = item_data.get("quantity")

#         if not product_id or not quantity or not isinstance(quantity, int) or quantity <= 0:
#             db.session.rollback()
#             abort(400, description="Invalid product ID or quantity for order item")
        
#         product = Product.query.get(product_id)
#         if product is None:
#             db.session.rollback()
#             abort(404, description=f"Product with ID {product_id} not found")
        
#         order_item = OrderItem(
#             order_id=order.id,
#             product_id=product_id,
#             quantity=quantity
#         )
#         db.session.add(order_item)
#         total_amount += product.price * quantity
    
#     order.total_amount = total_amount
#     db.session.commit()
#     return jsonify(order.to_dict()), 201

# @orders_bp.route("/<string:order_id>", methods=["PUT"])
# def update_order(order_id):
#     order = Order.query.get(order_id)
#     if order is None:
#         abort(404, description="Order not found")

#     data = request.get_json() or {}
#     order.address = data.get("address", order.address)
    
#     # Update items if provided
#     if "items" in data:
#         # Clear existing items
#         for item in order.items:
#             db.session.delete(item)
#         db.session.flush()

#         total_amount = Decimal("0.00")
#         for item_data in data["items"]:
#             product_id = item_data.get("product_id")
#             quantity = item_data.get("quantity")

#             if not product_id or not quantity or not isinstance(quantity, int) or quantity <= 0:
#                 db.session.rollback()
#                 abort(400, description="Invalid product ID or quantity for order item")
            
#             product = Product.query.get(product_id)
#             if product is None:
#                 db.session.rollback()
#                 abort(404, description=f"Product with ID {product_id} not found")
            
#             order_item = OrderItem(
#                 order_id=order.id,
#                 product_id=product_id,
#                 quantity=quantity
#             )
#             db.session.add(order_item)
#             total_amount += product.price * quantity
#         order.total_amount = total_amount

#     db.session.commit()
#     return jsonify(order.to_dict())

# @orders_bp.route("/<string:order_id>", methods=["DELETE"])
# def delete_order(order_id):
#     order = Order.query.get(order_id)
#     if order is None:
#         abort(404, description="Order not found")
#     db.session.delete(order)
#     db.session.commit()
#     return jsonify({"message": "Order deleted"}), 204
from flask import Blueprint, request, jsonify, abort
from ..db import db
from ..models.order import Order, OrderItem
from ..models.product import Product
from ..models.user import User

orders_bp = Blueprint("orders", __name__)

def _order_to_dict(o: Order):
    return {"id": o.id, "user": o.user_id, "address": o.address, "total_amount": float(o.total_amount or 0), "created_at": getattr(o, "created_at", None)}

def _order_item_to_dict(it: OrderItem):
    return {"id": it.id, "order": it.order_id, "product": it.product_id, "quantity": it.quantity}

@orders_bp.route("/", methods=["GET"])
def list_orders():
    orders = Order.query.all()
    return jsonify([_order_to_dict(o) for o in orders]), 200

@orders_bp.route("/", methods=["POST"])
def create_order():
    data = request.get_json() or {}
    user_id = data.get("user") or data.get("user_id")
    items = data.get("items") or []
    if not user_id or not items:
        return jsonify({"detail": "user and items required"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"detail": "user not found"}), 400
    order = Order(user_id=user.id, address=data.get("address", ""), total_amount=0)
    db.session.add(order)
    db.session.flush()
    total = 0
    for it in items:
        pid = it.get("product") or it.get("product_id")
        qty = int(it.get("quantity", 1))
        prod = Product.query.get(pid)
        if not prod:
            db.session.rollback()
            return jsonify({"detail": f"product {pid} not found"}), 400
        oi = OrderItem(order_id=order.id, product_id=prod.id, quantity=qty)
        db.session.add(oi)
        total += float(prod.price) * qty
    order.total_amount = round(total, 2)
    db.session.commit()
    return jsonify(_order_to_dict(order)), 201

@orders_bp.route("/<order_id>/", methods=["GET"])
@orders_bp.route("/<order_id>", methods=["GET"])
def get_order(order_id):
    o = Order.query.get_or_404(order_id)
    return jsonify(_order_to_dict(o)), 200

@orders_bp.route("/<order_id>/", methods=["PATCH", "PUT"])
@orders_bp.route("/<order_id>", methods=["PATCH", "PUT"])
def update_order(order_id):
    o = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    if "address" in data:
        o.address = data["address"]
    db.session.commit()
    return jsonify(_order_to_dict(o)), 200

@orders_bp.route("/<order_id>/", methods=["DELETE"])
@orders_bp.route("/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    o = Order.query.get_or_404(order_id)
    db.session.delete(o)
    db.session.commit()
    return ("", 204)

# nested items endpoints
@orders_bp.route("/<order_id>/items/", methods=["GET"])
def list_order_items(order_id):
    Order.query.get_or_404(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return jsonify([_order_item_to_dict(i) for i in items]), 200

@orders_bp.route("/<order_id>/items/", methods=["POST"])
def create_order_item(order_id):
    Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    pid = data.get("product") or data.get("product_id")
    qty = int(data.get("quantity", 1))
    prod = Product.query.get(pid)
    if not prod:
        return jsonify({"detail": "product not found"}), 400
    oi = OrderItem(order_id=order_id, product_id=prod.id, quantity=qty)
    db.session.add(oi)
    db.session.commit()
    return jsonify(_order_item_to_dict(oi)), 201

# top-level items endpoints
@orders_bp.route("/items/", methods=["GET"])
def list_all_order_items():
    items = OrderItem.query.all()
    return jsonify([_order_item_to_dict(i) for i in items]), 200

@orders_bp.route("/items/<item_id>/", methods=["GET", "PATCH", "DELETE"])
@orders_bp.route("/items/<item_id>", methods=["GET", "PATCH", "DELETE"])
def order_item_detail(item_id):
    it = OrderItem.query.get_or_404(item_id)
    if request.method == "GET":
        return jsonify(_order_item_to_dict(it)), 200
    if request.method in ("PATCH", "PUT"):
        data = request.get_json() or {}
        if "quantity" in data:
            it.quantity = int(data["quantity"])
            db.session.commit()
            return jsonify(_order_item_to_dict(it)), 200
        return jsonify(_order_item_to_dict(it)), 200
    db.session.delete(it)
    db.session.commit()
    return ("", 204)