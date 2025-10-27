from rest_framework.routers import DefaultRouter
from .views import PaymentMethodViewSet, PaymentViewSet
router = DefaultRouter(); router.register('methods', PaymentMethodViewSet, basename='paymentmethod'); router.register('', PaymentViewSet, basename='payment')
urlpatterns = router.urls
