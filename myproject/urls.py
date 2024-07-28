import subprocess

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import sys

def start_fastapi_server(request):
    subprocess.Popen([sys.executable, "-m", "uvicorn","travel_recommend.fastapi_app.app:app","--reload","--port","5000"])
    return HttpResponse("FastAPI server started")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('travel_recommend.urls')),
]

import threading
threading.Thread(target=start_fastapi_server).start()