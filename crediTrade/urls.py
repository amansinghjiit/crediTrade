from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('analytics/', include('analytics.urls')),
    path('cards/', include('cards.urls')),
]