from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from technician.models import Patient
from .models import Consultation, Treatment
from .forms import ConsultationForm, TreatmentForm
from django.db.models import Q
from notifications.utils import create_notification
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from technician.models import Patient
from .models import Consultation
from .forms import ConsultationForm

def is_neurologist(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'NEUROLOGIST'

@login_required
def dashboard(request):
    # Get all critical patients
    critical_patients = Patient.objects.filter(
        Q(status='SUBMITTED') | Q(status='REVIEWED')
    ).filter(consultations__isnull=True)
    
    critical_patients = [p for p in critical_patients if p.is_critical()]
    
    # Add alert message and notification if there are critical patients
    if critical_patients:
        alert_message = f'There are {len(critical_patients)} critical patients requiring immediate attention!'
        messages.error(request, alert_message)  # Using error level for more prominent display
        
        # Create a critical notification
        send_notification(
            user=request.user,
            title='Critical Patients Alert',
            message=alert_message,
            notification_type='critical'
        )
    
    # Get active consultations
    active_consultations = Consultation.objects.filter(
        neurologist=request.user,
        status='IN_PROGRESS'
    ).select_related('patient')
    
    # Get completed consultations
    completed_consultations = Consultation.objects.filter(
        neurologist=request.user,
        status='COMPLETED'
    ).select_related('patient').order_by('-updated_at')[:5]
    
    context = {
        'critical_patients': critical_patients,
        'active_consultations': active_consultations,
        'completed_consultations': completed_consultations,
    }
    
    return render(request, 'neurologist/dashboard.html', context)

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get or create consultation
    consultation, created = Consultation.objects.get_or_create(
        patient=patient,
        defaults={'neurologist': request.user, 'status': 'IN_PROGRESS'}
    )
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            form.save()
            # Check if patient is critical
            if patient.is_critical():
                messages.error(request, f'⚠️ Consultation updated for critical patient {patient.first_name} {patient.last_name}. Immediate attention required!')
            else:
                messages.success(request, f'Consultation updated for patient {patient.first_name} {patient.last_name}.')
            return redirect('neurologist:dashboard')
    else:
        form = ConsultationForm(instance=consultation)
    
    # Get NIHSS scores
    nihss_scores = patient.nihss_scores.all().order_by('-timestamp')
    
    # Get vital signs
    vital_signs = patient.vital_signs_logs.all().order_by('-timestamp')
    
    # Get treatments
    treatments = consultation.treatments.all().order_by('-administration_time')
    
    context = {
        'patient': patient,
        'consultation': consultation,
        'form': form,
        'nihss_scores': nihss_scores,
        'vital_signs': vital_signs,
        'treatments': treatments,
        'treatment_form': TreatmentForm(),
    }
    
    return render(request, 'neurologist/patient_detail.html', context)

@login_required
def administer_treatment(request, consultation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    form = TreatmentForm(request.POST)
    if form.is_valid():
        treatment = consultation.administer_treatment(
            treatment_type=form.cleaned_data['treatment_type'],
            medication_name=form.cleaned_data['medication_name'],
            dosage=form.cleaned_data['dosage'],
            notes=form.cleaned_data['notes'],
            administered_by=request.user
        )
        
        # Create notification for technician
        create_notification(
            recipient=consultation.patient.technician,
            title='Treatment Administered',
            message=f'Treatment {treatment.get_treatment_type_display()} has been administered to patient {consultation.patient}',
            link=f'/technician/patient/{consultation.patient.id}/'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Treatment administered successfully',
            'treatment': {
                'type': treatment.get_treatment_type_display(),
                'medication': treatment.medication_name,
                'dosage': treatment.dosage,
                'time': treatment.administration_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
    
    return JsonResponse({'error': form.errors}, status=400)

@login_required
@user_passes_test(is_neurologist)
def dashboard(request):
    consultations = Consultation.objects.filter(neurologist=request.user).order_by('-created_at')[:10]
    
    # Only count submitted, reviewed, and diagnosed patients
    submitted_patients = Patient.objects.filter(status='SUBMITTED')
    reviewed_patients = Patient.objects.filter(status='REVIEWED')
    diagnosed_patients = Patient.objects.filter(status='DIAGNOSED')
    
    total_patients = submitted_patients.count() + reviewed_patients.count() + diagnosed_patients.count()
    pending_count = submitted_patients.count()
    in_progress_count = reviewed_patients.count()
    diagnosed_count = diagnosed_patients.count()

    context = {
        'consultations': consultations,
        'total_patients': total_patients,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'diagnosed_count': diagnosed_count,
    }
    return render(request, 'neurologist/dashboard.html', context)

@login_required
@user_passes_test(is_neurologist)
def case_history(request):
    status = request.GET.get('status')
    
    # Base queryset excluding NEW (draft) patients
    patients = Patient.objects.exclude(status='NEW')
    
    if status:
        patients = patients.filter(status=status)
    
    paginator = Paginator(patients.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status,
    }
    return render(request, 'neurologist/case_history.html', context)

@login_required
@user_passes_test(is_neurologist)
def start_consultation(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Check if patient is available for consultation
    if patient.status != 'SUBMITTED':
        messages.error(request, 'This patient is not available for consultation.')
        return redirect('neurologist:case_history')
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.neurologist = request.user
            consultation.save()
            
            # Update patient status
            patient.status = 'DIAGNOSED'
            patient.save()
            
            if patient.is_critical():
                messages.error(request, f'⚠️ Consultation completed for critical patient {patient.first_name} {patient.last_name}.')
            else:
                messages.success(request, f'Consultation completed for patient {patient.first_name} {patient.last_name}.')
            return redirect('neurologist:dashboard')
    else:
        form = ConsultationForm()
    
    context = {
        'form': form,
        'patient': patient,
        'title': f'New Consultation for {patient.first_name} {patient.last_name}'
    }
    return render(request, 'neurologist/consultation_form.html', context)

@login_required
@user_passes_test(is_neurologist)
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    context = {
        'consultation': consultation,
        'patient': consultation.patient,
        'title': f'Consultation Details for {consultation.patient.first_name} {consultation.patient.last_name}'
    }
    return render(request, 'neurologist/consultation_detail.html', context)

@login_required
@user_passes_test(is_neurologist)
def simulate_diagnosis(request, patient_id):
    """Simulate a diagnosis based on patient data"""
    from django.http import JsonResponse
    import random
    from datetime import date
    
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Calculate age from date of birth
    today = date.today()
    age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
    
    # Simple simulation logic based on patient data
    symptoms = patient.chief_complaint.lower()
    
    # Basic simulation logic
    if 'headache' in symptoms or 'confusion' in symptoms:
        if random.random() < 0.3:  # 30% chance
            diagnosis = 'HEMORRHAGIC'
            notes = "Patient presents with symptoms suggestive of hemorrhagic stroke. Immediate CT scan recommended."
        else:
            diagnosis = 'ISCHEMIC'
            notes = "Signs and symptoms consistent with ischemic stroke. Immediate neurological intervention required."
    elif 'weakness' in symptoms or 'numbness' in symptoms:
        if age > 60:
            diagnosis = 'ISCHEMIC'
            notes = "Given age and symptoms, likely ischemic stroke. Consider thrombolytic therapy if within window."
        else:
            diagnosis = 'TIA'
            notes = "Considering age and presentation, possible TIA. Further monitoring needed."
    else:
        diagnosis = 'OTHER'
        notes = "Symptoms non-specific. Further evaluation needed."
    
    # Generate treatment plan based on diagnosis
    if diagnosis == 'HEMORRHAGIC':
        treatment = "1. Immediate CT scan\n2. Blood pressure management\n3. Neurosurgery consult\n4. ICU admission"
        medications = ["Antihypertensives", "Osmotic agents", "Anticonvulsants"]
    elif diagnosis == 'ISCHEMIC':
        treatment = "1. CT/MRI imaging\n2. Consider tPA if within window\n3. Stroke unit admission\n4. Early rehabilitation"
        medications = ["Aspirin", "Statins", "Antihypertensives"]
    elif diagnosis == 'TIA':
        treatment = "1. Urgent carotid imaging\n2. Cardiac evaluation\n3. Risk factor modification\n4. Close follow-up"
        medications = ["Antiplatelet agents", "Statins", "Blood pressure medication"]
    else:
        treatment = "1. Further diagnostic workup\n2. Neurological monitoring\n3. Symptom management"
        medications = ["To be determined based on findings"]
    
    return JsonResponse({
        'diagnosis': diagnosis,
        'notes': notes,
        'treatment_plan': treatment,
        'medications': medications,
        'age': age  # Include age in response for reference
    })
