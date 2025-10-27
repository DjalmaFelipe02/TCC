from django.test import TestCase
from rest_framework.test import APIClient
from .models import Category, Product
class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        c = Category.objects.create(name='Electronics', description='Electronics')
        Product.objects.create(name='Mouse', description='Optical', price='10.00', stock=5, category=c)
    def test_list(self):
        r = self.client.get('/api/products/'); self.assertEqual(r.status_code,200)
