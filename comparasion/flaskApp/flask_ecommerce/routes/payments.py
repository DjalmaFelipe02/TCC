
# from flask import Blueprint, request, jsonify, abort
# from flask_ecommerce.db import db
# from flask_ecommerce.models import PaymentMethod, Payment, User, Order
# from decimal import Decimal
# from datetime import datetime

# payments_bp = Blueprint("payments", __name__)

# # PaymentMethod CRUD
# @payments_bp.route("/methods", methods=["GET"])
# def list_payment_methods():
#     methods = PaymentMethod.query.all()
#     return jsonify([m.to_dict() for m in methods])

# @payments_bp.route("/methods/<string:method_id>", methods=["GET"])
# def get_payment_method(method_id):
#     method = PaymentMethod.query.get(method_id)
#     if method is None:
#         abort(404, description="Payment method not found")
#     return jsonify(method.to_dict())

# @payments_bp.route("/methods", methods=["POST"])
# def create_payment_method():
#     data = request.get_json() or {}
#     user_id = data.get("user_id")
#     method_type = data.get("type")
#     name = data.get("name")

#     if not user_id or not method_type or not name:
#         abort(400, description="User ID, type, and name are required for payment method")
    
#     user = User.query.get(user_id)
#     if user is None:
#         abort(404, description="User not found")

#     method = PaymentMethod(
#         user_id=user_id,
#         type=method_type,
#         name=name,
#         is_default=data.get("is_default", False),
#         is_active=data.get("is_active", True)
#     )
#     db.session.add(method)
#     db.session.commit()
#     return jsonify(method.to_dict()), 201

# @payments_bp.route("/methods/<string:method_id>", methods=["PUT"])
# def update_payment_method(method_id):
#     method = PaymentMethod.query.get(method_id)
#     if method is None:
#         abort(404, description="Payment method not found")

#     data = request.get_json() or {}
#     method.type = data.get("type", method.type)
#     method.name = data.get("name", method.name)
#     method.is_default = data.get("is_default", method.is_default)
#     method.is_active = data.get("is_active", method.is_active)
#     db.session.commit()
#     return jsonify(method.to_dict())

# @payments_bp.route("/methods/<string:method_id>", methods=["DELETE"])
# def delete_payment_method(method_id):
#     method = PaymentMethod.query.get(method_id)
#     if method is None:
#         abort(404, description="Payment method not found")
#     db.session.delete(method)
#     db.session.commit()
#     return jsonify({"message": "Payment method deleted"}), 204

# # Payment CRUD
# @payments_bp.route("/", methods=["GET"])
# def list_payments():
#     payments = Payment.query.all()
#     return jsonify([p.to_dict() for p in payments])

# @payments_bp.route("/<string:payment_id>", methods=["GET"])
# def get_payment(payment_id):
#     payment = Payment.query.get(payment_id)
#     if payment is None:
#         abort(404, description="Payment not found")
#     return jsonify(payment.to_dict())

# @payments_bp.route("/", methods=["POST"])
# def create_payment():
#     data = request.get_json() or {}
#     order_id = data.get("order_id")
#     amount = data.get("amount")
#     payment_method_id = data.get("payment_method_id")

#     if not order_id or not amount:
#         abort(400, description="Order ID and amount are required for payment")
    
#     order = Order.query.get(order_id)
#     if order is None:
#         abort(404, description="Order not found")

#     if payment_method_id:
#         payment_method = PaymentMethod.query.get(payment_method_id)
#         if payment_method is None:
#             abort(404, description="Payment method not found")

#     payment = Payment(
#         order_id=order_id,
#         payment_method_id=payment_method_id,
#         amount=Decimal(str(amount)),
#         currency=data.get("currency", "BRL"),
#         status=data.get("status", "pending"),
#         payment_date=datetime.fromisoformat(data["payment_date"]) if data.get("payment_date") else None
#     )
#     db.session.add(payment)
#     db.session.commit()
#     return jsonify(payment.to_dict()), 201

# @payments_bp.route("/<string:payment_id>", methods=["PUT"])
# def update_payment(payment_id):
#     payment = Payment.query.get(payment_id)
#     if payment is None:
#         abort(404, description="Payment not found")

#     data = request.get_json() or {}
#     payment.amount = Decimal(str(data.get("amount", payment.amount))) if data.get("amount") else payment.amount
#     payment.currency = data.get("currency", payment.currency)
#     payment.status = data.get("status", payment.status)
#     payment.payment_date = datetime.fromisoformat(data["payment_date"]) if data.get("payment_date") else payment.payment_date
#     payment.payment_method_id = data.get("payment_method_id", payment.payment_method_id)
#     db.session.commit()
#     return jsonify(payment.to_dict())

# @payments_bp.route("/<string:payment_id>", methods=["DELETE"])
# def delete_payment(payment_id):
#     payment = Payment.query.get(payment_id)
#     if payment is None:
#         abort(404, description="Payment not found")
#     db.session.delete(payment)
#     db.session.commit()
#     return jsonify({"message": "Payment deleted"}), 204
from flask import Blueprint, request, jsonify, abort
from ..db import db
from ..models.payment import PaymentMethod, Payment
from ..models.order import Order
from ..models.user import User
import logging
from sqlalchemy.exc import IntegrityError

payments_bp = Blueprint("payments", __name__)

def _pm_to_dict(pm: PaymentMethod):
    return {"id": pm.id, "user_id": pm.user_id, "name": pm.name, "type": pm.type, "is_default": pm.is_default, "is_active": pm.is_active, "created_at": getattr(pm, "created_at", None)}

def _payment_to_dict(p: Payment):
    return {"id": p.id, "order": p.order_id, "payment_method": p.payment_method_id, "amount": float(p.amount), "currency": p.currency, "status": p.status, "payment_date": getattr(p, "payment_date", None)}

@payments_bp.route("/methods", methods=["GET"])
def list_methods():
    methods = PaymentMethod.query.all()
    return jsonify([_pm_to_dict(m) for m in methods]), 200

@payments_bp.route("/methods", methods=["POST"])
def create_method():
    data = request.get_json() or {}
    # require user_id (model has NOT NULL constraint)
    user_id = data.get("user_id") or data.get("user")
    if not user_id:
        return jsonify({"detail": "user_id required"}), 400
    # validate user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"detail": "user not found"}), 400

    if not data.get("name"):
        return jsonify({"detail": "name required"}), 400

    pm = PaymentMethod(
        user_id=user.id,
        type=data.get("type", ""),
        name=data["name"],
        is_default=data.get("is_default", False),
        is_active=data.get("is_active", True),
    )
    try:
        db.session.add(pm)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logging.exception("create_method IntegrityError")
        return jsonify({"detail": "Conflict creating payment method", "error": str(e.orig) if hasattr(e, "orig") else str(e)}), 409
    except Exception as e:
        db.session.rollback()
        logging.exception("create_method unexpected error")
        return jsonify({"detail": "internal error", "error": str(e)}), 500
    return jsonify(_pm_to_dict(pm)), 201

@payments_bp.route("/", methods=["GET"])
def list_payments():
    pays = Payment.query.all()
    return jsonify([_payment_to_dict(p) for p in pays]), 200

@payments_bp.route("/", methods=["POST"])
def create_payment():
    data = request.get_json() or {}
    order_id = data.get("order") or data.get("order_id")
    if not order_id or "amount" not in data:
        return jsonify({"detail": "order and amount required"}), 400
    try:
        Order.query.get_or_404(order_id)
        pay = Payment(order_id=order_id, payment_method_id=data.get("payment_method") or data.get("method_id") or data.get("payment_method_id"), amount=data.get("amount", 0), currency=data.get("currency", "BRL"), status=data.get("status", "completed"))
        db.session.add(pay)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logging.exception("create_payment IntegrityError")
        return jsonify({"detail": "Conflict creating payment", "error": str(e.orig) if hasattr(e, "orig") else str(e)}), 409
    except Exception as e:
        db.session.rollback()
        logging.exception("create_payment unexpected error")
        return jsonify({"detail": "internal error", "error": str(e)}), 500
    return jsonify(_payment_to_dict(pay)), 201

@payments_bp.route("/<payment_id>/", methods=["GET", "PATCH", "DELETE"])
@payments_bp.route("/<payment_id>", methods=["GET", "PATCH", "DELETE"])
def payment_detail(payment_id):
    p = Payment.query.get_or_404(payment_id)
    if request.method == "GET":
        return jsonify(_payment_to_dict(p)), 200
    if request.method in ("PATCH", "PUT"):
        data = request.get_json() or {}
        if "status" in data:
            p.status = data["status"]
        db.session.commit()
        return jsonify(_payment_to_dict(p)), 200
    db.session.delete(p)
    db.session.commit()
    return ("", 204)