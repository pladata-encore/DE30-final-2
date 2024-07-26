import requests
import pymongo
from django.conf import settings
from django.http import JsonResponse
import uuid
import json
import gzip
from io import BytesIO

# MongoDB 클라이언트 설정
mongo_client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'],
                                   username=settings.DATABASES['default']['CLIENT']['username'],
                                   password=settings.DATABASES['default']['CLIENT']['password'])
db = mongo_client[settings.DATABASES['default']['NAME']]

# 컬렉션 선택
collection = db['areaBaseList']
badge_collection = db['diaryapp_badge']
nickname_collection = db['diaryapp_nickname']



# 별명 생성 함수
def create_nickname(unique_diary_id, user_email, content, plan_id):
    # 별명 api 호출
    url = 'http://localhost:5000/generate-nickname/'
    params = {
        'plan_id': plan_id,
        'content': content,
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch data from API"}, status=500)


    # # data = json.loads(response.content)
    # print(data)
    # title = data.get('title')
    # print(title)
    # nickname = data.get('nickname')

    try:
        json_data = response.json()  # requests 라이브러리의 json 메소드를 사용하여 자동으로 파싱
        print("Parsed JSON Data:", json_data)  # 파싱된 데이터 출력
    except ValueError as e:
        print("Error parsing JSON:", e)
        return None, None, None, None  # 오류 시 None 반환

    # title과 nickname 추출
    title = json_data.get('title')
    nickname = json_data.get('nickname')

    return title, nickname

    # # 뱃지 찾기
    # badge = find_badge(title)
    # if not badge:
    #     return JsonResponse({"error": "No badge found for the given title"}, status=404)
    #
    # # 별명 저장
    # nickname_id = save_nickname(nickname, badge, unique_diary_id, user_email, title)
    #
    # # 뱃지 이미지 Base64 디코딩 및 압축 해제
    # badge_image = decompress_badge(badge)
    # badge_name = badge['name']
    #
    # return JsonResponse({"nickname_id": str(nickname_id), "nickname": nickname, "badge_name": badge_name, "badge_image": badge_image}, status=201)



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
def save_nickname(nickname, badge, unique_diary_id, user_email, title):
    nickname_document = {
        "nickname_id": uuid.uuid4(),
        "nickname": nickname,
        "badge_id": badge['badge_id'],
        "unique_diary_id": unique_diary_id,
        "user_email":user_email,
        "title": title
    }
    result = nickname_collection.insert_one(nickname_document)
    return result.nickname_id, result.nickname, result.badge


# 별명, 뱃지 db에서 불러오기 함수
# 여기에 별명, 뱃지를 불러오는 함수를 만들고 여기저기 가져다 쓰면 될듯
# 다이어리 아이디 필요, 다이어리에서 유저아이디, 별명아이디 사용, 별명아이디로 뱃지아이디 찾기
# 대표 별명 만들기



# 뱃지 이미지 압축 해제 함수
def decompress_badge(badge):

    compressed_img = badge['badge']

    # Gzip 압축 해제
    img_gzip = BytesIO(compressed_img)
    with gzip.GzipFile(fileobj=img_gzip, mode='rb') as f:
        badge_image = f.read().decode('utf-8')

    return badge_image













