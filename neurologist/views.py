from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'neurologist/dashboard.html', {
        'title': 'Neurologist Dashboard'
    })

@login_required
def pending_cases(request):
    return render(request, 'neurologist/pending_cases.html', {
        'title': 'Pending Cases',
        'cases': []  # We'll add actual cases later
    })

@login_required
def case_history(request):
    return render(request, 'neurologist/case_history.html', {
        'title': 'Case History',
        'cases': []  # We'll add actual cases later
    })
