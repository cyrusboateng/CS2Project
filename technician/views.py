from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Patient, VitalSignsLog
from .forms import PatientForm, VitalSignsLogForm

# Create your views here.

@login_required
def dashboard(request):
    patients = Patient.objects.filter(created_by=request.user).order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'draft_count': patients.filter(status='DRAFT').count(),
        'submitted_count': patients.filter(status='SUBMITTED').count(),
        'diagnosed_count': patients.filter(status='DIAGNOSED').count(),
    }
    return render(request, 'technician/dashboard.html', context)

@login_required
def patient_new(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()
            messages.success(request, 'Patient record created successfully.')
            return redirect('technician:patient_detail', pk=patient.pk)
    else:
        form = PatientForm()
    
    return render(request, 'technician/patient_form.html', {'form': form, 'title': 'New Patient'})

@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save()
            messages.success(request, 'Patient record updated successfully.')
            return redirect('technician:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'technician/patient_form.html', {
        'form': form,
        'title': f'Edit Patient: {patient}',
        'patient': patient
    })

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk, created_by=request.user)
    vital_signs_form = VitalSignsLogForm()
    vital_signs_logs = patient.vital_signs_logs.all()[:5]
    
    if request.method == 'POST':
        if 'submit_case' in request.POST and patient.status == 'DRAFT':
            patient.status = 'SUBMITTED'
            patient.save()
            messages.success(request, 'Case submitted successfully for review.')
            return redirect('technician:patient_detail', pk=pk)
            
        vital_signs_form = VitalSignsLogForm(request.POST)
        if vital_signs_form.is_valid():
            vital_signs = vital_signs_form.save(commit=False)
            vital_signs.patient = patient
            vital_signs.save()
            messages.success(request, 'Vital signs recorded successfully.')
            return redirect('technician:patient_detail', pk=pk)
    
    return render(request, 'technician/patient_detail.html', {
        'patient': patient,
        'vital_signs_form': vital_signs_form,
        'vital_signs_logs': vital_signs_logs,
    })

@login_required
def patient_list(request):
    status = request.GET.get('status', '')
    if status:
        patients = Patient.objects.filter(created_by=request.user, status=status)
    else:
        patients = Patient.objects.filter(created_by=request.user)
    
    paginator = Paginator(patients.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'technician/patient_list.html', {
        'page_obj': page_obj,
        'status': status,
    })
