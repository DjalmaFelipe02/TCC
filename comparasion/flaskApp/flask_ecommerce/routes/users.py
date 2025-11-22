from flask import Blueprint, request, jsonify, abort
from ..db import db
from ..models.user import User
import logging
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

users_bp = Blueprint("users", __name__)

def _user_to_dict(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "birth_date": u.birth_date,
        "address": u.address,
        "created_at": getattr(u, "created_at", None),
    }

@users_bp.route("/", methods=["GET"])
def list_users():
    users = User.query.all()
    return jsonify([_user_to_dict(u) for u in users]), 200

@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("email"):
        return jsonify({"detail": "name and email required"}), 400

    # parse birth_date string -> date object (optional)
    birth_date_val = data.get("birth_date")
    birth_date_obj = None
    if birth_date_val:
        try:
            # aceita YYYY-MM-DD
            birth_date_obj = datetime.strptime(birth_date_val, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"detail": "birth_date must be in YYYY-MM-DD format"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"detail": "email already exists"}), 409

    u = User(
        name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        birth_date=birth_date_obj,
        address=data.get("address"),
    )
    try:
        db.session.add(u)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logging.exception("create_user IntegrityError")
        return jsonify({"detail": "Conflict creating user", "error": str(e.orig) if hasattr(e, "orig") else str(e)}), 409
    except Exception as e:
        db.session.rollback()
        logging.exception("create_user unexpected error")
        return jsonify({"detail": "internal error", "error": str(e)}), 500

    return jsonify(_user_to_dict(u)), 201

@users_bp.route("/<user_id>/", methods=["GET"])
@users_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    u = User.query.get_or_404(user_id)
    return jsonify(_user_to_dict(u)), 200

@users_bp.route("/<user_id>/", methods=["PATCH", "PUT"])
@users_bp.route("/<user_id>", methods=["PATCH", "PUT"])
def update_user(user_id):
    u = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    for k in ("name", "email", "phone", "birth_date", "address"):
        if k in data:
            setattr(u, k, data[k])
    db.session.commit()
    return jsonify(_user_to_dict(u)), 200

@users_bp.route("/<user_id>/", methods=["DELETE"])
@users_bp.route("/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return ("", 204)