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
    total_patients = Patient.objects.all().count()  # All patients in the system
    pending_count = Patient.objects.filter(status='SUBMITTED').count()  # Patients waiting for review
    in_progress_count = Patient.objects.filter(status='REVIEWED').count()  # Patients under review
    diagnosed_count = Patient.objects.filter(status='DIAGNOSED').count()  # Diagnosed patients

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
    patients = Patient.objects.all()
    
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
