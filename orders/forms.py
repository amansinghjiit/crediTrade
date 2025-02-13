from django import forms
from .models import PendingOrder
from .models_fetching import get_models

class PendingOrderForm(forms.ModelForm):
    model = forms.ChoiceField(choices=[], required=False, widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_choices = [('', 'Model')] + [(m, m) for m in get_models()]
        if self.instance and self.instance.pk and self.instance.model:
            if self.instance.model not in dict(model_choices):
                model_choices.append((self.instance.model, self.instance.model))
        self.fields['model'].choices = model_choices

    class Meta:
        model = PendingOrder
        fields = ['name', 'tracking', 'otp', 'obd', 'model', 'pin']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'tracking': forms.TextInput(attrs={'placeholder': 'Tracking'}),
            'otp': forms.TextInput(attrs={'placeholder': 'OTP'}),
            'obd': forms.TextInput(attrs={'placeholder': 'Last 4 digits of phone no.'}),
            'pin': forms.Select(attrs={'class': 'form-control'}),
        }
