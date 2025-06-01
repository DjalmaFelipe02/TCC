from flask import Flask, request, Response, jsonify, abort
from werkzeug.exceptions import BadRequest, NotFound

# Importações dos padrões de projeto
# Corrigido o nome da pasta para abstract_factory
from .abstract_factory.factory import SerializerFactory
from .abstract_factory.serializers import Serializer # Importar a interface base
from .facade.checkout_services import CheckoutFacade
from .strategy.payment_processor import PaymentProcessor, CreditCardStrategy, PayPalStrategy, PaymentStrategy

# --- Configuração da Aplicação Flask ---
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False # Manter a ordem dos dicionários em JSON

# Dados de exemplo para serialização (usados no GET)
DEFAULT_SERIALIZATION_DATA_FLASK = {"name": "Flask User", "id": 456, "active": False}

# --- Implementação do Padrão Abstract Factory (Serialização) ---
@app.route("/serialize/<string:format>", methods=["GET"])
def handle_serialization_factory_get(format):
    """Endpoint GET para demonstrar o padrão Abstract Factory (Flask).

    Recebe o formato desejado na URL (json ou xml).
    Usa dados de exemplo definidos internamente.
    Utiliza a SerializerFactory para obter a instância correta do Serializer.
    Retorna os dados serializados com o mimetype apropriado.

    Exemplo de teste:
    curl -X GET "http://127.0.0.1:5000/serialize/json"
    curl -X GET "http://127.0.0.1:5000/serialize/xml"
    """
    try:
        # Utiliza a Factory para obter o serializador correto
        serializer = SerializerFactory.create_serializer(format)
        # Usa os dados de exemplo definidos no início do arquivo
        serialized_data = serializer.serialize(DEFAULT_SERIALIZATION_DATA_FLASK)
        mimetype = f"application/{format}"
        # Retorna a resposta com os dados serializados e o mimetype correto
        return Response(serialized_data, mimetype=mimetype)
    except ValueError as e:
        # Retorna erro 400 se o formato for inválido
        abort(400, description=str(e))
    except Exception as e:
        # Tratamento genérico de erro
        abort(500, description=f"Erro interno ao serializar: {e}")

# --- Implementação do Padrão Strategy (Pagamento) ---
@app.route("/pay/<string:method>", methods=["POST"])
def process_payment_strategy(method):
    """Endpoint para demonstrar o padrão Strategy (Flask).

    Recebe o método de pagamento na URL (creditcard ou paypal) e os detalhes
    do pagamento no corpo da requisição.
    Instancia o PaymentProcessor com a Strategy apropriada.

    Exemplo de teste:
    curl -X POST "http://127.0.0.1:5000/pay/creditcard" -H "Content-Type: application/json" -d 	rä{\"amount\": 150.75, \"currency\": \"BRL\"}"
    curl -X POST "http://127.0.0.1:5000/pay/paypal" -H "Content-Type: application/json" -d 	rä{\"amount\": 99.99}"
    """
    if not request.is_json:
        abort(400, description="Requisição precisa ser JSON.")

    data = request.get_json()
    amount = data.get("amount")
    currency = data.get("currency", "USD") # Default currency

    if amount is None:
        abort(400, description="O campo 'amount' é obrigatório.")

    # Seleciona a estratégia com base no método da URL
    if method == "creditcard":
        strategy = CreditCardStrategy()
    elif method == "paypal":
        strategy = PayPalStrategy()
    else:
        # Retorna erro 404 se o método for inválido (ou 400, dependendo da semântica desejada)
        abort(404, description=f"Método de pagamento '{method}' não encontrado.")

    # Cria o contexto com a estratégia selecionada
    processor = PaymentProcessor(strategy)
    # Executa o pagamento
    result = processor.execute_payment(amount)

    # Retorna o resultado como JSON
    return jsonify({"payment_details": result, "currency": currency})

# --- Implementação do Padrão Facade (Checkout) ---
@app.route("/checkout", methods=["POST"])
def process_checkout_facade():
    """Endpoint para demonstrar o padrão Facade (Flask).

    Recebe os detalhes do pedido no corpo da requisição.
    Utiliza a CheckoutFacade para simplificar a interação com os subsistemas.

    Exemplo de teste:
    curl -X POST "http://127.0.0.1:5000/checkout" -H "Content-Type: application/json" -d 	rä{\"product_id\": 2, \"zip_code\": \"99888\", \"subtotal\": 250.0}"
    """
    if not request.is_json:
        abort(400, description="Requisição precisa ser JSON.")

    data = request.get_json()
    product_id = data.get("product_id")
    zip_code = data.get("zip_code")
    subtotal = data.get("subtotal")

    # Validação básica dos dados de entrada
    if not all([product_id, zip_code, subtotal is not None]):
        abort(400, description="Campos 'product_id', 'zip_code', e 'subtotal' são obrigatórios.")

    # Instancia a Facade
    facade = CheckoutFacade()
    try:
        # Chama o método da Facade para processar o pedido
        result = facade.complete_order(
            product_id=int(product_id), # Garante que seja int
            zip_code=str(zip_code),
            subtotal=float(subtotal) # Garante que seja float
        )
        # Retorna o resultado como JSON
        return jsonify(result)
    except ValueError as e:
        # Retorna erro 400 em caso de falha (ex: estoque)
        abort(400, description=str(e))
    except Exception as e:
        # Tratamento genérico de erro
        abort(500, description=f"Erro interno no checkout: {e}")

# --- Rota Principal --- (Opcional)
@app.route("/", methods=["GET"])
def index():
    """Endpoint inicial da API Flask."""
    return jsonify({"message": "Bem-vindo à API Comparativa Flask! Use os endpoints para testar os padrões."})

# --- Tratamento de Erros HTTP ---
@app.errorhandler(400)
def handle_bad_request(error):
    """Handler para erros 400 Bad Request."""
    response = jsonify({"error": "Bad Request", "message": error.description})
    response.status_code = 400
    return response

@app.errorhandler(404)
def handle_not_found(error):
    """Handler para erros 404 Not Found."""
    response = jsonify({"error": "Not Found", "message": error.description})
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_internal_error(error):
    """Handler para erros 500 Internal Server Error."""
    response = jsonify({"error": "Internal Server Error", "message": error.description})
    response.status_code = 500
    return response

# --- Execução da Aplicação --- (se executado diretamente)
if __name__ == "__main__":
    # Roda o servidor Flask em modo debug
    # O servidor estará rodando em http://127.0.0.1:5000 por padrão
    print("Iniciando servidor Flask em http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

