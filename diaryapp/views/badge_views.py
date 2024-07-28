from django.shortcuts import render
import pymongo
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .nickname_views import *


User = get_user_model()

# MongoDB 클라이언트 설정
mongo_client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'],
                                   username=settings.DATABASES['default']['CLIENT']['username'],
                                   password=settings.DATABASES['default']['CLIENT']['password'])
db = mongo_client[settings.DATABASES['default']['NAME']]

# 컬렉션 선택
collection = db['areaBaseList']
badge_collection = db['diaryapp_badge']
nickname_collection = db['diaryapp_nickname']

#@login_required
def list_badge(request):
    user_email = settings.DEFAULT_FROM_EMAIL
    # user_email = request.user.email
    nicknames = nickname_collection.find({"user_email": user_email})

    list_badge = []
    for nickname in nicknames :
        nickname, badge_name, badge_image = get_nickname(nickname['nickname_id'])
        badgenickname = {
            'nickname': nickname,
            'badge_name': badge_name,
            'badge_image': badge_image
        }
        list_badge.append(badgenickname)

    return render(request, 'diaryapp/list_badge.html', {'list_badge':list_badge})