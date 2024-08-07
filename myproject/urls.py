import subprocess
import threading

from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('travel/', include('travel_recommend.urls')),
    path('jpages/', include('Jpage.urls', namespace='Jpage')),
]


