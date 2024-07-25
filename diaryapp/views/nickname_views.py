import requests
import pymongo
from django.conf import settings
from django.http import JsonResponse
import uuid

# MongoDB 클라이언트 설정
mongo_client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'],
                                   username=settings.DATABASES['default']['CLIENT']['username'],
                                   password=settings.DATABASES['default']['CLIENT']['password'])
db = mongo_client[settings.DATABASES['default']['NAME']]

# 컬렉션 선택
collection = db['areaBaseList']
badge_collection = db['diaryapp_badge']
nickname_collection = db['diaryapp_nickname']


# 뱃지 찾기 함수
def find_badge(title):
    area_base = collection.find_one({"title": title}, {"cat1": 1, "cat3": 1, "_id": 0})
    if area_base:
        cat3 = area_base.get('cat3')
        cat1 = area_base.get('cat1')

        if cat1 in ['음식', '쇼핑']:
            badge = badge_collection.find_one({"categoryCode1": cat1})
            if cat1 == '음식' and cat3 == '카페/전통찻집':
                badge = badge_collection.find_one({"categoryCode3": cat3})
        else:
            badge = badge_collection.find_one({"categoryCode3": cat3}) if cat3 else None
            if not badge:
                badge = badge_collection.find_one({"categoryCode1": cat1}) if cat1 else None

        if not badge:
            badge = badge_collection.find_one({"name": '여행자'})

        return badge
    return badge_collection.find_one({"name": '여행자'})


# 별명 저장 함수
def save_nickname(nickname, title, unique_diary_id, badge):
    nickname_document = {
        "nickname_id": uuid.uuid4(),
        "nickname": nickname,
        "unique_diary_id": unique_diary_id,
        # api 호출하기전에 가져오는 다이어리로 연결, 일대일 연결,
        # 다이어리가 수정되거나 삭제되면 업데이트
        "badge_id": badge['badge_id'],
        "title": title
    }
    result = nickname_collection.insert_one(nickname_document)
    return result.inserted_id

# 별명 생성 함수
def create_nickname(request):
    if request.method == 'POST':
        response = requests.get('http://localhost:5000/generate-nickname/')
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch data from API"}, status=500)

        data = response.json()
        title = data['title']
        nickname = data['nickname']

        # 뱃지 찾기
        badge = find_badge(title)
        if not badge:
            return JsonResponse({"error": "No badge found for the given title"}, status=404)

        # 별명 저장
        # 다이어리 아이디 예시 : api에서 호출하면 거기서 넘겨줘도 좋을듯
        unique_diary_id='20240709062329즐거운 전주 여행'
        nickname_id = save_nickname(nickname, title, unique_diary_id, badge)

        return JsonResponse({"nickname_id": str(nickname_id), "nickname": nickname}, status=201)

    return JsonResponse({"error": "Invalid request method"}, status=405)
