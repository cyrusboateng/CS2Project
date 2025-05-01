from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import Patient, VitalSignsLog, CTScan
from .forms import PatientForm, VitalSignsLogForm
from accounts.decorators import is_technician
from neurologist.models import Consultation
from notifications.utils import send_notification

# Create your views here.

@login_required
@user_passes_test(is_technician)
def dashboard(request):
    # Get all patients for this technician
    patients = Patient.objects.filter(technician=request.user).order_by('-created_at')
    
    # Get counts for different statuses
    total_patients = patients.count()
    draft_count = patients.filter(status='NEW').count()
    submitted_count = patients.filter(status='SUBMITTED').count()
    diagnosed_count = patients.filter(status='DIAGNOSED').count()
    
    # Get recent patients (all statuses)
    recent_patients = patients[:10]  # Get 10 most recent patients
    
    context = {
        'recent_patients': recent_patients,
        'total_patients': total_patients,
        'draft_count': draft_count,
        'submitted_count': submitted_count,
        'diagnosed_count': diagnosed_count,
    }
    return render(request, 'technician/dashboard.html', context)

@login_required
@user_passes_test(is_technician)
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
            
            # Send notification to neurologists if submitted
            if action == 'submit':
                neurologist_group = Group.objects.get(name='Neurologist')
                for neurologist in neurologist_group.user_set.all():
                    send_notification(
                        user=neurologist,
                        notification_type='update',
                        title='New Patient Case',
                        message=f'A new patient case has been submitted by {request.user.get_full_name() or request.user.username}.',
                        content_object=patient
                    )
            
            messages.success(request, success_message)
            return redirect('technician:patient_detail', pk=patient.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientForm()
    
    return render(request, 'technician/patient_form.html', {'form': form, 'title': 'New Patient'})

@login_required
@user_passes_test(is_technician)
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
            
            # Send notification to neurologists if submitted
            if action == 'submit':
                neurologist_group = Group.objects.get(name='Neurologist')
                for neurologist in neurologist_group.user_set.all():
                    send_notification(
                        user=neurologist,
                        notification_type='update',
                        title='Patient Case Updated',
                        message=f'A patient case has been updated and resubmitted by {request.user.get_full_name() or request.user.username}.',
                        content_object=patient
                    )
            
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
@user_passes_test(is_technician)
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk, technician=request.user)
    
    if request.method == 'POST':
        if 'update_nihss' in request.POST:
            patient.nihss = request.POST.get('nihss', '')
            patient.save()
            
            # Send notification to neurologists if case is already submitted
            if patient.status != 'NEW':
                try:
                    neurologist_group = Group.objects.get(name='Neurologist')
                    for neurologist in neurologist_group.user_set.all():
                        send_notification(
                            user=neurologist,
                            notification_type='update',
                            title='NIHSS Score Updated',
                            message=f'NIHSS score has been updated for patient {patient.first_name} {patient.last_name}.',
                            content_object=patient
                        )
                except Group.DoesNotExist:
                    # Log this as a warning but don't fail the update
                    messages.warning(request, 'Could not notify neurologists - group not found')
            
            messages.success(request, 'NIHSS details updated successfully.')
            return redirect('technician:patient_detail', pk=pk)
            
        elif 'upload_ct_scan' in request.POST and request.FILES.get('ct_scan'):
            try:
                ct_scan = CTScan.objects.create(
                    patient=patient,
                    image=request.FILES['ct_scan'],
                    date_taken=request.POST['date_taken'],
                    description=request.POST.get('description', '')
                )
                
                # Send notification to neurologists if case is already submitted
                if patient.status != 'NEW':
                    try:
                        neurologist_group = Group.objects.get(name='Neurologist')
                        for neurologist in neurologist_group.user_set.all():
                            send_notification(
                                user=neurologist,
                                notification_type='update',
                                title='New CT Scan Added',
                                message=f'A new CT scan has been uploaded for patient {patient.first_name} {patient.last_name}.',
                                content_object=ct_scan
                            )
                    except Group.DoesNotExist:
                        # Log this as a warning but don't fail the upload
                        messages.warning(request, 'Could not notify neurologists - group not found')
                
                messages.success(request, 'CT scan uploaded successfully.')
            except Exception as e:
                messages.error(request, f'Error uploading CT scan: {str(e)}')
            return redirect('technician:patient_detail', pk=pk)
    
    vital_signs = patient.vital_signs_logs.all()[:5]
    ct_scans = patient.ct_scans.all().order_by('-date_taken')
    consultations = patient.consultations.all().order_by('-created_at')
    
    context = {
        'patient': patient,
        'vital_signs': vital_signs,
        'ct_scans': ct_scans,
        'consultations': consultations,
    }
    return render(request, 'technician/patient_detail.html', context)

@login_required
@user_passes_test(is_technician)
def patient_list(request):
    patients = Patient.objects.filter(technician=request.user).order_by('-created_at')
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'technician/patient_list.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_technician)
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk, technician=request.user)
    
    if request.method == 'POST':
        patient.delete()
        messages.success(request, f'Patient {patient.first_name} {patient.last_name} has been deleted successfully.')
        return redirect('technician:patient_list')
    
    return render(request, 'technician/patient_confirm_delete.html', {'patient': patient})
