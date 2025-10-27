from fastapi import FastAPI
from fastapi_ecommerce.database import engine, Base
from fastapi_ecommerce.routers import users, products, orders, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI E-Commerce")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])

