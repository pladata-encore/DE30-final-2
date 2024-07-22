from pymongo import MongoClient
from datetime import datetime

# MongoDB 클라이언트 연결
client = MongoClient('mongodb://localhost:27017/')
db = client['diary']
collection = db['diaryapp_aiwritemodel']

def filter_diaries(year=None, month=None):
    # 조건이 없으면 모든 다이어리를 반환
    if not year or not month:
        return collection.find()

    # 월별로 필터링
    start_date = datetime(year=int(year), month=int(month), day=1)
    if int(month) == 12:
        end_date = datetime(year=int(year) + 1, month=1, day=1)
    else:
        end_date = datetime(year=int(year), month=int(month) + 1, day=1)

    return collection.find({
        'created_at': {
            '$gte': start_date,
            '$lt': end_date
        }
    })