from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_serialize_json():
    response = client.get("/serialize/json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_process_payment_creditcard():
    response = client.post("/pay/creditcard", json={"amount": 100, "currency": "USD"})
    assert response.status_code == 200
    assert response.json()["result"]["method"] == "creditcard"

def test_checkout():
    response = client.post("/checkout", json={
        "product_id": "1",
        "zip_code": "12345",
        "subtotal": 100.0
    })
    assert response.status_code == 200