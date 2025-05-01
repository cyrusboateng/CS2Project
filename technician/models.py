from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

# Create your models here.

class Patient(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('SUBMITTED', 'Submitted for Review'),
        ('REVIEWED', 'Under Review'),
        ('DIAGNOSED', 'Diagnosed'),
        ('DISCHARGED', 'Discharged'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Demographics
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    
    # Medical Information
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    
    # Initial Vital Signs
    blood_pressure_systolic = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(300)])
    blood_pressure_diastolic = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(200)])
    heart_rate = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(300)])
    respiratory_rate = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    oxygen_saturation = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    glasgow_coma_scale = models.IntegerField(validators=[MinValueValidator(3), MaxValueValidator(15)])
    
    # Chief Complaint and Notes
    chief_complaint = models.TextField()
    notes = models.TextField(blank=True)
    nihss = models.TextField(blank=True, help_text="National Institutes of Health Stroke Scale score and details")
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    technician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('technician:patient_detail', kwargs={'pk': self.pk})
    
    def is_critical(self):
        """Check if patient's condition is critical based on vital signs and NIHSS score."""
        # Check vital signs against critical thresholds
        if (
            self.blood_pressure_systolic > 220 or self.blood_pressure_systolic < 90 or
            self.blood_pressure_diastolic > 120 or self.blood_pressure_diastolic < 60 or
            self.heart_rate > 130 or self.heart_rate < 50 or
            self.respiratory_rate > 30 or self.respiratory_rate < 10 or
            self.temperature > 39.5 or self.temperature < 35.0 or
            self.oxygen_saturation < 90 or
            self.glasgow_coma_scale < 13
        ):
            return True
        
        # Check latest vital signs log if available
        latest_vitals = self.vital_signs_logs.first()
        if latest_vitals and (
            latest_vitals.blood_pressure_systolic > 220 or latest_vitals.blood_pressure_systolic < 90 or
            latest_vitals.blood_pressure_diastolic > 120 or latest_vitals.blood_pressure_diastolic < 60 or
            latest_vitals.heart_rate > 130 or latest_vitals.heart_rate < 50 or
            latest_vitals.respiratory_rate > 30 or latest_vitals.respiratory_rate < 10 or
            latest_vitals.temperature > 39.5 or latest_vitals.temperature < 35.0 or
            latest_vitals.oxygen_saturation < 90 or
            latest_vitals.glasgow_coma_scale < 13
        ):
            return True
        
        return False

class VitalSignsLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs_logs')
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    oxygen_saturation = models.IntegerField()
    glasgow_coma_scale = models.IntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Vitals for {self.patient} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class CTScan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ct_scans')
    image = models.ImageField(upload_to='ct_scans/%Y/%m/%d/')
    description = models.TextField(blank=True, help_text="Optional description or notes about the CT scan")
    date_taken = models.DateField(help_text="Date the CT scan was taken")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_taken']
    
    def __str__(self):
        return f"CT Scan for {self.patient} taken on {self.date_taken}"
