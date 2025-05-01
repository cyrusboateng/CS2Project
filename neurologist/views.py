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
    consultations = Consultation.objects.filter(neurologist=request.user).order_by('-created_at')
    pending_cases = Patient.objects.filter(status='SUBMITTED').count()
    
    context = {
        'consultations': consultations[:5],
        'pending_count': pending_cases,
        'in_progress_count': consultations.filter(status='IN_PROGRESS').count(),
        'completed_count': consultations.filter(status='COMPLETED').count(),
    }
    return render(request, 'neurologist/dashboard.html', context)

@login_required
@neurologist_required
def pending_cases(request):
    patients = Patient.objects.filter(status='SUBMITTED').order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'neurologist/pending_cases.html', {
        'page_obj': page_obj,
    })

@login_required
@neurologist_required
def start_consultation(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id, status='SUBMITTED')
    
    # Check if consultation already exists
    consultation = Consultation.objects.filter(patient=patient).first()
    if consultation:
        messages.warning(request, 'This case is already under review.')
        return redirect('neurologist:consultation_detail', pk=consultation.pk)
    
    # Create new consultation
    consultation = Consultation.objects.create(
        patient=patient,
        neurologist=request.user
    )
    patient.status = 'REVIEWED'
    patient.save()
    
    messages.success(request, 'Consultation started successfully.')
    return redirect('neurologist:consultation_detail', pk=consultation.pk)

@login_required
@neurologist_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    
    # Ensure the neurologist can only view their own consultations
    if consultation.neurologist != request.user:
        raise PermissionDenied("You can only view your own consultations.")
    
    patient = consultation.patient
    vital_signs_logs = patient.vital_signs_logs.all()[:5]
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consultation updated successfully.')
            return redirect('neurologist:consultation_detail', pk=pk)
    else:
        form = ConsultationForm(instance=consultation)
    
    return render(request, 'neurologist/consultation_detail.html', {
        'consultation': consultation,
        'patient': patient,
        'vital_signs_logs': vital_signs_logs,
        'form': form,
    })

@login_required
@neurologist_required
def case_history(request):
    consultations = Consultation.objects.filter(neurologist=request.user)
    status = request.GET.get('status')
    if status:
        consultations = consultations.filter(status=status)
    
    paginator = Paginator(consultations.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'neurologist/case_history.html', {
        'page_obj': page_obj,
        'status': status,
    })
