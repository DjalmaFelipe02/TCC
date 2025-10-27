from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Category, Product
class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(name='U', email='u@example.com', address='Rua U, 1')
        c = Category.objects.create(name='Books')
        self.p = Product.objects.create(name='Book A', price='20.00', stock=10, category=c)
    def test_create(self):
        payload = {'user': str(self.user.id), 'address': self.user.address, 'items': [{'product': str(self.p.id), 'quantity':2}]}
        res = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(res.status_code, 201)
