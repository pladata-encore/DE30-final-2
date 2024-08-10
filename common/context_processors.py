from django.conf import settings
from pymongo import MongoClient

from diaryapp.views.badge_views import get_main_badge

# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
user_collection_social = db['users_usermodel']
user_collection_basic = db['users']

# 사용자 정보
def get_user(request, user_email=None):
    # 세션 사용자 받아오기
    if not user_email:
        user_email = request.session.get('userSession')
        print(f'-------------------------------context_processors--session---------{user_email}')

    user = None

    # 소셜 컬렉션에서 조회
    if user_email :
        # 다른 사용자
        user = user_collection_social.find_one({'email': user_email})

    # 기본 컬렉션에서 사용자 조회
    if not user:
        user = user_collection_basic.find_one({'email': user_email})
        # user = {
        #     'username': '로그인한 사용자',
        #     'email': 'neweeee@gmail.com',
        # }

    # 로그인 사용자인지 확인
    is_own_page = user and (user['email'] == request.session.get('userSession'))

    return {
        'user': user,
        'is_own_page': is_own_page,
        #'is_own_page': True,
        # 로그인 사용자 테스트 : True
        # 다른 사용자 테스트 : 주소에 'view/<str:user_email>/' 넣기, urls 설정, False
    }



# 메인 뱃지
def main_badge(request):

    # 로그인 사용자 이메일
    user_email = request.session.get('userSession')
    print(f'-------------------------------main_badge--session-----------------{user_email}')

    main_nickname_id, main_nickname, main_badge_name, main_badge_image = get_main_badge(user_email)
    return {
        'main_nickname': main_nickname,
        'main_badge_name': main_badge_name,
        'main_badge_image': main_badge_image
    }
