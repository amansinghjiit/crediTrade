from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'whatsapp_number', 'phonepe_name', 'phonepe_number','amount_due','last_login_ip')
    search_fields = ('name', 'whatsapp_number')

admin.site.register(UserProfile, UserProfileAdmin)
