from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from technician.models import Patient
from .models import Consultation
from .forms import ConsultationForm

def neurologist_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'NEUROLOGIST':
            raise PermissionDenied("You must be a neurologist to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@neurologist_required
def dashboard(request):
    # Show all consultations by this neurologist
    consultations = Consultation.objects.filter(neurologist=request.user).order_by('-created_at')
    
    # Count all patients by status
    total_patients = Patient.objects.count()
    pending_cases = Patient.objects.filter(status='SUBMITTED').count()
    diagnosed_cases = Patient.objects.filter(status='DIAGNOSED').count()
    
    context = {
        'consultations': consultations[:5],
        'total_patients': total_patients,
        'pending_count': pending_cases,
        'diagnosed_count': diagnosed_cases,
        'in_progress_count': consultations.filter(status='IN_PROGRESS').count(),
        'completed_count': consultations.filter(status='COMPLETED').count(),
    }
    return render(request, 'neurologist/dashboard.html', context)

@login_required
@neurologist_required
def pending_cases(request):
    # Show all patients that need review (status=SUBMITTED)
    patients = Patient.objects.filter(status='SUBMITTED').order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'neurologist/pending_cases.html', {
        'page_obj': page_obj,
    })

@login_required
@neurologist_required
def case_history(request):
    # Show all patients, regardless of status
    status_filter = request.GET.get('status', '')
    patients = Patient.objects.all().order_by('-created_at')
    
    if status_filter:
        patients = patients.filter(status=status_filter)
    
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'neurologist/case_history.html', {
        'page_obj': page_obj,
        'current_status': status_filter,
        'status_choices': Patient.STATUS_CHOICES,
    })

@login_required
@neurologist_required
def start_consultation(request, patient_id):
    # Allow starting consultation for any submitted patient
    patient = get_object_or_404(Patient, id=patient_id, status='SUBMITTED')
    
    # Check if consultation already exists
    consultation = Consultation.objects.filter(patient=patient).first()
    if consultation:
        messages.warning(request, 'This case is already under review.')
        return redirect('neurologist:consultation_detail', pk=consultation.pk)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.neurologist = request.user
            consultation.save()
            
            # Update patient status
            patient.status = 'REVIEWED'
            patient.save()
            
            messages.success(request, 'Consultation started successfully.')
            return redirect('neurologist:consultation_detail', pk=consultation.pk)
    else:
        form = ConsultationForm()
    
    return render(request, 'neurologist/consultation_form.html', {
        'form': form,
        'patient': patient,
    })

@login_required
@neurologist_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            consultation = form.save()
            
            # If consultation is completed, update patient status
            if consultation.status == 'COMPLETED':
                consultation.patient.status = 'DIAGNOSED'
                consultation.patient.save()
            
            messages.success(request, 'Consultation updated successfully.')
            return redirect('neurologist:consultation_detail', pk=consultation.pk)
    else:
        form = ConsultationForm(instance=consultation)
    
    return render(request, 'neurologist/consultation_detail.html', {
        'form': form,
        'consultation': consultation,
    })
