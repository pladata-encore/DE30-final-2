# diaryapp/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('generate_diary/', views.generate_diary, name='generate_diary'),
    path('write_diary/', views.write_diary, name='write_diary'),
    path('image/<int:pk>/', views.image_detail, name='image_detail'),
    path('list_diary/', views.list_diary, name='list_diary'),
    path('detail_diary/<str:unique_diary_id>/', views.detail_diary_by_id, name='detail_diary_by_id'),
    path('update_diary/<str:unique_diary_id>/', views.update_diary, name='update_diary'),
    path('delete_diary/<str:unique_diary_id>/', views.delete_diary, name='delete_diary'),
#    path('create_comments/<str:unique_diary_id>/', views.create_comments, name='create_comments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)