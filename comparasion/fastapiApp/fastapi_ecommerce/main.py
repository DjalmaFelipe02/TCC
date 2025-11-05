from fastapi import FastAPI
from fastapi_ecommerce.database import engine, Base

# Importações explícitas — garante que todos os routers sejam registrados
from fastapi_ecommerce.routers.users import router as users_router
from fastapi_ecommerce.routers.products import router as products_router
from fastapi_ecommerce.routers.orders import router as orders_router
from fastapi_ecommerce.routers.payments import router as payments_router

# Criação das tabelas no banco (caso não existam)
Base.metadata.create_all(bind=engine)

# Inicialização do app FastAPI
app = FastAPI(
    title="FastAPI E-Commerce",
    description="API REST para e-commerce desenvolvida em FastAPI",
    version="1.0.0",
    redirect_slashes=True,  # evita 404 com/sem barra no final
)

# Registro explícito dos routers
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(payments_router, prefix="/api/payments", tags=["payments"])

# ------------------------------------------------------------
# Verificação automática das rotas registradas (opcional)
# ------------------------------------------------------------
@app.on_event("startup")
async def verify_routes():
    print("\n🚀 Rotas registradas no app:")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"{list(route.methods)} -> {route.path}")
    print("------------------------------------------------------------\n")
