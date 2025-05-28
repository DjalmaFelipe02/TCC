
from flask import Flask, request, Response
from abstratct_factory.factory import SerializerFactory
from facade.checkout_services import CheckoutFacade
from strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy

app = Flask(__name__)

@app.route("/serialize/<format>")
def handle_serialization(format):
    """
    Serializa dados no formato especificado (json ou xml).

    Args:
        format (str): Formato de serialização ('json' ou 'xml').

    Returns:
        Response: Dados serializados ou mensagem de erro.
    """
    data = {"user": {"name": "Alice", "age": 25, "active": True}}
    try:
        serializer = SerializerFactory.create_serializer(format)
        return Response(
            serializer.serialize(data),
            mimetype=f"application/{format}"
        )
    except ValueError as e:
        return {"error": str(e)}, 400



@app.route("/pay/<method>", methods=["POST"])
def process_payment(method):
    """
    Processa pagamento utilizando a estratégia informada(Strategy).

    Args:
        method (str): Método de pagamento ('creditcard' ou 'paypal').

    Returns:
        dict: Resultado do pagamento ou mensagem de erro.
    """
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
    """
    Realiza o checkout utilizando o padrão Facade.

    Returns:
        dict: Resultado do pedido ou mensagem de erro.
    """
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