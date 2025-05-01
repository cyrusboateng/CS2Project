from django import forms
from .models import Consultation

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'diagnosis_notes', 'treatment_plan', 'follow_up_notes', 'status']
        widgets = {
            'diagnosis_notes': forms.Textarea(attrs={'rows': 4}),
            'treatment_plan': forms.Textarea(attrs={'rows': 4}),
            'follow_up_notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Add help text for diagnosis notes
        self.fields['diagnosis_notes'].help_text = 'Include relevant findings and reasoning for diagnosis'
        self.fields['treatment_plan'].help_text = 'Specify medications, dosages, and any immediate interventions needed'
