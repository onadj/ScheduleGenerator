from django.urls import path
from .views import generate_schedule_view

urlpatterns = [
    path('generate-schedule/', generate_schedule_view, name='generate_schedule'),
]
