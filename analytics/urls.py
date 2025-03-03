from django.urls import path
from .views import order_insights,update_return_amount,ledger

urlpatterns = [
    path('order-insights/', order_insights, name='order_insights'),
    path("update-return-amount/", update_return_amount, name="update_return_amount"),
    path('ledger/', ledger, name='ledger'),
]
