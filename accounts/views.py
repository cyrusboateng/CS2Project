from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.db import transaction
from .models import UserProfile
from .forms import UserProfileForm, UserCreationForm
import logging

logger = logging.getLogger(__name__)

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    role = form.cleaned_data.get('role')
                    logger.error(f"Creating profile with role: {role}")  # Debug log
                    
                    # Create UserProfile
                    profile = UserProfile.objects.create(
                        user=user,
                        role=role
                    )
                    logger.error(f"Profile created: {profile}")  # Debug log
                    
                messages.success(request, 'Account created successfully. You can now log in.')
                return redirect('accounts:login')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")  # Log the actual error
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Registration error: {str(e)}')
        else:
            # Log form errors
            logger.error(f"Form errors: {form.errors}")
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    profile = request.user.userprofile
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def dashboard(request):
    try:
        role = request.user.userprofile.role
        if role == 'TECHNICIAN':
            return redirect('technician:dashboard')
        elif role == 'NEUROLOGIST':
            return redirect('neurologist:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile error. Please contact support.')
        return redirect('accounts:login')
    
    messages.error(request, 'Invalid role configuration')
    return redirect('accounts:login')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
