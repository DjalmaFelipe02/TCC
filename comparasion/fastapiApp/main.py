"""
Aplicação principal FastAPI - TCC APIs REST.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import db_manager
from app.api.v1.users import router as users_router
from app.api.v1.products import router as products_router

# Configurar logging
setup_logging()
logger = get_logger("main")

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host (segurança)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)


# Middleware de logging personalizado
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para logging de requisições."""
    start_time = time.time()
    
    # Log da requisição
    logger.info(f"REQUEST: {request.method} {request.url.path} - IP: {request.client.host}")
    
    try:
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = time.time() - start_time
        
        # Log da resposta
        logger.info(
            f"RESPONSE: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # Adicionar header com tempo de processamento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"ERROR: {request.method} {request.url.path} - {str(e)} - Time: {process_time:.3f}s")
        raise


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para exceções HTTP."""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais."""
    logger.error(f"Unhandled Exception: {type(exc).__name__} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Erro interno do servidor",
            "path": request.url.path
        }
    )


# ============================================================================
# EVENTOS DE INICIALIZAÇÃO
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Eventos executados na inicialização da aplicação."""
    logger.info("Iniciando aplicação FastAPI...")
    
    # Criar tabelas do banco de dados
    try:
        db_manager.create_tables()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    logger.info(f"Aplicação {settings.PROJECT_NAME} v{settings.VERSION} iniciada com sucesso!")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos executados no encerramento da aplicação."""
    logger.info("Encerrando aplicação FastAPI...")


# ============================================================================
# ROTAS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da aplicação."""
    return {
        "message": f"Bem-vindo ao {settings.PROJECT_NAME}!",
        "version": settings.VERSION,
        "description": settings.PROJECT_DESCRIPTION,
        "docs": "/docs",
        "redoc": "/redoc",
        "api": {
            "users": "/api/v1/users",
            "products": "/api/v1/products",
            "health": "/health"
        },
        "features": [
            "Autenticação JWT",
            "CRUD completo de usuários",
            "CRUD completo de produtos",
            "Paginação e filtros",
            "Logging estruturado",
            "Validação de dados",
            "Tratamento de erros",
            "Documentação automática"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificação de saúde."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.time(),
        "database": "connected"
    }


# Incluir routers da API
app.include_router(users_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Iniciando servidor FastAPI em {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
