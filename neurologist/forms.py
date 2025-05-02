from django import forms
from .models import Consultation, Treatment

class ConsultationForm(forms.ModelForm):
    diagnosis = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    treatment_plan = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    medications = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    follow_up_instructions = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'treatment_plan', 'medications', 'follow_up_instructions']
        
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        diagnosis = cleaned_data.get('diagnosis')
        treatment_plan = cleaned_data.get('treatment_plan')
        
        if status == 'COMPLETED':
            if not diagnosis:
                raise forms.ValidationError("Diagnosis is required to complete the consultation.")
            if not treatment_plan:
                raise forms.ValidationError("Treatment plan is required to complete the consultation.")

class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = ['treatment_type', 'medication_name', 'dosage', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['treatment_type'].widget.attrs['class'] = 'form-control form-select'
