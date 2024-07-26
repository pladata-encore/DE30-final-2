import pymongo
from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

mongo_client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'],
                                   username=settings.DATABASES['default']['CLIENT']['username'],
                                   password=settings.DATABASES['default']['CLIENT']['password'])
db = mongo_client[settings.DATABASES['default']['NAME']]
aiwritemodel_collection = db['diaryapp_aiwritemodel']
imagemodel_collection = db['diaryapp_imagemodel']

def filter_diaries(year=None, month=None):
    match_condition = {}
    if year and month:
        start_date = datetime(year=int(year), month=int(month), day=1)
        if int(month) == 12:
            end_date = datetime(year=int(year) + 1, month=1, day=1)
        else:
            end_date = datetime(year=int(year), month=int(month) + 1, day=1)
        match_condition['created_at'] = {'$gte': start_date, '$lt': end_date}

    pipeline = [
        {'$match': match_condition},
        {'$lookup': {
            'from': 'diaryapp_imagemodel',
            'localField': 'representative_image_id',
            'foreignField': 'id',
            'as': 'representative_image'
        }},
        {'$project': {
            'unique_diary_id': 1,
            'diarytitle': 1,
            'created_at': 1,
            'representative_image': {'$arrayElemAt': ['$representative_image', 0]}
        }},
        {'$sort': {'created_at': -1}}
    ]

    result = list(aiwritemodel_collection.aggregate(pipeline))
    print(f"Total diaries found: {len(result)}")
    for diary in result:
        print(f"Diary: {diary.get('diarytitle', 'No title')}, "
              f"Created: {diary.get('created_at', 'No date')}, "
              f"Has Image: {'Yes' if diary.get('representative_image') else 'No'}")
    return result
