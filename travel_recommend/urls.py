from django.urls import path
from . import views

urlpatterns = [
    path('create_schedule/', views.recommend, name='create_schedule'),    # 사용자 입력을 받는 페이지 URL
    path('ajax/load-subregions/', views.load_subregions, name='load_subregions'),     # AJAX로 세부 지역 정보 받아오는 URL
    path('results/', views.results, name='results'),  # 사용자 입력으로부터 추천 결과를 받는 페이지 URL
    path('test123/',views.index)
]
