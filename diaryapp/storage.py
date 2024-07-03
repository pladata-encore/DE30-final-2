# diaryapp/storage.py

from urllib.parse import urljoin
from djongo.storage import GridFSStorage
from myproject import settings
from gridfs import GridFS
from pymongo import MongoClient

client = MongoClient('mongodb://localhost', 27017)
db = client['diary']  # MongoDB 데이터베이스 이름
fs = GridFS(db, collection='fs')  # 'fs'는 GridFS 컬렉션 이름


def save_file_to_gridfs(data, filename):
    file_id = fs.put(data, filename=filename)
    return str(file_id)

def get_file_from_gridfs(unique_diary_id):
    file = fs.get(unique_diary_id)
    return file.read() if file else None

def get_file_url_from_gridfs(unique_diary_id):
    try:
        file = fs.get(unique_diary_id)
        file_url = f"{settings.MEDIA_BASE_URL}{file.filename}"
        return file_url
    except:
        pass
def delete_file_from_gridfs(unique_diary_id):
    fs.delete(unique_diary_id)

