from fastapi.testclient import TestClient
from main import app
from database import Base, engine
client = TestClient(app)

def setup_module(module):
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)

def test_create_user():
    res = client.post('/users/', json={'name':'A','email':'a@example.com'}); assert res.status_code==201
