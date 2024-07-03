from django.urls import path
from Jpage import views

urlpatterns = [
    path('map/', views.get_category, name='get_category')
]




