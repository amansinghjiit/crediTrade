import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from .signals import handle_pending_order_status
from .models import PendingOrder, DeliveredOrder, Transaction

class GetUserProfileNameMixin:
    def get_user_profile_name(self, obj):
        return obj.user_profile.name

    get_user_profile_name.short_description = 'User'

class ExportCSVActionMixin:
    def export_orders_csv(self, request, queryset):
        fields = [field for field in self.list_display if field != 'get_user_profile_name']
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.model_name}.csv"'
        writer = csv.writer(response)
        writer.writerow(fields)
        for obj in queryset:
            writer.writerow([getattr(obj, field, '') for field in fields])
        return response

    export_orders_csv.short_description = "Export as CSV"

class PendingOrderAdmin(GetUserProfileNameMixin, ExportCSVActionMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name', 'name', 'tracking', 'model')
    list_per_page = 100
    list_display = (
        'get_user_profile_name', 'name', 'tracking', 'otp', 'obd', 'model', 'pin'
    )
    list_filter = ('pin',)
    actions = ['mark_as_delivered', 'export_orders_csv']
    csv_export_url_name = 'export_pending_orders_csv'

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')
        for order in queryset:
            handle_pending_order_status(sender=PendingOrder, instance=order)

    mark_as_delivered.short_description = "Mark as Delivered"

class DeliveredOrderAdmin(GetUserProfileNameMixin, ExportCSVActionMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name', 'name', 'model')
    list_per_page = 50
    list_display = (
        'get_user_profile_name', 'date', 'name','tracking','model', 'pin', 'return_amount'
    )
    list_filter = ('date', 'pin')
    list_editable = ('return_amount',)
    actions = ['export_orders_csv']
    csv_export_url_name = 'export_delivered_orders_csv'
class TransactionAdmin(GetUserProfileNameMixin, admin.ModelAdmin):
    search_fields = ('user_profile__name',)
    list_per_page = 100
    list_display = ('date', 'get_user_profile_name', 'transaction_type', 'description', 'amount')
    list_filter = ('date', 'transaction_type')

admin.site.register(PendingOrder, PendingOrderAdmin)
admin.site.register(DeliveredOrder, DeliveredOrderAdmin)
admin.site.register(Transaction, TransactionAdmin)
