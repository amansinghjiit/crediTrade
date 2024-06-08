from django import forms
from .models import PendingOrder

class PendingOrderForm(forms.ModelForm):
    class Meta:
        model = PendingOrder
        fields = ['name', 'tracking', 'otp', 'obd', 'model', 'pin']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'tracking': forms.TextInput(attrs={'placeholder': 'Tracking'}),
            'otp': forms.TextInput(attrs={'placeholder': 'OTP'}),
            'obd': forms.TextInput(attrs={'placeholder': 'Last 4 digits of phone no.'}),
            'model': forms.TextInput(attrs={'placeholder': 'Model'}),
            'pin': forms.Select(attrs={'class': 'form-control'}),
        }
