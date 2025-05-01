from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def is_neurologist(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'NEUROLOGIST':
            return function(request, *args, **kwargs)
        messages.error(request, 'You must be a neurologist to access this page.')
        return redirect('login')
    return wrap

def is_technician(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'TECHNICIAN':
            return function(request, *args, **kwargs)
        messages.error(request, 'You must be a technician to access this page.')
        return redirect('login')
    return wrap

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
