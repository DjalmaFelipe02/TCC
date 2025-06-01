from locust import HttpUser, task, between
import random

class EcommerceUser(HttpUser):
    """Simula um usuário navegando e realizando ações em um e-commerce.

    Este usuário testa os endpoints que implementam os padrões:
    - Abstract Factory (GET /serialize/...)
    - Strategy (POST /pay/...)
    - Facade (POST /checkout)
    """
    # Tempo de espera entre as tarefas (simula o "pensamento" do usuário)
    wait_time = between(1, 3) # Espera entre 1 e 3 segundos

    # --- Tarefas relacionadas ao Abstract Factory (Serialização) ---
    @task(1) # Menor peso, serialização pode ser menos frequente
    def serialize_json(self):
        """Testa o endpoint GET de serialização JSON."""
        self.client.get("/serialize/json", name="/serialize/[format]")

    @task(1) # Menor peso
    def serialize_xml(self):
        """Testa o endpoint GET de serialização XML."""
        self.client.get("/serialize/xml", name="/serialize/[format]")

    # --- Tarefas relacionadas ao Strategy (Pagamento) ---
    @task(3) # Peso maior, pagamentos são ações comuns
    def pay_credit_card(self):
        """Testa o endpoint POST de pagamento com Cartão de Crédito.

        Usa valores de pagamento aleatórios.
        """
        amount = round(random.uniform(10.0, 500.0), 2) # Valor aleatório
        payload = {"amount": amount, "currency": random.choice(["USD", "BRL", "EUR"])}
        self.client.post("/pay/creditcard", json=payload, name="/pay/[method]")

    @task(2) # Peso médio, PayPal pode ser menos usado que cartão
    def pay_paypal(self):
        """Testa o endpoint POST de pagamento com PayPal.

        Usa valores de pagamento aleatórios.
        """
        amount = round(random.uniform(5.0, 300.0), 2)
        payload = {"amount": amount, "currency": "USD"} # PayPal geralmente em USD
        self.client.post("/pay/paypal", json=payload, name="/pay/[method]")

    # --- Tarefa relacionada ao Facade (Checkout) ---
    @task(4) # Maior peso, checkout é uma ação crucial e comum
    def checkout(self):
        """Testa o endpoint POST de checkout.

        Usa IDs de produto, CEPs e subtotais aleatórios.
        """
        payload = {
            "product_id": random.randint(1, 1000),
            "zip_code": f"{random.randint(10000, 99999)}",
            "subtotal": round(random.uniform(20.0, 1000.0), 2)
        }
        self.client.post("/checkout", json=payload)

    # --- (Opcional) Tarefa para acessar a raiz --- 
    # Descomente se quiser incluir acessos à página inicial nos testes
    # @task(1)
    # def view_root(self):
    #     """Acessa o endpoint raiz ("/")."""
    #     self.client.get("/")

    def on_start(self):
        """(Opcional) Código a ser executado quando um usuário Locust inicia."""
        print("Iniciando um novo usuário simulado...")
        # Exemplo: poderia fazer login aqui se a API exigisse autenticação
        pass

    def on_stop(self):
        """(Opcional) Código a ser executado quando um usuário Locust para."""
        print("Parando um usuário simulado.")
        pass

# Para executar:
# 1. Certifique-se que a aplicação Flask ou FastAPI esteja rodando.
# 2. Navegue até a pasta `load_tests` no terminal.
# 3. Execute o Locust:
#    locust -f locustfile.py --host http://127.0.0.1:5000  # Para testar Flask
#    locust -f locustfile.py --host http://127.0.0.1:8001  # Para testar FastAPI
# 4. Acesse a interface web do Locust (geralmente http://localhost:8089).