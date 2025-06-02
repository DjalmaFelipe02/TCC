from fastapi import FastAPI, HTTPException, Response, Path, Query, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Literal, Dict, Any

# Importações dos padrões de projeto
from .strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy, PaymentStrategy
from .facade.checkout_services import CheckoutFacade
# Importações da Abstract Factory refatorada
from .abstract_factory.providers import SerializerProvider, get_provider, JsonProvider, XmlProvider # Importar as fábricas concretas
from .abstract_factory.serializers import CompactSerializer, ReadableSerializer # Importar interfaces base dos produtos

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="API Comparativa FastAPI vs Flask (Abstract Factory Refatorado)",
    description="Demonstração da aplicação dos padrões Abstract Factory (canônico), Facade e Strategy usando FastAPI.",
    version="1.1.0" # Versão incrementada
)

# --- Modelos Pydantic para Validação de Requisição/Resposta ---
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"

class CheckoutRequest(BaseModel):
    product_id: int
    zip_code: str
    subtotal: float

# Dados de exemplo para serialização
DEFAULT_SERIALIZATION_DATA = {"user": {"name": "FastAPI User", "id": 123, "active": True, "roles": ["admin", "editor"]}}

# --- Implementação do Padrão Strategy (Pagamento) - Sem alterações ---

def get_payment_processor(method: Literal["creditcard", "paypal"] = Path(...)) -> PaymentProcessor:
    if method == "creditcard":
        strategy = CreditCardStrategy()
    elif method == "paypal":
        strategy = PayPalStrategy()
    return PaymentProcessor(strategy)

@app.post("/pay/{method}", tags=["Strategy Pattern"], summary="Processa um pagamento usando uma estratégia específica (POST)")
async def process_payment_strategy(
    request: PaymentRequest,
    processor: PaymentProcessor = Depends(get_payment_processor)
) -> JSONResponse:
    result = processor.execute_payment(request.amount)
    return JSONResponse(content={"payment_details": result, "currency": request.currency})

# --- Implementação do Padrão Facade (Checkout) - Sem alterações ---

def get_checkout_facade() -> CheckoutFacade:
    return CheckoutFacade()

@app.post("/checkout", tags=["Facade Pattern"], summary="Processa um checkout simplificado usando Facade (POST)")
async def process_checkout_facade(
    request: CheckoutRequest,
    facade: CheckoutFacade = Depends(get_checkout_facade)
) -> JSONResponse: 
    """
    Endpoint para demonstrar o padrão Facade.

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
        raise HTTPException(status_code=400, detail=str(e))

# --- Implementação do Padrão Abstract Factory (Serialização - Refatorado) ---

# Dependência para obter a Fábrica Abstrata correta (Provider)
def get_serializer_provider(format: Literal["json", "xml"] = Path(...)) -> SerializerProvider:
    """Dependência FastAPI para injetar a Fábrica Abstrata (Provider) correta."""
    try:
        return get_provider(format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/serialize/{format}", tags=["Abstract Factory Pattern"], summary="Serializa dados de exemplo usando Abstract Factory (GET)")
async def serialize_data_abstract_factory(
    provider: SerializerProvider = Depends(get_serializer_provider),
    style: Literal["compact", "readable"] = Query("readable", description="Estilo de serialização: compact ou readable")
) -> Response:
    """Endpoint GET para demonstrar o padrão Abstract Factory canônico.

    Recebe o formato (json/xml) na URL e o estilo (compact/readable) como query param.
    Usa a Fábrica Abstrata (`SerializerProvider`) injetada para criar o serializador
    apropriado da família (compacta ou legível) e formato corretos.

    Exemplos:
    - GET /serialize/json?style=readable
    - GET /serialize/xml?style=compact
    """
    try:
        # Usa a fábrica (provider) para criar o serializador da família/estilo correto
        if style == "compact":
            serializer = provider.create_compact_serializer()
        else: # style == "readable"
            serializer = provider.create_readable_serializer()

        # Serializa os dados de exemplo
        serialized_data = serializer.serialize(DEFAULT_SERIALIZATION_DATA)
        # Determina o media type com base no formato da fábrica (implícito no provider)
        format = "json" if isinstance(provider, JsonProvider) else "xml"
        media_type = f"application/{format}"

        # Retorna a resposta como texto plano para preservar a formatação
        return PlainTextResponse(content=serialized_data, media_type=media_type)

    except Exception as e:
        # Captura erros inesperados durante a criação ou serialização
        raise HTTPException(status_code=500, detail=f"Erro interno ao serializar: {e}")

# --- Rota Principal --- (Opcional)
@app.get("/", tags=["Info"], summary="Endpoint inicial da API")
async def root():
    return {"message": "Bem-vindo à API Comparativa FastAPI (Abstract Factory Refatorado)!"}

# --- Instruções para Execução ---
# uvicorn comparasion.fastapiApp.main:app --reload --port 8001

