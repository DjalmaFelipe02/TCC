from fastapi import FastAPI, HTTPException, Response, Path, Depends
from fastapiApp.strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy
from fastapiApp.facade.checkout_services import CheckoutFacade
from pydantic import BaseModel
from typing import Literal

app = FastAPI()

#Como colocar o fastapi para rodar o servidor
# uvicorn fastapiApp.main:app --reload


# Testar essa Rote no ThunderClient ou Postman
#curl -X POST "http://127.0.0.1:8000/checkout" -H "Content-Type: application/json" -d '{"product_id": 1, "zip_code": "12345", "subtotal": 100.0}'


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
    return {
        "result": processor.execute_payment(request.amount),
        "currency": request.currency
    }

@app.post("/checkout")
async def checkout(request: CheckoutRequest):
    facade = CheckoutFacade()
    try:
        return facade.complete_order(
            product_id=request.product_id,
            zip_code=request.zip_code,
            subtotal=request.subtotal
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))