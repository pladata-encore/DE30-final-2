from django.urls import path
from . import views

app_name= 'travel'

urlpatterns = [
    path('', views.index, name='service_main'), # 서비스 메인 페이지
    path('recommend/', views.recommend, name='recommend'),    # 사용자 입력을 받는 페이지 URL
    path('ajax/load-subregions/', views.load_subregions, name='load_subregions'),     # AJAX로 세부 지역 정보 받아오는 URL
    path('results/<str:plan_id>/', views.results, name='results'),  # 사용자 입력으로부터 추천 결과를 받는 페이지 URL
    path('get_place_info/', views.get_place_info, name='get_place_info'),  # 추천 결과에서 장소 클릭 시 보여지는 모달에 포함되는 여행 장소 정보
    path('view_schedule/<str:plan_id>/', views.view_schedule, name='view_schedule'),
    path('test-redirect/', views.test_redirect, name='test_redirect')

]
