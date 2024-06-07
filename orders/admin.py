from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .signals import handle_pending_order_status
from .models import PendingOrder, DeliveredOrder, Transaction

class GetUserProfileNameMixin:
    def get_user_profile_name(self, obj):
        return obj.user_profile.name

    get_user_profile_name.short_description = 'User'

class ExportCSVActionMixin:
    def export_orders_csv(self, request, queryset):
        url = reverse(self.csv_export_url_name)
        return HttpResponseRedirect(url)
    
    export_orders_csv.short_description = "Export as CSV"

class PendingOrderAdmin(GetUserProfileNameMixin, ExportCSVActionMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name', 'name', 'tracking', 'model')
    list_per_page = 100
    list_display = (
        'get_user_profile_name', 'name', 'tracking', 'otp', 'obd', 'model', 'shop')
    list_filter = ('model', 'shop')
    actions = ['mark_as_delivered', 'export_orders_csv']
    csv_export_url_name = 'export_pending_orders_csv'

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')
        for order in queryset:
            handle_pending_order_status(sender=PendingOrder, instance=order)

    mark_as_delivered.short_description = "Mark as Delivered"

class DeliveredOrderAdmin(GetUserProfileNameMixin, ExportCSVActionMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name', 'name', 'model')
    list_per_page = 100
    list_display = (
        'get_user_profile_name', 'date', 'name', 'model', 'shop', 'get_invoice_status', 'return_amount'
    )
    list_filter = ('date', 'shop')
    list_editable = ('return_amount',)
    actions = ['export_orders_csv']
    csv_export_url_name = 'export_delivered_orders_csv'

    def get_invoice_status(self, obj):
        return '1' if obj.invoice else '0'

    get_invoice_status.short_description = 'Invoice'

class TransactionAdmin(GetUserProfileNameMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name',)
    list_per_page = 100
    list_display = ('date', 'get_user_profile_name', 'transaction_type', 'description', 'amount')
    list_filter = ('date', 'transaction_type')

admin.site.register(PendingOrder, PendingOrderAdmin)
admin.site.register(DeliveredOrder, DeliveredOrderAdmin)
admin.site.register(Transaction, TransactionAdmin)
