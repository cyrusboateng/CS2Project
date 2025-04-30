from django.urls import path
from . import views

app_name = 'neurologist'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]
