from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .db import db  # usar a instância do db definida em db.py
import os

def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # DB: usa caminho relativo ao projeto flaskApp
    db_path = os.path.join(os.path.dirname(__file__), "..", "ecommerce.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath(db_path)}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate = Migrate(app, db)
    CORS(app)  # Enable CORS for all routes

    # registrando blueprints (certifique-se que os módulos existem)
    from .routes.users import users_bp
    from .routes.products import products_bp
    from .routes.orders import orders_bp
    from .routes.payments import payments_bp

    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")

    # criar tabelas se necessário
    with app.app_context():
        from . import models  # importa models para registrar metadata
        db.create_all()

    return app

if __name__ == "__main__":
    create_app().run(debug=True)


