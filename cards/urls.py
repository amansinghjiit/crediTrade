from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_cards, name='my_cards'),
    path('add/', views.add_card, name='add_card'),
    path('delete/<int:card_id>/', views.delete_card, name='delete_card'),
]
