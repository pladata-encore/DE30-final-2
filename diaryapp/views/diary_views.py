from django.shortcuts import render, get_object_or_404
import logging
import traceback
import pymongo
from django.db import DatabaseError
from django.http import HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse

from diaryapp.models import AiwriteModel
from .nickname_views import get_nickname
from .badge_views import get_main_badge
from common.context_processors import get_user


# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
user_collection = db['users']


logger = logging.getLogger(__name__)



# 다이어리 메인
#@login_required
def viewDiary(request, user_email=None):

    # 사용자 정보 가져오기
    user_info = get_user(request, user_email)
    user = user_info['user']
    is_own_page = user_info['is_own_page']

    # 사용자 다이어리 전체 이름 가져오기
    user['title_diary'] = user.get('title_diary', f"{user.get('name', '즐거운 여행자')}의 여행 다이어리")

    # 사용자 메인 뱃지 가져오기
    main_nickname, main_badge_name, main_badge_image = get_main_badge(user['email'])

    # 사용자 다이어리 슬라이드
    enriched_diary_list = []
    try:
        diaries = AiwriteModel.objects.filter(user_email=user['email']).order_by('-created_at')[:5]

        # 디버깅을 위한 로그 추가
        logger.info(f"Retrieved diaries for {user_email}")
        print()
        for diary in diaries:
            logger.info(f"Diary: {diary.unique_diary_id}, Title: {diary.diarytitle}, Created at: {diary.created_at}")

            try:
                diary_model = get_object_or_404(AiwriteModel, unique_diary_id=diary.unique_diary_id)
                nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
                enriched_diary = {
                    'diary': diary,
                    'nickname': nickname,
                    'badge_name': badge_name,
                    'badge_image': badge_image
                }
                enriched_diary_list.append(enriched_diary)
            except Exception as e:
                logger.error(f"Error retrieving additional info for diary {diary.unique_diary_id}: {str(e)}")
                logger.error(traceback.format_exc())
                enriched_diary_list.append({
                    'diary': diary,
                    'nickname': 'Unknown',
                    'badge_name': 'Unknown',
                    'badge_image': 'Unknown'
                })

    except DatabaseError as e:
        logger.error(f"Database error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        enriched_diary_list = []
        return HttpResponseServerError("An error occurred while accessing the database.")

    context = {
        'user_nickname': main_nickname,
        'user_badge_name': main_badge_name,
        'user_badge_image': main_badge_image,
        'user': user,
        'is_own_page': is_own_page,
        'diary_list': enriched_diary_list,
        'user_email': user_email,
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