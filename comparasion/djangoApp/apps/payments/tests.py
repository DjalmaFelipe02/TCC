from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Category, Product
from apps.orders.models import Order
class PaymentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(name='PayUser', email='pay@example.com', address='Rua Pay, 1')
        c = Category.objects.create(name='Gadgets'); p = Product.objects.create(name='G', price='15.00', stock=5, category=c)
        self.order = Order.objects.create(user=self.user, address=self.user.address, total_amount=15.00)
    def test_create(self):
        rc = self.client.post('/api/payments/methods/', {'user': str(self.user.id),'type':'pix','name':'PIX-1'}, format='json'); self.assertIn(rc.status_code,(200,201))
        pm_id = rc.json().get('id') if rc.status_code==201 else None
        rp = self.client.post('/api/payments/', {'order': str(self.order.id),'payment_method': pm_id,'amount':'15.00','status':'pending'}, format='json'); self.assertEqual(rp.status_code,201)
