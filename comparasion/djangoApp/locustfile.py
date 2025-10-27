
from locust import HttpUser, task, between
import random
import uuid

class DjangoAPIUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://localhost:8000"  # Altere para o host da sua API, se necessário

    # IDs para armazenar os IDs dos recursos criados para operações de PUT/DELETE
    user_ids = []
    product_ids = []
    category_ids = []
    order_ids = []
    order_item_ids = []
    payment_ids = []
    payment_method_ids = []

    def on_start(self):
        self.session_prefix = str(uuid.uuid4())[:8]
        # Garante que haja pelo menos um usuário, categoria e método de pagamento para as operações subsequentes
        self.create_user()
        self.create_category()
        self.create_payment_method()

    # --- User Endpoints --- #
    @task(3)
    def create_user(self):
        user_data = {
            "name": f"{self.session_prefix}_User_{uuid.uuid4()}",
            "email": f"user_{self.session_prefix}_{uuid.uuid4()}@example.com",
            "phone": "11999999999",
            "birth_date": "1990-01-01",
            "address": "Rua Exemplo, 123"
        }
        response = self.client.post("/api/users/", json=user_data)
        if response.status_code == 201:
            self.user_ids.append(response.json()["id"])
        else:
            try:
                body = response.json()
            except Exception:
                body = response.text
            print("CREATE_USER FAILED:", response.status_code, body)

    @task(10)
    def get_users(self):
        self.client.get("/api/users/")

    @task(5)
    def get_single_user(self):
        if self.user_ids:
            user_id = random.choice(self.user_ids)
            self.client.get(f"/api/users/{user_id}/")

    @task(2)
    def update_user(self):
        if self.user_ids:
            user_id = random.choice(self.user_ids)
            updated_data = {"name": f"Updated User {uuid.uuid4()}"}
            self.client.patch(f"/api/users/{user_id}/", json=updated_data)

    @task(1)
    def delete_user(self):
        if self.user_ids:
            user_id = self.user_ids.pop(0)  # Remove o mais antigo para evitar repetição
            self.client.delete(f"/api/users/{user_id}/")

    # --- Product Endpoints --- #
    @task(3)
    def create_category(self):
        category_data = {"name": f"Category {uuid.uuid4()}", "description": "A new category"}
        response = self.client.post("/api/products/categories/", json=category_data)
        if response.status_code == 201:
            self.category_ids.append(response.json()["id"])

    @task(10)
    def get_categories(self):
        self.client.get("/api/products/categories/")

    @task(3)
    def create_product(self):
        if not self.category_ids: 
            self.create_category() 

        product_data = {
            "name": f"Product {uuid.uuid4()}",
            "description": "Awesome product",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(1, 100),
            "category_id": random.choice(self.category_ids)
        }
        response = self.client.post("/api/products/", json=product_data)
        if response.status_code == 201:
            self.product_ids.append(response.json()["id"])
        else:
            print("CREATE_PRODUCT ERROR:", response.status_code, response.text)

    @task(10)
    def get_products(self):
        self.client.get("/api/products/")

    @task(5)
    def get_single_product(self):
        if self.product_ids:
            product_id = random.choice(self.product_ids)
            self.client.get(f"/api/products/{product_id}/")

    @task(2)
    def update_product(self):
        if self.product_ids:
            product_id = random.choice(self.product_ids)
            updated_data = {"price": round(random.uniform(5.0, 500.0), 2)}
            self.client.patch(f"/api/products/{product_id}/", json=updated_data)

    @task(1)
    def delete_product(self):
        if self.product_ids:
            product_id = self.product_ids.pop(0)
            self.client.delete(f"/api/products/{product_id}/")

    @task(3)
    def create_order(self):
        if not self.user_ids: 
            self.create_user()
        if not self.product_ids:
            self.create_product()
        if not self.user_ids or not self.product_ids:
            return

        order_data = {
            # serializers esperam 'user' FK
            "user": random.choice(self.user_ids),
            # enviar items com 'product' (campo do OrderItemSerializer) e quantity
            "items": [
                {"product": random.choice(self.product_ids), "quantity": random.randint(1, 3)}
            ],
            "address": "Endereço de Entrega, 456"
        }
        response = self.client.post("/api/orders/", json=order_data)
        if response.status_code == 201:
            self.order_ids.append(response.json()["id"])
        else:
            print("CREATE_ORDER ERROR:", response.status_code, response.text)

    @task(10)
    def get_orders(self):
        self.client.get("/api/orders/")

    @task(5)
    def get_single_order(self):
        if not self.order_ids:
            return
        order_id = random.choice(self.order_ids)
        r = self.client.get(f"/api/orders/{order_id}/")
        if r.status_code == 404:
            print(f"[WARN] Order {order_id} não existe mais — removendo da lista")
            self.order_ids.remove(order_id)

    @task(2)
    def update_order(self):
        if self.order_ids:
            order_id = random.choice(self.order_ids)
            updated_data = {"address": "Novo Endereço, 789"}
            self.client.patch(f"/api/orders/{order_id}/", json=updated_data)

    @task(1)
    def delete_order(self):
        if self.order_ids:
            order_id = self.order_ids.pop(0)
            r = self.client.delete(f"/api/orders/{order_id}/")
            if r.status_code == 404:
                print(f"[INFO] Order {order_id} já não existia (404 ignorado)")

    @task(3)
    def create_order_item(self):
        if not self.order_ids:
            self.create_order()
        if not self.product_ids:
            self.create_product()
        if not self.order_ids or not self.product_ids:
            return

        order_id = random.choice(self.order_ids)
        product_id = random.choice(self.product_ids)
        order_item_data = {
            "order": order_id,
            "product": product_id,
            "quantity": random.randint(1, 5)
        }

        # try endpoints in order of likelihood
        endpoints = [
            f"/api/orders/{order_id}/items/",
            "/api/orders/items/",
            "/api/order-items/",
            "/api/order-items"
        ]
        for ep in endpoints:
            r = self.client.post(ep, json=order_item_data)
            # success
            if r.status_code in (200, 201):
                try:
                    self.order_item_ids.append(r.json().get("id"))
                except Exception:
                    pass
                return
            # if endpoint simply not found or method not allowed, try next
            if r.status_code in (404, 405):
                continue
            # unexpected error -> log and stop trying
            print("CREATE_ORDER_ITEM ERROR:", r.status_code, ep, r.text)
            return

        print("CREATE_ORDER_ITEM: no endpoint accepted the request")

    @task(10)
    def get_order_items(self):
        if not self.order_ids:
            return
        order_id = random.choice(self.order_ids)
        endpoints = [
            f"/api/orders/{order_id}/items/",
            "/api/orders/items/",
            "/api/order-items/",
            "/api/order-items"
        ]
        for ep in endpoints:
            r = self.client.get(ep)
            if r.status_code == 200:
                return
            if r.status_code == 404:
                continue
            # unexpected -> log
            print("GET_ORDER_ITEMS ERROR:", r.status_code, ep, r.text)
            return
        print("GET_ORDER_ITEMS: no endpoint returned 200")

    @task(5)
    def get_single_order_item(self):
        if self.order_item_ids:
            order_item_id = random.choice(self.order_item_ids)
            r = self.client.get(f"/api/orders/items/{order_item_id}/")
            if r.status_code == 404:
                print(f"[WARN] OrderItem {order_item_id} não encontrado — removendo da lista")
                self.order_item_ids.remove(order_item_id)

    @task(2)
    def update_order_item(self):
        if not self.order_item_ids:
            return
        order_item_id = random.choice(self.order_item_ids)
        # opcional: verificar existência via GET antes de PATCH
        r = self.client.get(f"/api/orders/items/{order_item_id}/")
        if r.status_code != 200:
            print("ORDER_ITEM not found before PATCH:", order_item_id, r.status_code)
            return
        r = self.client.patch(f"/api/orders/items/{order_item_id}/", json={"quantity": 5})
        if r.status_code != 200:
            print("PATCH_ORDER_ITEM FAILED:", order_item_id, r.status_code, r.text)

    @task(1)
    def delete_order_item(self):
        if self.order_item_ids:
            order_item_id = self.order_item_ids.pop(0)
            self.client.delete(f"/api/orders/items/{order_item_id}/")

    # --- Payment Endpoints --- #
    @task(3)
    def create_payment_method(self):
        if not self.user_ids:
            self.create_user()

        payment_method_data = {
            "user": random.choice(self.user_ids),
            "type": random.choice([c[0] for c in [('credit_card','Cartão de Crédito'), ('debit_card','Cartão de Débito'), ('paypal','PayPal'), ('pix','PIX'), ('bank_transfer','Transferência Bancária'), ('boleto','Boleto Bancário')]]),
            "name": f"Method {uuid.uuid4()}"
        }
        response = self.client.post("/api/payments/methods/", json=payment_method_data)
        if response.status_code == 201:
            self.payment_method_ids.append(response.json()["id"])

    @task(10)
    def get_payment_methods(self):
        self.client.get("/api/payments/methods/")

    @task(3)
    def create_payment(self):
        if not self.order_ids: 
            self.create_order()
        if not self.payment_method_ids: 
            self.create_payment_method()

        payment_data = {
            "order": random.choice(self.order_ids),
            "payment_method": random.choice(self.payment_method_ids),
            "amount": round(random.uniform(50.0, 2000.0), 2),
            "currency": "BRL",
            "status": random.choice(["pending", "completed", "failed"])
            # "status": random.choice([c[0] for c in [('pending','pending'),('completed','completed'),('failed','failed')]])
        }
        response = self.client.post("/api/payments/", json=payment_data)
        if response.status_code == 201:
            self.payment_ids.append(response.json()["id"])

    @task(10)
    def get_payments(self):
        self.client.get("/api/payments/")

    @task(5)
    def get_single_payment(self):
        if self.payment_ids:
            payment_id = random.choice(self.payment_ids)
            r = self.client.get(f"/api/payments/{payment_id}/")
            if r.status_code == 404:
                self.payment_ids.remove(payment_id)
    @task(2)
    def update_payment(self):
        if self.payment_ids:
            payment_id = random.choice(self.payment_ids)
            updated_data = {"status": random.choice(["pending", "completed", "failed"])}
            self.client.patch(f"/api/payments/{payment_id}/", json=updated_data)

    @task(1)
    def delete_payment(self):
        if self.payment_ids:
            payment_id = self.payment_ids.pop(0)
            self.client.delete(f"/api/payments/{payment_id}/")

