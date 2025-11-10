from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .db import db  
from urllib.parse import quote_plus
import os


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        db_user = os.getenv('DB_USER', 'root')
        db_password = quote_plus(os.getenv('DB_PASSWORD', '*******'))
        db_host = os.getenv('DB_HOST', 'localhost')
        db_name = os.getenv('DB_NAME', 'ecommerce_flask')
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate = Migrate(app, db)
    CORS(app)

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
        from . import models  
        db.create_all()

    return app

if __name__ == "__main__":
    create_app().run(debug=True)


