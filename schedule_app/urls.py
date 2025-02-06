from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('schedule/', include('schedule.urls')),  # Povezujemo aplikaciju schedule
]
