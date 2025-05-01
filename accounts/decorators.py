from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def is_neurologist(user):
    """
    Check if the user is a neurologist.
    """
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'NEUROLOGIST'

def is_technician(user):
    """
    Check if the user is a technician.
    """
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'TECHNICIAN'

def role_required(role):
    """
    Decorator for views that checks that the user has the required role,
    redirecting to the login page if necessary.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')
            
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, 'User profile not found.')
                return redirect('accounts:login')
            
            if request.user.userprofile.role != role:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
