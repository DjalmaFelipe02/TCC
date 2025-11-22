from locust import HttpUser, task, between, events
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EcomUser(HttpUser):
    """
    Locust test that targets the Flask app (or Django) because both share the same API routes.
    Set the host when running Locust or in the UI (e.g. http://127.0.0.1:8000 or http://127.0.0.1:5000).
    """
    host = "http://127.0.0.1:5000"

    wait_time = between(0.5, 2)

    # cached ids for CRUD operations
    user_ids = []
    category_ids = []
    product_ids = []
    order_ids = []
    order_item_ids = []
    payment_method_ids = []
    payment_ids = []

    def on_start(self):
        # try to seed lists from server
        try:
            r = self.client.get("/api/users/")
            if r.status_code == 200 and r.json():
                self.user_ids = [u["id"] for u in r.json()]
        except Exception:
            pass
        try:
            r = self.client.get("/api/products/categories")
            if r.status_code == 200 and r.json():
                self.category_ids = [c["id"] for c in r.json()]
        except Exception:
            pass
        try:
            r = self.client.get("/api/products/")
            if r.status_code == 200 and r.json():
                self.product_ids = [p["id"] for p in r.json()]
        except Exception:
            pass

    # ------- USERS -------
    @task(3)
    def create_user(self):
        rand_num = random.randint(100000, 999999)
        payload = {
            "name": f"Locust User {rand_num}",
            "email": f"locust_{rand_num}@example.com",
            "phone": f"11{random.randint(900000000,999999999)}",
            "birth_date": "1990-01-01",
            "address": "Rua Locust, 1"
        }
        r = self.client.post("/api/users/", json=payload)
        if r.status_code == 201:
            self.user_ids.append(r.json().get("id"))
        else:
            self._log_fail("CREATE_USER", r)

    @task(6)
    def list_users(self):
        self.client.get("/api/users/")

    # ------- CATEGORIES & PRODUCTS -------
    @task(2)
    def create_category(self):
        payload = {"name": f"Cat {random.randint(10000, 99999)}", "description": "Criada pelo Locust"}
        r = self.client.post("/api/products/categories", json=payload)
        if r.status_code == 201:
            self.category_ids.append(r.json().get("id"))
        else:
            self._log_fail("CREATE_CATEGORY", r)

    @task(6)
    def list_categories(self):
        self.client.get("/api/products/categories")

    @task(3)
    def create_product(self):
        if not self.category_ids:
            self.create_category()
        payload = {
            "name": f"Prod {random.randint(100000, 999999)}",
            "description": "Produto de teste",
            "price": round(random.uniform(10, 500), 2),
            "stock": random.randint(1, 50),
            "category_id": (random.choice(self.category_ids) if self.category_ids else None)
        }
        r = self.client.post("/api/products/", json=payload)
        if r.status_code == 201:
            pid = r.json().get("id")
            if pid:
                self.product_ids.append(pid)
        else:
            self._log_fail("CREATE_PRODUCT", r)

    @task(8)
    def list_products(self):
        self.client.get("/api/products/")

    # ------- ORDERS & ORDER ITEMS -------
    @task(4)
    def create_order(self):
        if not self.user_ids:
            self.create_user()
        if not self.product_ids:
            self.create_product()
        if not self.user_ids or not self.product_ids:
            return
        user = random.choice(self.user_ids)
        prod = random.choice(self.product_ids)
        payload = {
            "user": user,
            "items": [{"product": prod, "quantity": random.randint(1, 3)}],
            "address": "Endereço Locust, 99"
        }
        r = self.client.post("/api/orders/", json=payload)
        if r.status_code == 201:
            oid = r.json().get("id")
            if oid:
                self.order_ids.append(oid)
        else:
            self._log_fail("CREATE_ORDER", r)

    @task(6)
    def list_orders(self):
        self.client.get("/api/orders/")

    @task(2)
    def create_order_item(self):
        # try nested endpoint first, fallback to top-level
        if not self.order_ids:
            self.create_order()
        if not self.product_ids:
            self.create_product()
        if not self.order_ids or not self.product_ids:
            return
        order_id = random.choice(self.order_ids)
        prod = random.choice(self.product_ids)
        payload = {"product": prod, "quantity": random.randint(1,5)}
        endpoints = [f"/api/orders/{order_id}/items/", "/api/orders/items/", "/api/order-items/"]
        for ep in endpoints:
            r = self.client.post(ep, json=payload)
            if r.status_code in (200, 201):
                iid = None
                try:
                    iid = r.json().get("id")
                except Exception:
                    pass
                if iid:
                    self.order_item_ids.append(iid)
                return
            if r.status_code in (404, 405):
                continue
            self._log_fail(f"CREATE_ORDER_ITEM @ {ep}", r)
            return

    @task(4)
    def list_order_items(self):
        if not self.order_ids:
            return
        order_id = random.choice(self.order_ids)
        endpoints = [f"/api/orders/{order_id}/items/", "/api/orders/items/", "/api/order-items/"]
        for ep in endpoints:
            r = self.client.get(ep)
            if r.status_code == 200:
                return
            if r.status_code == 404:
                continue
            self._log_fail(f"LIST_ORDER_ITEMS @ {ep}", r)
            return

    @task(2)
    def update_order_item(self):
        if not self.order_item_ids:
            return
        item_id = random.choice(self.order_item_ids)
        # ensure it exists
        rcheck = self.client.get(f"/api/orders/items/{item_id}/")
        if rcheck.status_code != 200:
            # if not present remove from cache
            try:
                self.order_item_ids.remove(item_id)
            except Exception:
                pass
            return
        r = self.client.patch(f"/api/orders/items/{item_id}/", json={"quantity": random.randint(1, 10)})
        if r.status_code not in (200,):
            self._log_fail("PATCH_ORDER_ITEM", r)

    # ------- PAYMENTS & METHODS -------
    @task(2)
    def create_payment_method(self):
        if not self.user_ids:
            self.create_user()
        payload = {
            "user": random.choice(self.user_ids) if self.user_ids else None, 
            "type": "credit_card", 
            "name": f"Card {random.randint(100000, 999999)}"
        }
        r = self.client.post("/api/payments/methods", json=payload)
        if r.status_code == 201:
            mid = r.json().get("id")
            if mid:
                self.payment_method_ids.append(mid)
        else:
            self._log_fail("CREATE_PAYMENT_METHOD", r)

    @task(4)
    def list_payment_methods(self):
        self.client.get("/api/payments/methods")

    @task(3)
    def create_payment(self):
        if not self.order_ids:
            self.create_order()
        if not self.payment_method_ids:
            self.create_payment_method()
        if not self.order_ids or not self.payment_method_ids:
            return
        payload = {
            "order": random.choice(self.order_ids), 
            "payment_method": random.choice(self.payment_method_ids), 
            "amount": round(random.uniform(10,500),2)
        }
        r = self.client.post("/api/payments/", json=payload)
        if r.status_code == 201:
            pid = r.json().get("id")
            if pid:
                self.payment_ids.append(pid)
        else:
            self._log_fail("CREATE_PAYMENT", r)

    @task(6)
    def list_payments(self):
        self.client.get("/api/payments/")

    # ------- helpers -------
    def _log_fail(self, name, resp):
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print(f"[Locust] {name} -> {resp.status_code} : {body}")

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