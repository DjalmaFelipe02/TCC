from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def serialize_json(self):
        self.client.get("/serialize/json")

    @task
    def process_payment(self):
        self.client.post("/pay/creditcard", json={"amount": 100, "currency": "USD"})

    @task
    def checkout(self):
        self.client.post("/checkout", json={
            "product_id": "1",
            "zip_code": "12345",
            "subtotal": 100.0
        })