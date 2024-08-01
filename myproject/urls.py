import subprocess

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import sys

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Jpage.urls')),
]