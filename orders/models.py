from django.db import models
from django.utils import timezone
from accounts.models import UserProfile
from .utils import validate_size
from .models_fetching import get_models

class PendingOrder(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    tracking = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    obd = models.CharField(max_length=4, help_text='Last 4 digits of phone number')
    model = models.CharField(max_length=50, blank=True, null=True)
        
    STATUS_CHOICES = [
        ('Delivered', 'Delivered'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', editable=True)
    
    PIN_CHOICES = [
        ('', 'Pin'),
        ('Jagdamba 766015', 'Jagdamba 766015'),
        ('Delhi 110091', 'Delhi 110091'),
        ('416118 / 416115' , '416118 / 416115'),
        ('Wholesale 492001', 'Wholesale 492001'),
        ('Pansari 767001', 'Pansari 767001'),
        ('228001 / 228159','228001 / 228159'),
        ('226020 / 226021', '226020 / 226021'),
        ('225001','225001'),
        ('Other', 'Other'),
    ]
    pin = models.CharField(max_length=20, choices=PIN_CHOICES, default='')

class DeliveredOrder(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    name = models.CharField(max_length=25)
    model = models.CharField(max_length=50)
    pin = models.CharField(max_length=20)
    invoice = models.FileField(upload_to='invoices/', validators=[validate_size], blank=True)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Transaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    TRANSACTION_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    description = models.CharField(max_length=30)
    auto_created = models.BooleanField(default=False, editable=True)