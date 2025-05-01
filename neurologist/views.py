from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from technician.models import Patient
from .models import Consultation
from .forms import ConsultationForm

def is_neurologist(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'NEUROLOGIST'

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
            
            messages.success(request, 'Consultation completed successfully.')
            return redirect('neurologist:consultation_detail', pk=consultation.pk)
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
