from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import logout
from .models import UserProfile
from .forms import UserProfileForm

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile for the new user
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role updated successfully')
            return redirect('accounts:dashboard')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def dashboard(request):
    try:
        role = request.user.userprofile.role
        if role == 'TECHNICIAN':
            return redirect('technician:dashboard')
        elif role == 'NEUROLOGIST':
            return redirect('neurologist:dashboard')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please select your role (Technician or Neurologist)')
        return redirect('accounts:profile')
    
    messages.info(request, 'Please select your role to continue')
    return render(request, 'accounts/dashboard.html', {'show_role_selection': True})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
