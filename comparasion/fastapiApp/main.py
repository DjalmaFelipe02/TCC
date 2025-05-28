from fastapi import FastAPI, HTTPException, Response, Path, Depends
from fastapiApp.strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy
from fastapiApp.facade.checkout_services import CheckoutFacade
from pydantic import BaseModel

app = FastAPI()

# Classe para requisição de pagamento
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"

class CheckoutRequest(BaseModel):
    product_id: int
    zip_code: str
    subtotal: float

# Injeção de Dependência
def get_processor(method: str = Path(...)):
    """
    Injeta o Strategy de pagamento baseada no método informado.

    Args:
        method (str): Método de pagamento ('creditcard' ou 'paypal').

    Returns:
        PaymentProcessor: Processador de pagamento com a estratégia escolhida.

    Raises:
        HTTPException: Se o método for inválido.
    """
    if method == "creditcard":
        return PaymentProcessor(CreditCardStrategy())
    elif method == "paypal":
        return PaymentProcessor(PayPalStrategy())
    raise HTTPException(400, detail="Método inválido")

@app.post("/pay/{method}")
async def pay(
    method: str,
    request: PaymentRequest,
    processor: PaymentProcessor = Depends(get_processor)
):
    """
    Processa pagamento utilizando a estratégia informada (Strategy).

    Args:
        method (str): Método de pagamento ('creditcard' ou 'paypal').
        request (PaymentRequest): Dados do pagamento.
        processor (PaymentProcessor): Processador injetado.

    Returns:
        dict: Resultado do pagamento e moeda.
    """
    return {
        "result": processor.execute_payment(request.amount),
        "currency": request.currency
    }

@app.post("/checkout")
async def checkout(request: CheckoutRequest):
    """
    Realiza o checkout utilizando o padrão Facade.

    Args:
        request (CheckoutRequest): Dados do pedido.

    Returns:
        dict: Resultado do pedido ou mensagem de erro.

    Raises:
        HTTPException: Se ocorrer erro no processamento do pedido.
    """
    facade = CheckoutFacade()
    try:
        return facade.complete_order(
            product_id=request.product_id,
            zip_code=request.zip_code,
            subtotal=request.subtotal
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))