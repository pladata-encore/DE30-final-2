from django.urls import path, re_path
from . import views

urlpatterns = [
    path('generate_diary/', views.generate_diary, name='generate_diary'),
    path('write_diary/', views.write_diary, name='write_diary'),
    path('list_diary/', views.list_diary, name='list_diary'),
#    path('detail_diary/title/<str:diary_title>/', views.detail_diary_by_title, name='detail_diary_by_title'),
    path('detail_diary/id/<str:unique_diary_id>/', views.detail_diary_by_id, name='detail_diary_by_id'),
]
