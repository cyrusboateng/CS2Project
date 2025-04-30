from django.urls import path
from . import views

app_name = 'neurologist'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cases/pending/', views.pending_cases, name='pending_cases'),
    path('cases/history/', views.case_history, name='case_history'),
]
