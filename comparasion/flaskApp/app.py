
from flask import Flask, request, Response
from abstratct_factory.factory import SerializerFactory
from facade.checkout_services import CheckoutFacade
from strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy

app = Flask(__name__)

#Para rodar o server, use o comando: (python app.py), dentro do diretório flaskApp
# O servidor estará rodando em http://127.0.0.1:5000

# As Rotes testadas no ThunderClient ou Postman foram:
#curl -X GET "http://127.0.0.1:5000/serialize/json"
#curl -X POST "http://127.0.0.1:5000/pay/creditcard" -H "Content-Type: application/json" -d '{"amount": 100, "currency": "USD"}'
#curl -X POST "http://127.0.0.1:5000/checkout" -H "Content-Type: application/json" -d '{"product_id": 1, "zip_code": "12345", "subtotal": 100.0}'

# app.py (Rota)
@app.route("/")
def index():
    return "Hello, World!"

@app.route("/serialize/<format>")
def handle_serialization(format):
    data = {"user": {"name": "Alice", "age": 25, "active": True}}
    try:
        serializer = SerializerFactory.create_serializer(format)
        return Response(
            serializer.serialize(data),
            mimetype=f"application/{format}"
        )
    except ValueError as e:
        return {"error": str(e)}, 400


# app.py (Rota)
@app.route("/pay/<method>", methods=["POST"])
def process_payment(method):
    amount = request.json.get("amount")
    if method == "creditcard":
        processor = PaymentProcessor(CreditCardStrategy())
    elif method == "paypal":
        processor = PaymentProcessor(PayPalStrategy())
    else:
        return {"error": "Método inválido"}, 400
    
    return {"result": processor.execute_payment(amount)}

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    facade = CheckoutFacade()
    try:
        result = facade.complete_order(
            product_id=data["product_id"],
            zip_code=data["zip_code"],
            subtotal=data["subtotal"]
        )
        return result
    except ValueError as e:
        return {"error": str(e)}, 400
    
    
if __name__ == "__main__":
    app.run(debug=True)