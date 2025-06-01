import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_handle_serialization_json(client):
    response = client.get("/serialize/json")
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_process_payment_creditcard(client):
    response = client.post("/pay/creditcard", json={"amount": 100})
    assert response.status_code == 200
    assert response.json["result"]["method"] == "creditcard"

def test_checkout(client):
    response = client.post("/checkout", json={
        "product_id": 1,
        "zip_code": "12345",
        "subtotal": 100.0
    })
    assert response.status_code == 200