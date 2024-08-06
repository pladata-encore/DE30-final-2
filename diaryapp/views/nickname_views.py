import requests
import pymongo
from django.conf import settings
from django.http import JsonResponse
import uuid
import json
import gzip
from io import BytesIO

# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
collection = db['areaBaseList']
badge_collection = db['diaryapp_badge']
nickname_collection = db['diaryapp_nickname']


# 별명 생성 함수
def create_nickname(unique_diary_id, user_email, content, plan_id):

    print(f'--------여기는 create_nickname-- {plan_id}')
    # 별명 api 호출
    url = 'http://localhost:5000/generate-nickname/'
    params = {
        'plan_id': plan_id,
        'content': content,
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch data from API"}, status=500)

    data = json.loads(response.content)
    title = data[0]
    nickname = data[1]

    # 뱃지 찾기
    badge = find_badge(title)
    if not badge:
        return JsonResponse({"error": "No badge found for the given title"}, status=404)

    # 별명 저장
    nickname_id = save_nickname(nickname, badge, unique_diary_id, user_email, title)

    return nickname_id


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
        "nickname_id": str(uuid.uuid4()),
        "nickname": nickname,
        "badge_id": badge['badge_id'],
        "unique_diary_id": unique_diary_id,
        "user_email":user_email,
        "related_title": title
    }
    nickname_collection.insert_one(nickname_document)
    return nickname_document['nickname_id']


# 뱃지 이미지 압축 해제 함수
def decompress_badge(badge):

    compressed_img = badge['badge']

    # Gzip 압축 해제
    img_gzip = BytesIO(compressed_img)
    with gzip.GzipFile(fileobj=img_gzip, mode='rb') as f:
        badge_image = f.read().decode('utf-8')

    return badge_image


# 별명, 뱃지 db에서 불러오기 함수
def get_nickname(nickname_id=None):
    if nickname_id:
        target_nickname = nickname_collection.find_one({"nickname_id": nickname_id})
        nickname = target_nickname['nickname']
        badge_id = target_nickname['badge_id']

        target_badge = badge_collection.find_one({"badge_id": badge_id})
        badge_name = target_badge['name']

        compressed_img = target_badge['badge']
        # Gzip 압축 해제
        img_gzip = BytesIO(compressed_img)
        with gzip.GzipFile(fileobj=img_gzip, mode='rb') as f:
            badge_image = f.read().decode('utf-8')

        return nickname_id, nickname, badge_name, badge_image
    else :
        return '','별명이 없습니다.', '', ''

















