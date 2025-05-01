from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import UserProfile

class UserCreationForm(BaseUserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class UserProfileForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('TECHNICIAN', 'Technician'),
        ('NEUROLOGIST', 'Neurologist'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )

    class Meta:
        model = UserProfile
        fields = ['role']
