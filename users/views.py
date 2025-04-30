from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegistrationForm, UserProfileUpdateForm

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            
            # Redirect based on role
            if user.userprofile.is_technician():
                return redirect('technician:dashboard')
            else:
                return redirect('neurologist:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=request.user.userprofile)
    
    return render(request, 'users/profile.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.userprofile.is_technician():
        return redirect('technician:dashboard')
    else:
        return redirect('neurologist:dashboard')
