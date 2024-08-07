from django.urls import path
from Jpage import views

app_name = 'Jpage'

urlpatterns = [
    path('jpage/', views.get_data, name='get_data'),
    path('middlecategory/', views.get_middle_category, name='get_middle_category'),
    path('smallcategory/', views.get_small_category, name='get_small_category'),
    path('citydistrict/', views.get_cityDistrict, name='get_cityDistrict'),
    path('place/', views.get_places, name='get_places'),
    path('coordinate/', views.get_coordinate, name='get_coordinate'),
    path('save_Plan/', views.get_Jplan, name='get_Jplan'),
    path('user_info/', views.user_info_view, name='user_info'),
    path('user_info/<str:user_email>/', views.user_info_view, name='user_info_with_email'),
    path('J/', views.jpagerender, name='jpagerender'),
]


