from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    whatsapp_number = models.CharField(max_length=10, blank=True, null=True)
    phonepe_name = models.CharField(max_length=50, blank=True, null=True)
    phonepe_number = models.CharField(max_length=10, blank=True, null=True)
    account_holder_name = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    last_login_ip = models.CharField(max_length=45, blank=True, null=True) 

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
