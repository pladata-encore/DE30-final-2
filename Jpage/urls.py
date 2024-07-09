from django.urls import path
from Jpage import views

urlpatterns = [
    path('jpage/', views.get_data, name='get_data'),
    path('middlecategory/', views.get_middle_category, name='get_middle_category'),
    path('smallcategory/', views.get_small_category, name='get_small_category'),
    path('citydistrict/', views.get_cityDistrict, name='get_cityDistrict'),
    path('place/', views.get_places, name='get_places')
]




