from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pymongo
from django.conf import settings
from django.http import JsonResponse

from .badge_views import get_main_badge
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
    user=user_info['user']
    is_own_page=user_info['is_own_page']

    # 사용자 다이어리 전체 이름 가져오기
    user['title_diary'] = user.get('title_diary', f"{user.get('name', '즐거운 여행자')}의 여행 다이어리")

    # 사용자 메인 뱃지 가져오기
    main_nickname, main_badge_name, main_badge_image = get_main_badge(user['email'])

    context = {
        'user_nickname': main_nickname,
        'user_badge_name': main_badge_name,
        'user_badge_image': main_badge_image,
        'user': user,
        'is_own_page': is_own_page,
    }
    return render(request, 'diaryapp/diary.html', context)


# 다이어리 제목 설정
# @login_required
def save_title_diary(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        # user_email = request.user.email
        # 로그인 사용자 예시 이메일
        user_email = settings.DEFAULT_FROM_EMAIL

        try:
            user = user_collection.find_one({'email': user_email})
            current_title = user.get('title_diary', '')

            if title == current_title:
                return JsonResponse({'success': True})

            if not title:
                title = f"{user.get('name', '즐거운 여행자')}의 여행 다이어리"

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