import subprocess
import threading
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns= [
    path('admin/', admin.site.urls),
    path('travel/', include('travel_recommend.urls')),
    path('jpages/', include('Jpage.urls', namespace='Jpage')),
    path('diary/', include('diaryapp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

