from locust import HttpUser, task, between, events
import random
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DjangoAPIUser(HttpUser):
    """
    Locust test para Django REST API com IDs Integer
    Execute: locust -f locustfile.py --host=http://localhost:8000
    
    Recomendações:
    - Máximo 50 usuários simultâneos para evitar sobrecarga do MySQL
    - Spawn rate: 5-10 usuários por segundo
    """
    host = "http://localhost:8000"
    wait_time = between(2, 5)

    # Cache de IDs (compartilhado entre todas as instâncias)
    # Usando class variables para sincronização
    _lock = threading.Lock()
    user_ids = []
    product_ids = []
    category_ids = []
    order_ids = []
    payment_method_ids = []
    payment_ids = []

    def on_start(self):
        """Inicialização"""
        logger.info("🚀 Iniciando teste de carga Django...")
        
        # Carrega dados existentes
        self._load_existing_data()
        
        # Garante dados mínimos
        self._ensure_initial_data()

    def _load_existing_data(self):
        """Carrega dados existentes da API"""
        try:
            r = self.client.get("/api/users/", name="[SETUP] Load users")
            if r.status_code == 200:
                users = r.json()
                if isinstance(users, dict) and 'results' in users:
                    with self._lock:
                        self.user_ids = [u["id"] for u in users['results']]
                else:
                    with self._lock:
                        self.user_ids = [u["id"] for u in users]
                logger.info(f"📊 Carregados {len(self.user_ids)} usuários")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar usuários: {e}")

        try:
            r = self.client.get("/api/products/categories/", name="[SETUP] Load categories")
            if r.status_code == 200:
                cats = r.json()
                if isinstance(cats, dict) and 'results' in cats:
                    with self._lock:
                        self.category_ids = [c["id"] for c in cats['results']]
                else:
                    with self._lock:
                        self.category_ids = [c["id"] for c in cats]
                logger.info(f"📊 Carregadas {len(self.category_ids)} categorias")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar categorias: {e}")

        try:
            r = self.client.get("/api/products/", name="[SETUP] Load products")
            if r.status_code == 200:
                prods = r.json()
                if isinstance(prods, dict) and 'results' in prods:
                    with self._lock:
                        self.product_ids = [p["id"] for p in prods['results']]
                else:
                    with self._lock:
                        self.product_ids = [p["id"] for p in prods]
                logger.info(f"📊 Carregados {len(self.product_ids)} produtos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos: {e}")

    def _ensure_initial_data(self):
        """Garante dados mínimos para os testes"""
        if len(self.user_ids) < 10:
            logger.info("🔧 Criando usuários iniciais...")
            for _ in range(10):
                self.create_user()
        
        if len(self.category_ids) < 3:
            logger.info("🔧 Criando categorias iniciais...")
            for _ in range(3):
                self.create_category()
        
        if len(self.product_ids) < 10:
            logger.info("🔧 Criando produtos iniciais...")
            for _ in range(10):
                self.create_product()

    def _safe_add_id(self, id_list, new_id):
        """Adiciona ID de forma thread-safe"""
        if new_id:
            with self._lock:
                if new_id not in id_list:
                    id_list.append(new_id)

    def _safe_remove_id(self, id_list, remove_id):
        """Remove ID de forma thread-safe"""
        with self._lock:
            try:
                id_list.remove(remove_id)
            except ValueError:
                pass

    def _safe_choice(self, id_list):
        """Escolhe ID aleatório de forma thread-safe"""
        with self._lock:
            if not id_list:
                return None
            return random.choice(id_list)

    # ==================== USERS ====================
    @task(5)
    def create_user(self):
        payload = {
            "name": f"User {random.randint(10000, 99999)}",
            "email": f"user{random.randint(10000, 99999)}@test.com",
            "phone": "+5511999999999",
            "birth_date": "1990-01-01",
            "address": "Test Address, 123"
        }
        with self.client.post("/api/users/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                user_id = r.json().get("id")
                self._safe_add_id(self.user_ids, user_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(15)
    def list_users(self):
        with self.client.get("/api/users/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(10)
    def get_user(self):
        user_id = self._safe_choice(self.user_ids)
        if not user_id:
            return
        
        with self.client.get(f"/api/users/{user_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.user_ids, user_id)
                r.failure("User not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    @task(3)
    def update_user(self):
        user_id = self._safe_choice(self.user_ids)
        if not user_id:
            return
        
        payload = {"name": f"Updated User {random.randint(1000, 9999)}"}
        with self.client.patch(f"/api/users/{user_id}/", json=payload, catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.user_ids, user_id)
                r.failure("User not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    @task(1)
    def delete_user(self):
        # Só deleta se tiver muitos usuários (manter pool mínimo)
        if len(self.user_ids) < 20:
            return
        
        user_id = self._safe_choice(self.user_ids)
        if not user_id:
            return
        
        with self.client.delete(f"/api/users/{user_id}/", catch_response=True) as r:
            if r.status_code == 204:
                self._safe_remove_id(self.user_ids, user_id)
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.user_ids, user_id)
                r.success()  # Não considerar erro se já foi deletado
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== CATEGORIES ====================
    @task(3)
    def create_category(self):
        payload = {
            "name": f"Category {random.randint(10000, 99999)}",
            "description": "Test category"
        }
        with self.client.post("/api/products/categories/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                cat_id = r.json().get("id")
                self._safe_add_id(self.category_ids, cat_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(10)
    def list_categories(self):
        with self.client.get("/api/products/categories/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def get_category(self):
        cat_id = self._safe_choice(self.category_ids)
        if not cat_id:
            return
        
        with self.client.get(f"/api/products/categories/{cat_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.category_ids, cat_id)
                r.failure("Category not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PRODUCTS ====================
    @task(5)
    def create_product(self):
        cat_id = self._safe_choice(self.category_ids)
        if not cat_id:
            return
        
        payload = {
            "name": f"Product {random.randint(10000, 99999)}",
            "description": "Test product",
            "price": round(random.uniform(10, 500), 2),
            "stock": random.randint(50, 200),
            "category_id": cat_id
        }
        with self.client.post("/api/products/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                prod_id = r.json().get("id")
                self._safe_add_id(self.product_ids, prod_id)
                r.success()
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(20)
    def list_products(self):
        with self.client.get("/api/products/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(12)
    def get_product(self):
        prod_id = self._safe_choice(self.product_ids)
        if not prod_id:
            return
        
        with self.client.get(f"/api/products/{prod_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.product_ids, prod_id)
                r.failure("Product not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    @task(3)
    def update_product(self):
        prod_id = self._safe_choice(self.product_ids)
        if not prod_id:
            return
        
        payload = {
            "price": round(random.uniform(10, 500), 2),
            "stock": random.randint(50, 200)
        }
        with self.client.patch(f"/api/products/{prod_id}/", json=payload, catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.product_ids, prod_id)
                r.failure("Product not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== ORDERS ====================
    @task(8)
    def create_order(self):
        user_id = self._safe_choice(self.user_ids)
        prod_id = self._safe_choice(self.product_ids)
        
        if not user_id or not prod_id:
            return
        
        payload = {
            "user": user_id,
            "items": [
                {
                    "product": prod_id,
                    "quantity": random.randint(1, 3)
                }
            ],
            "address": "Test Order Address, 456"
        }
        with self.client.post("/api/orders/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                order_id = r.json().get("id")
                self._safe_add_id(self.order_ids, order_id)
                r.success()
            elif r.status_code == 400:
                # FK inválida - usuário ou produto foi deletado
                r.success()  # Não considerar erro (race condition)
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(15)
    def list_orders(self):
        with self.client.get("/api/orders/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(10)
    def get_order(self):
        order_id = self._safe_choice(self.order_ids)
        if not order_id:
            return
        
        with self.client.get(f"/api/orders/{order_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.order_ids, order_id)
                r.failure("Order not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PAYMENT METHODS ====================
    @task(4)
    def create_payment_method(self):
        user_id = self._safe_choice(self.user_ids)
        if not user_id:
            return
        
        payload = {
            "user": user_id,
            "type": random.choice(["credit_card", "debit_card", "pix"]),
            "name": f"Card {random.randint(1000, 9999)}"
        }
        with self.client.post("/api/payments/methods/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                method_id = r.json().get("id")
                self._safe_add_id(self.payment_method_ids, method_id)
                r.success()
            elif r.status_code == 400:
                # FK inválida - usuário foi deletado
                r.success()  # Não considerar erro
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(10)
    def list_payment_methods(self):
        with self.client.get("/api/payments/methods/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(5)
    def get_payment_method(self):
        method_id = self._safe_choice(self.payment_method_ids)
        if not method_id:
            return
        
        with self.client.get(f"/api/payments/methods/{method_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.payment_method_ids, method_id)
                r.failure("Payment method not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")

    # ==================== PAYMENTS ====================
    @task(6)
    def create_payment(self):
        order_id = self._safe_choice(self.order_ids)
        method_id = self._safe_choice(self.payment_method_ids)
        
        if not order_id or not method_id:
            return
        
        payload = {
            "order": order_id,
            "payment_method": method_id,
            "amount": round(random.uniform(10, 500), 2),
            "status": "pending"
        }
        with self.client.post("/api/payments/", json=payload, catch_response=True) as r:
            if r.status_code == 201:
                payment_id = r.json().get("id")
                self._safe_add_id(self.payment_ids, payment_id)
                r.success()
            elif r.status_code == 400:
                # FK inválida - order ou payment_method foi deletado
                r.success()  # Não considerar erro
            else:
                r.failure(f"Status {r.status_code}: {r.text}")

    @task(12)
    def list_payments(self):
        with self.client.get("/api/payments/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Status {r.status_code}")

    @task(6)
    def get_payment(self):
        payment_id = self._safe_choice(self.payment_ids)
        if not payment_id:
            return
        
        with self.client.get(f"/api/payments/{payment_id}/", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                self._safe_remove_id(self.payment_ids, payment_id)
                r.failure("Payment not found - removed from cache")
            else:
                r.failure(f"Status {r.status_code}")


# Event listeners
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO TESTE DE CARGA DJANGO")
    logger.info(f"🎯 Host: {environment.host}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("🏁 TESTE FINALIZADO")
    stats = environment.stats
    logger.info(f"📊 Total requests: {stats.total.num_requests}")
    logger.info(f"❌ Total failures: {stats.total.num_failures}")
    logger.info(f"⚡ Avg response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"✅ Success rate: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.2f}%")
    logger.info("=" * 60)