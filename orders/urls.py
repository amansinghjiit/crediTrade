from django.urls import path
from . import views

urlpatterns = [
    path('delivery-form/', views.delivery_form_view, name='delivery_form'),
    path('pending/', views.pending_orders_view, name='pending'),
    path('delivered/', views.delivered_orders_view, name='delivered'),
    path('pending/delete/<int:id>/', views.delete_entry, name='delete_entry'),
    path('pending/edit/<int:id>/', views.edit_entry, name='edit_entry'),
    path('upload_invoice/', views.upload_invoice, name='upload_invoice'),
    path('remove_invoice/', views.remove_invoice, name='remove_invoice'),
    path('view_invoice/<int:order_id>/', views.view_invoice, name='view_invoice'),
    path('export_pending_orders_csv/', views.export_pending_orders_csv, name='export_pending_orders_csv'),
    path('export_delivered_orders_csv/', views.export_delivered_orders_csv, name='export_delivered_orders_csv'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('payments-dashboard/', views.payments_dashboard, name='payments_dashboard'),
    path('user-payment-details/<int:user_id>/', views.user_payment_details, name='user_payment_details'),
    path('make-payment/<int:user_id>/', views.make_payment, name='make_payment'),
    path('transaction-history/<int:user_profile_id>/', views.transaction_history, name='transaction_history'),
    path('export-payment-details/', views.export_payment_details, name='export_payment_details'),
]
