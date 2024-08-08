from pymongo import MongoClient

# MongoDB 연결 설정

# client = MongoClient('mongodb://127.0.0.1:27017/')
# db = client.MyDiary
from django.conf import settings
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 삽입할 데이터 문서 생성
data = [
    {"code": 12, "name": "관광지"},
    {"code": 14, "name": "문화시설"},
    {"code": 25, "name": "여행코스"},
    {"code": 28, "name": "레포츠"},
    {"code": 38, "name": "쇼핑"},
    {"code": 39, "name": "음식점"}
]

# MongoDB에 데이터 삽입
db.contentTypeId.insert_many(data)
