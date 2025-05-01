from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Patient, VitalSignsLog
from .forms import PatientForm, VitalSignsLogForm
from accounts.decorators import is_technician

# Create your views here.

@login_required
@is_technician
def dashboard(request):
    patients = Patient.objects.filter(technician=request.user).order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'new_count': patients.filter(status='NEW').count(),
        'submitted_count': patients.filter(status='SUBMITTED').count(),
        'diagnosed_count': patients.filter(status='DIAGNOSED').count(),
    }
    return render(request, 'technician/dashboard.html', context)

@login_required
@is_technician
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.technician = request.user
            
            # Set status based on action
            action = request.POST.get('action', 'draft')
            if action == 'submit':
                patient.status = 'SUBMITTED'
                success_message = 'Patient record created and submitted for neurologist review.'
            else:
                patient.status = 'NEW'
                success_message = 'Patient record saved as draft.'
            
            patient.save()
            messages.success(request, success_message)
            return redirect('technician:patient_detail', pk=patient.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientForm()
    
    return render(request, 'technician/patient_form.html', {'form': form, 'title': 'New Patient'})

@login_required
@is_technician
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk, technician=request.user)
    
    # Don't allow editing if patient is already under review or diagnosed
    if patient.status not in ['NEW', 'SUBMITTED']:
        messages.error(request, 'Cannot edit patient details once under review or diagnosed.')
        return redirect('technician:patient_detail', pk=patient.pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            
            # Set status based on action
            action = request.POST.get('action', 'draft')
            if action == 'submit':
                patient.status = 'SUBMITTED'
                success_message = 'Patient record updated and submitted for neurologist review.'
            else:
                patient.status = 'NEW'
                success_message = 'Patient record saved as draft.'
            
            patient.save()
            messages.success(request, success_message)
            return redirect('technician:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'technician/patient_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Edit Patient'
    })

@login_required
@is_technician
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk, technician=request.user)
    vital_signs_logs = patient.vital_signs_logs.order_by('-created_at')[:5]
    
    if request.method == 'POST':
        form = VitalSignsLogForm(request.POST)
        if form.is_valid():
            vital_signs = form.save(commit=False)
            vital_signs.patient = patient
            vital_signs.save()
            messages.success(request, 'Vital signs recorded successfully.')
            return redirect('technician:patient_detail', pk=patient.pk)
    else:
        form = VitalSignsLogForm()
    
    return render(request, 'technician/patient_detail.html', {
        'patient': patient,
        'vital_signs_logs': vital_signs_logs,
        'form': form,
    })

@login_required
@is_technician
def patient_list(request):
    patients = Patient.objects.filter(technician=request.user).order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'technician/patient_list.html', {'page_obj': page_obj})
