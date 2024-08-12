from django.conf import settings
from pymongo import MongoClient

import pymongo
from diaryapp.views.badge_views import get_main_badge

# MongoDB 클라이언트 설정
# db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]
# db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']['CLIENT']]
# MongoDB 클라이언트 설정
client = pymongo.MongoClient('mongodb://127.0.0.1:27017')
db = client['MyDiary']

# 컬렉션
user_collection = db['users_usermodel']

user_collection_social = db['users_usermodel']
user_collection_basic = db['users']

# 사용자 정보
def get_user(request, user_email=None):
    # 사용자 정보 조회
    if user_email :
        # 다른 사용자
        user = user_collection.find_one({'email': user_email})
    else:
        # 로그인 사용자
        user_email = request.session.get('userSession')
        # print(f'-----------------context_processors----{user_email}')
        #user = user_collection.find_one({'email': user_email})
        user = {
            'email': 'neweeee@gmail.com',
            'username': '로그인 사용자'
        }

    # 로그인 사용자 확인
    #is_own_page = user and (user['email'] == request.user.email)

    return {
        'user': user,
        #'is_own_page': is_own_page,
        'is_own_page': True,
        # 로그인 사용자 테스트 : True
        # 다른 사용자 테스트 : 주소에 'view/<str:user_email>/' 넣기, urls 설정, False
    }



# 메인 뱃지
def main_badge(request):

    # user_email = request.user.email
    # 로그인 사용자 예시 이메일
    user_email = settings.DEFAULT_FROM_EMAIL

    main_nickname_id, main_nickname, main_badge_name, main_badge_image = get_main_badge(user_email)
    return {
        'main_nickname': main_nickname,
        'main_badge_name': main_badge_name,
        'main_badge_image': main_badge_image
    }
