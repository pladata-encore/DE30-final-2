from django.urls import path
from . import views

urlpatterns = [

    path('',views.viewDiary),

    # Bootstrap 테마 예시 페이지
    path('index',views.viewIndex),
    path('elements',views.viewElements),
    path('generic',views.viewGeneric)
    ]