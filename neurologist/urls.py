from django.urls import path
from . import views

app_name = 'neurologist'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pending/', views.pending_cases, name='pending_cases'),
    path('history/', views.case_history, name='case_history'),
    path('consultation/start/<int:patient_id>/', views.start_consultation, name='start_consultation'),
    path('consultation/<int:pk>/', views.consultation_detail, name='consultation_detail'),
]
