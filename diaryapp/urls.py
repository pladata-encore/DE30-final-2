from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from diaryapp.views import diarywrite_views, comment_views, base_views, diary_views, nickname_views

urlpatterns = [
    #### diarywrite_views.py ####
    # 다이어리 생성
    path('generate_diary/', diarywrite_views.generate_diary, name='generate_diary'),
    path('write_diary/', diarywrite_views.write_diary, name='write_diary'),
    path('image/<int:pk>/', diarywrite_views.image_detail, name='image_detail'),

    # 리스트 다이어리
    path('list_diary/', diarywrite_views.list_diary, name='list_diary'),

    # 다이어리 상세화면
    path('detail_diary/<str:unique_diary_id>/', diarywrite_views.detail_diary_by_id, name='detail_diary_by_id'),

    # 다이어리 업데이트
    path('update_diary/<str:unique_diary_id>/', diarywrite_views.update_diary, name='update_diary'),

    # 다이어리 삭제
    path('delete_diary/<str:unique_diary_id>/', diarywrite_views.delete_diary, name='delete_diary'),

    # 다이어리 메인
    path('',diarywrite_views.viewDiary),
    # path('<str:social_id>/', diarywrite_views.viewDiary, name='user_diary_main'),

    # 일정 모달창
    path('plan_modal/<str:unique_diary_id>/', diarywrite_views.plan_modal, name='plan_modal'),


    #### comment_views.py ####
    # 댓글 달기
    path('create_comment/<str:unique_diary_id>/', comment_views.create_comment, name='create_comment'),

    # 댓글 삭제
    path('comment/delete/<str:diary_id>/<int:comment_id>/', comment_views.delete_comment, name='delete_comment'),

    # 태그된 친구 클릭 시 메인 다이어리 화면 이동 - 사용자 다이어리의 메인 화면 경로
    # path('maindiary', views.delete_diary, name='main_diary'),


    # 다이어리 메인
    path('',diary_views.viewDiary),


    # Bootstrap 테마 예시 페이지
    path('index', base_views.viewIndex),
    path('elements', base_views.viewElements),
    path('generic', base_views.viewGeneric)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


