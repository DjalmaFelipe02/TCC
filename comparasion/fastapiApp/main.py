from fastapi import FastAPI, HTTPException, Response, Path, Depends, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Literal, Dict, Any

# Importações dos padrões de projeto
from .strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy, PaymentStrategy
from .facade.checkout_services import CheckoutFacade
from .abstract_factory.factory import SerializerFactory
from .abstract_factory.serializers import Serializer # Importar a interface base

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="API Comparativa FastAPI vs Flask",
    description="Demonstração da aplicação dos padrões Abstract Factory, Facade e Strategy usando FastAPI.",
    version="1.0.0"
)

# --- Modelos Pydantic para Validação de Requisição/Resposta ---
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"

class CheckoutRequest(BaseModel):
    product_id: int
    zip_code: str
    subtotal: float

DEFAULT_SERIALIZATION_DATA = {"name": "FastAPI User", "id": 123, "active": True}
# --- Implementação do Padrão Strategy (Pagamento) ---

# Injeção de Dependência para obter o PaymentProcessor com a Strategy correta
def get_payment_processor(method: Literal["creditcard", "paypal"] = Path(...)) -> PaymentProcessor:
    """Dependência FastAPI para injetar o PaymentProcessor com a estratégia correta."""
    if method == "creditcard":
        strategy = CreditCardStrategy()
    elif method == "paypal":
        strategy = PayPalStrategy()
    # FastAPI lida com o erro se 'method' não for 'creditcard' ou 'paypal' devido ao Literal
    # mas podemos adicionar uma verificação extra se necessário.
    return PaymentProcessor(strategy)

@app.post("/pay/{method}", tags=["Strategy Pattern"], summary="Processa um pagamento usando uma estratégia específica")
async def process_payment_strategy(
    request: PaymentRequest,
    processor: PaymentProcessor = Depends(get_payment_processor)
) -> JSONResponse:
    """Endpoint para demonstrar o padrão Strategy.

    Recebe o método de pagamento na URL (creditcard ou paypal) e os detalhes
    do pagamento no corpo da requisição.
    A dependência `get_payment_processor` injeta a instância correta do
    `PaymentProcessor` com a `PaymentStrategy` selecionada.
    """
    result = processor.execute_payment(request.amount)
    return JSONResponse(content={"payment_details": result, "currency": request.currency})

# --- Implementação do Padrão Facade (Checkout) ---

# Injeção de Dependência para a Facade (embora simples, demonstra o conceito)
def get_checkout_facade() -> CheckoutFacade:
    """Dependência FastAPI para injetar a instância da CheckoutFacade."""
    return CheckoutFacade()

@app.post("/checkout", tags=["Facade Pattern"], summary="Processa um checkout simplificado usando Facade")
async def process_checkout_facade(
    request: CheckoutRequest,
    facade: CheckoutFacade = Depends(get_checkout_facade)
) -> JSONResponse:
    """Endpoint para demonstrar o padrão Facade.

    Recebe os detalhes do pedido no corpo da requisição.
    A dependência `get_checkout_facade` injeta a instância da `CheckoutFacade`,
    que simplifica a interação com os subsistemas de estoque, frete e impostos.
    """
    try:
        result = facade.complete_order(
            product_id=request.product_id,
            zip_code=request.zip_code,
            subtotal=request.subtotal
        )
        return JSONResponse(content=result)
    except ValueError as e:
        # Tratamento de erro (ex: produto fora de estoque)
        raise HTTPException(status_code=400, detail=str(e))

# --- Implementação do Padrão Abstract Factory (Serialização) ---

# Injeção de Dependência para obter o Serializer correto
def get_serializer(format: Literal["json", "xml"] = Path(...)) -> Serializer:
    """Dependência FastAPI para injetar o Serializer correto via Abstract Factory."""
    try:
        return SerializerFactory.create_serializer(format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# CORRIGIDO: Alterado para @app.get e removido o corpo da requisição
@app.get("/serialize/{format}", tags=["Abstract Factory Pattern"], summary="Serializa dados de exemplo usando Abstract Factory (GET)")
async def serialize_data_factory_get(
    format: Literal["json", "xml"],
    serializer: Serializer = Depends(get_serializer)
) -> Response:
    """Endpoint GET para demonstrar o padrão Abstract Factory.

    Recebe o formato desejado na URL (json ou xml).
    Usa dados de exemplo definidos internamente.
    A dependência `get_serializer` usa a `SerializerFactory` para obter
    a instância correta do `Serializer`.
    Retorna os dados serializados com o mimetype apropriado.
    Exemplo: GET /serialize/json ou GET /serialize/xml
    """
    serialized_data = serializer.serialize(DEFAULT_SERIALIZATION_DATA)
    media_type = f"application/{format}"
    # Retorna PlainTextResponse para garantir que a string já formatada seja retornada
    # Se retornássemos um dict para JSON, FastAPI o re-serializaria.
    return PlainTextResponse(content=serialized_data, media_type=media_type)

# --- Rota Principal --- (Opcional)
@app.get("/", tags=["Info"], summary="Endpoint inicial da API")
async def root():
    return {"message": "Bem-vindo à API Comparativa FastAPI! Use os endpoints para testar os padrões."}

# --- Instruções para Execução (se executado diretamente) ---
# Para rodar: uvicorn comparasion.fastapiApp.main:app --reload --port 8001
# (Ajuste o port se necessário para evitar conflito com o Flask)

