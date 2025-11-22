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