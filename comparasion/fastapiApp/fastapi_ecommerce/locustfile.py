from locust import HttpUser, task, between, events
import random
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcomUser(HttpUser):
    """
    Locust test com IDs Integer
    Execute: locust -f locustfile.py --host=http://127.0.0.1:8000
    """
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)

    # Cache de IDs (agora são integers)
    user_ids = []
    category_ids = []
    product_ids = []
    order_ids = []
    payment_method_ids = []
    payment_ids = []

    def on_start(self):
        """Inicialização e verificação de conectividade"""
        logger.info("🚀 Iniciando teste de carga...")
        
        # Testa conectividade
        try:
            r = self.client.get("/docs", name="[HEALTHCHECK] /docs")
            if r.status_code != 200:
                logger.error(f"❌ API não está respondendo: {r.status_code}")
                return
            logger.info("✅ API está online")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            return

        # Carrega dados existentes
        self._load_existing_data()
        
        # Cria dados iniciais se necessário
        self._ensure_initial_data()

    def _load_existing_data(self):
        """Carrega dados existentes da API"""
        try:
            r = self.client.get("/api/users/", name="[SETUP] Load users")
            if r.status_code == 200:
                users = r.json()
                self.user_ids = [u["id"] for u in users]
                logger.info(f"📊 Carregados {len(self.user_ids)} usuários")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar usuários: {e}")

        try:
            r = self.client.get("/api/products/categories", name="[SETUP] Load categories")
            if r.status_code == 200:
                cats = r.json()
                self.category_ids = [c["id"] for c in cats]
                logger.info(f"📊 Carregadas {len(self.category_ids)} categorias")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar categorias: {e}")

        try:
            r = self.client.get("/api/products/", name="[SETUP] Load products")
            if r.status_code == 200:
                prods = r.json()
                self.product_ids = [p["id"] for p in prods]
                logger.info(f"📊 Carregados {len(self.product_ids)} produtos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos: {e}")

    def _ensure_initial_data(self):
        """Garante dados mínimos para os testes"""
        if len(self.user_ids) < 3:
            logger.info("🔧 Criando usuários iniciais...")
            for _ in range(3):
                self.create_user()
        
        if len(self.category_ids) < 2:
            logger.info("🔧 Criando categorias iniciais...")
            for _ in range(2):
                self.create_category()
        
        if len(self.product_ids) < 5:
            logger.info("🔧 Criando produtos iniciais...")
            for _ in range(5):
                self.create_product()

    # ==================== USERS ====================
    @task(3)
    def create_user(self):
        payload = {
            "name": f"User {random.randint(10000, 99999)}",
            "email": f"user{random.randint(10000, 99999)}@test.com",
            "phone": f"+55{random.randint(10000000000, 99999999999)}",
            "birth_date": "1990-01-01",
            "address": "Test Address, 123"
        }
        with self.client.post("/api/users/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                user_id = r.json().get("id")
                if user_id:
                    self.user_ids.append(user_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(8)
    def list_users(self):
        with self.client.get("/api/users/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def get_user(self):
        if not self.user_ids:
            return
        user_id = random.choice(self.user_ids)
        with self.client.get(f"/api/users/{user_id}", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                try:
                    self.user_ids.remove(user_id)
                except ValueError:
                    pass
                r.failure("User not found")
            else:
                r.failure(f"Status {r.status_code}")

    @task(2)
    def update_user(self):
        if not self.user_ids:
            return
        user_id = random.choice(self.user_ids)
        payload = {"name": f"Updated User {random.randint(1000, 9999)}"}
        with self.client.patch(f"/api/users/{user_id}", json=payload, catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== CATEGORIES ====================
    @task(2)
    def create_category(self):
        payload = {
            "name": f"Category {random.randint(10000, 99999)}",
            "description": "Test category"
        }
        with self.client.post("/api/products/categories", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                cat_id = r.json().get("id")
                if cat_id:
                    self.category_ids.append(cat_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(6)
    def list_categories(self):
        with self.client.get("/api/products/categories", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PRODUCTS ====================
    @task(3)
    def create_product(self):
        if not self.category_ids:
            self.create_category()
            if not self.category_ids:
                return
        
        payload = {
            "name": f"Product {random.randint(10000, 99999)}",
            "description": "Test product",
            "price": round(random.uniform(10, 500), 2),
            "stock": random.randint(50, 200),
            "category_id": random.choice(self.category_ids)
        }
        with self.client.post("/api/products/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                prod_id = r.json().get("id")
                if prod_id:
                    self.product_ids.append(prod_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(10)
    def list_products(self):
        with self.client.get("/api/products/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(6)
    def get_product(self):
        if not self.product_ids:
            return
        prod_id = random.choice(self.product_ids)
        with self.client.get(f"/api/products/{prod_id}", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                try:
                    self.product_ids.remove(prod_id)
                except ValueError:
                    pass
                r.failure("Product not found")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== ORDERS ====================
    @task(4)
    def create_order(self):
        if not self.user_ids or not self.product_ids:
            return
        
        user_id = random.choice(self.user_ids)
        prod_id = random.choice(self.product_ids)
        
        payload = {
            "user_id": user_id,
            "items": [
                {
                    "product_id": prod_id,
                    "quantity": random.randint(1, 3)
                }
            ],
            "address": "Test Order Address, 456"
        }
        with self.client.post("/api/orders/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                order_id = r.json().get("id")
                if order_id:
                    self.order_ids.append(order_id)
                r.success()
            elif r.status_code == 400:
                # Pode ser falta de estoque
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(8)
    def list_orders(self):
        with self.client.get("/api/orders/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def get_order(self):
        if not self.order_ids:
            return
        order_id = random.choice(self.order_ids)
        with self.client.get(f"/api/orders/{order_id}", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                try:
                    self.order_ids.remove(order_id)
                except ValueError:
                    pass
                r.failure("Order not found")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PAYMENT METHODS ====================
    @task(2)
    def create_payment_method(self):
        if not self.user_ids:
            return
        
        payload = {
            "user_id": random.choice(self.user_ids),
            "type": random.choice(["credit_card", "debit_card", "pix"]),
            "name": f"Card {random.randint(1000, 9999)}"
        }
        with self.client.post("/api/payments/methods", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                method_id = r.json().get("id")
                if method_id:
                    self.payment_method_ids.append(method_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(6)
    def list_payment_methods(self):
        with self.client.get("/api/payments/methods", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PAYMENTS ====================
    @task(3)
    def create_payment(self):
        if not self.order_ids or not self.payment_method_ids:
            return
        
        payload = {
            "order_id": random.choice(self.order_ids),
            "payment_method_id": random.choice(self.payment_method_ids),
            "amount": round(random.uniform(10, 500), 2)
        }
        with self.client.post("/api/payments/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                payment_id = r.json().get("id")
                if payment_id:
                    self.payment_ids.append(payment_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(6)
    def list_payments(self):
        with self.client.get("/api/payments/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")


# Event listeners
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO TESTE DE CARGA")
    logger.info(f"🎯 Host: {environment.host}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("🏁 TESTE FINALIZADO")
    logger.info("=" * 60)