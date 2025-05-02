from django.db import models
from django.contrib.auth.models import User
from technician.models import Patient

# Create your models here.

class Treatment(models.Model):
    TREATMENT_CHOICES = [
        ('TPA', 'Tissue Plasminogen Activator (tPA)'),
        ('ANTICOAGULANT', 'Anticoagulant Therapy'),
        ('ANTIPLATELET', 'Antiplatelet Therapy'),
        ('ANTIHYPERTENSIVE', 'Antihypertensive Medication'),
        ('OTHER', 'Other Treatment')
    ]
    
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='treatments')
    treatment_type = models.CharField(max_length=20, choices=TREATMENT_CHOICES)
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    administration_time = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    administered_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.get_treatment_type_display()} - {self.medication_name} ({self.dosage})'

class Consultation(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    DIAGNOSIS_CHOICES = [
        ('ISCHEMIC', 'Ischemic Stroke'),
        ('HEMORRHAGIC', 'Hemorrhagic Stroke'),
        ('TIA', 'Transient Ischemic Attack'),
        ('OTHER', 'Other'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    neurologist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    diagnosis = models.CharField(max_length=20, choices=DIAGNOSIS_CHOICES, null=True, blank=True)
    diagnosis_notes = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    medications = models.TextField(blank=True, help_text="List prescribed medications and dosages")
    follow_up_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Consultation for {self.patient} by Dr. {self.neurologist.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and self._state.adding is False:
            self.patient.status = 'DIAGNOSED'
            self.patient.save()
        super().save(*args, **kwargs)
    
    def administer_treatment(self, treatment_type, medication_name, dosage, notes, administered_by):
        """Administer treatment to the patient"""
        treatment = Treatment.objects.create(
            consultation=self,
            treatment_type=treatment_type,
            medication_name=medication_name,
            dosage=dosage,
            notes=notes,
            administered_by=administered_by
        )
        return treatment
