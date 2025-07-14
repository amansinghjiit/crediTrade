from django.db import models
from django.contrib.auth.models import User
from encrypted_model_fields.fields import EncryptedCharField

BANK_CHOICES = [
    ('SBI', 'SBI'),
    ('HDFC', 'HDFC'),
    ('ICICI', 'ICICI'),
    ('AXIS', 'AXIS'),
    ('KOTAK', 'KOTAK'),
    ('BOB', 'BOB'),
    ('IDFC', 'IDFC'),
    ('YES', 'YES'),
    ('RBL', 'RBL'),
    ('AMEX', 'AMEX'),
    ('PNB', 'PNB'),
    ('AU', 'AU'),
    ('ONECARD', 'ONECARD'),
    ('DBS', 'DBS'),
    ('INDUSIND', 'INDUSIND'),
    ('UNION', 'UNION'),
    ('FEDERAL', 'FEDERAL'),
    ('HSBC', 'HSBC'),
    ('CANARA', 'CANARA'),
    ('BOI', 'BOI'),
    ('INDIAN', 'INDIAN'),
    ('OTHER', 'OTHER'),
]

class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank = models.CharField(max_length=20, choices=BANK_CHOICES)
    card_number = EncryptedCharField(max_length=50)
    expiry = EncryptedCharField(max_length=50)
    cvv = EncryptedCharField(max_length=50)
    card_variant = models.CharField(max_length=50, blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.bank}"

