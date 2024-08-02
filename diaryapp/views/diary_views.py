from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pymongo
from django.conf import settings
from django.http import JsonResponse

from .badge_views import *
from common.context_processors import get_user


# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
user_collection = db['users']


# 다이어리 메인
#@login_required
def viewDiary(request, user_email=None):

    # 사용자 정보 가져오기
    user_info = get_user(request, user_email)

    context = {
        'user': user_info['user'],
        #'is_own_page': is_own_page,
        'is_own_page': user_info['is_own_page'],
        # 내 페이지 테스트 : True
        # 다른 사람 페이지 테스트 : 주소에 'view/<str:user_email>/' 넣기, False
    }
    return render(request, 'diaryapp/diary.html', context)


# 다이어리 제목 설정
# @login_required
def save_title_diary(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        # 현재 로그인한 사용자 이메일 가져 오기
        # user_email = request.user.email
        user_email = 'ymlove112002@naver.com'  # 예시 이메일

        try:
            user = user_collection.find_one({'email': user_email})
            current_title = user.get('title_diary', '')

            if title == current_title:
                return JsonResponse({'success': True})

            if not title:
                title = f"{user.get('name', '여행자')}의 여행 다이어리"

            result = user_collection.update_one(
                {'email': user_email},
                {'$set': {'title_diary': title}}
            )

            if result.matched_count > 0:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': '서버 오류: ' + str(e)})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 다이어리 메인 대표 뱃지
def main_badge(request):
    main_nickname, main_badge_name, main_badge_image = get_main_badge(user_email)
    return {
        'main_nickname': main_nickname,
        'main_badge_name': main_badge_name,
        'main_badge_image': main_badge_image
    }