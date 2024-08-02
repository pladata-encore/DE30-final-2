from django.shortcuts import render, redirect
import pymongo
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .nickname_views import *

# MongoDB 클라이언트 설정
mongo_client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'],
                                   username=settings.DATABASES['default']['CLIENT']['username'],
                                   password=settings.DATABASES['default']['CLIENT']['password']
                                   )

db = mongo_client[settings.DATABASES['default']['NAME']]

# 컬렉션 선택
collection = db['areaBaseList']
badge_collection = db['diaryapp_badge']
nickname_collection = db['diaryapp_nickname']

# user 정보 가져 오기
user_email = settings.DEFAULT_FROM_EMAIL  # 예시 이메일
# user_email = request.user.email

# 뱃지 리스트 함수
@require_http_methods(["GET"])
#@login_required
def list_badge(request):

    # 대표 별명 가져 오기
    nickname_main = nickname_collection.find_one({"user_email": user_email, "is_main": True})

    if nickname_main:
        main_nickname_id = nickname_main['nickname_id']
        main_nickname, main_badge_name, main_badge_image = get_nickname(nickname_main['nickname_id'])
    else:
        main_nickname_id, main_nickname, main_badge_name, main_badge_image = '','대표 별명이 없습니다.', '', ''

    # 모든 별명 가져 오기
    nicknames = nickname_collection.find({"user_email": user_email})

    list_badge = []
    for item in nicknames :
        nickname, badge_name, badge_image = get_nickname(item['nickname_id'])
        badgenickname = {
            'nickname_id' : item['nickname_id'],
            'nickname': nickname,
            'badge_name': badge_name,
            'badge_image': badge_image,
            'is_main': item.get('is_main', False)  # 대표 여부 추가
        }
        list_badge.append(badgenickname)

    context = {
        'main_nickname_id': main_nickname_id,
        'main_nickname': main_nickname,
        'main_badge_name': main_badge_name,
        'main_badge_image': main_badge_image,
        'list_badge': list_badge,
    }

    return render(request, 'diaryapp/list_badge.html', context)


# 대표 뱃지 설정 함수
@require_http_methods(["POST"])
def set_main_badge(request):
    nickname_id = request.POST.get('nickname_id')

    # 현재 대표 뱃지
    current_main_nickname = nickname_collection.find_one({"user_email": user_email, "is_main": True})

    # 이전 대표 뱃지 False
    if current_main_nickname:
        nickname_collection.update_one(
            {'nickname_id': current_main_nickname['nickname_id']},
            {'$unset': {'is_main': False}}
        )

    # 새 대표 뱃지 True
    nickname_collection.update_one(
        {'nickname_id':nickname_id, 'user_email': user_email},
        {'$set': {'is_main': True}}
    )

    return JsonResponse({'success': True})

# 대표 뱃지 삭제 함수
@require_http_methods(["POST"])
def unset_main_badge(request):
    nickname_id = request.POST.get('nickname_id')

    # 선택된 닉네임의 is_main 필드를 삭제
    nickname_collection.update_one(
        {'nickname_id': nickname_id, 'user_email': user_email},
        {'$unset': {'is_main': False}}
    )

    return JsonResponse({'success': True})

# 대표 별명, 뱃지 db에서 불러오기 함수
def get_main_badge(user_email):
    nickname_main = nickname_collection.find_one({"user_email": user_email, "is_main": True})
    if nickname_main:
        main_nickname, main_badge_name, main_badge_image = get_nickname(nickname_main['nickname_id'])
    else:
        main_nickname, main_badge_name, main_badge_image = '대표 별명이 없습니다.', '', ''

    return main_nickname, main_badge_name, main_badge_image