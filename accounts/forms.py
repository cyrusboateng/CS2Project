from django import forms
from .models import UserProfile

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
