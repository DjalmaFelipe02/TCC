from django.test import TestCase
from rest_framework.test import APIClient
from .models import User
class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create(name='Alice', email='alice@example.com', phone='111', birth_date='1990-01-01', address='Rua A, 1')
    def test_list(self):
        r = self.client.get('/api/users/'); self.assertEqual(r.status_code,200)
    def test_create(self):
        payload={'name':'Bob','email':'bob@example.com','phone':'222','birth_date':'1992-02-02','address':'Rua B, 2'}
        r = self.client.post('/api/users/', payload, format='json'); self.assertEqual(r.status_code,201)
