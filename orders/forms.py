from django import forms
from .models import PendingOrder
from .models_fetching import get_models

class PendingOrderForm(forms.ModelForm):
    class Meta:
        model = PendingOrder
        fields = ['name', 'tracking', 'otp', 'obd', 'model', 'pin']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'tracking': forms.TextInput(attrs={'placeholder': 'Tracking'}),
            'otp': forms.TextInput(attrs={'placeholder': 'OTP'}),
            'obd': forms.TextInput(attrs={'placeholder': 'Last 4 digits of phone no.'}),
            'model': forms.Select(attrs={'class': 'form-control'}),
            'pin': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_choices = [('', 'Model')] + [(model, model) for model in get_models()]
        self.fields['model'].choices = model_choices
