from django.urls import path
from . import views

urlpatterns = [
    path('create_schedule/', views.recommend, name='create_schedule'),    # 사용자 입력을 받는 페이지 URL
    path('ajax/load-subregions/', views.load_subregions, name='load_subregions'),     # AJAX로 세부 지역 정보 받아오는 URL
    path('results/', views.results, name='results'),  # 사용자 입력으로부터 추천 결과를 받는 페이지 URL
    path('get_place_info/', views.get_place_info, name='get_place_info'),  # 추천 결과에서 장소 클릭 시 보여지는 모달에 포함되는 여행 장소 정보
    path('save_schedule/', views.save_schedule, name="save_schedule"), # 사용자 일정을 DB에 저장
    path('', views.index, name='service_main'), # 서비스 메인 페이지
]
