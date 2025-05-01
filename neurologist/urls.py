from django.urls import path
from . import views

app_name = 'neurologist'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cases/', views.case_history, name='case_history'),
    path('consultation/<int:patient_id>/start/', views.start_consultation, name='start_consultation'),
    path('consultation/<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('consultation/<int:patient_id>/simulate/', views.simulate_diagnosis, name='simulate_diagnosis'),
]
