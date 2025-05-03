# test_facade.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_checkout_success():
    response = client.post("/checkout", json={
        "product_id": "123",
        "zip_code": "00000-000",
        "subtotal": 100.0
    })
    assert response.status_code == 200
    assert "total" in response.json()