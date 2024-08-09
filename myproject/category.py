import urllib.request
from urllib.parse import urlencode, quote_plus
import json
import time
from pymongo import MongoClient

# MongoDB 연결 설정
# client = MongoClient('mongodb://127.0.0.1:27017/')
# db = client.MyDiary
from django.conf import settings
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]
content_type_collection = db.contentTypeId

# API 키 설정
key = "자신의 키를 입력하세요"

# 페이지 단위로 데이터 가져오기 설정
num_of_rows = 100  # 한 번에 가져올 데이터 개수
max_retries = 5
retry_delay = 5  # 초

# 데이터 수집 함수 정의
def collect_data(url, params):
    page_no = 1
    while True:
        queryParams = '?' + urlencode(params, encoding='utf-8')

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url + queryParams)
                response = urllib.request.urlopen(req, timeout=10)
                response_body = response.read()

                response_text = response_body.decode('utf-8')
                data = json.loads(response_text)

                if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
                    items = data['response']['body']['items']['item']
                    return items, data['response']['body']['totalCount'], page_no

            except urllib.error.URLError as e:
                print(f"시도 {attempt + 1} 실패: {e}")
                time.sleep(retry_delay)
            except json.JSONDecodeError as e:
                print(f"JSON 디코딩 오류: {e}")
                break

        page_no += 1

    return [], 0, 0

# 모든 code 값을 가져옴
content_types = content_type_collection.find({}, {"code": 1, "_id": 0})
content_type_ids = [item['code'] for item in content_types]

# 대분류(category 1) 데이터 수집
url_cat1 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"
params_cat1 = {
    quote_plus('ServiceKey'): key,
    quote_plus('numOfRows'): num_of_rows,
    quote_plus('pageNo'): 1,
    quote_plus('MobileOS'): 'ETC',
    quote_plus('MobileApp'): 'AppTest',
    quote_plus('_type'): 'json'
}

items, total_count, page_no = collect_data(url_cat1, params_cat1)

if items:
    db.categoryCode1.insert_many(items)

    if page_no == 1:
        total_count_cat1 = total_count

# 중분류(category 2) 데이터 수집
url_cat2 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"
params_cat2 = {
    quote_plus('ServiceKey'): key,
    quote_plus('numOfRows'): num_of_rows,
    quote_plus('pageNo'): 1,
    quote_plus('MobileOS'): 'ETC',
    quote_plus('MobileApp'): 'AppTest',
    quote_plus('_type'): 'json'
}

for content_type_id in content_type_ids:
    params_cat2['cat1'] = content_type_id
    items, total_count, page_no = collect_data(url_cat2, params_cat2)

    if items:
        db.categoryCode2.insert_many(items)

        if page_no == 1:
            total_count_cat2 = total_count

# 소분류(category 3) 데이터 수집
url_cat3 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"
params_cat3 = {
    quote_plus('ServiceKey'): key,
    quote_plus('numOfRows'): num_of_rows,
    quote_plus('pageNo'): 1,
    quote_plus('MobileOS'): 'ETC',
    quote_plus('MobileApp'): 'AppTest',
    quote_plus('_type'): 'json'
}

for content_type_id in content_type_ids:
    for cat1_code in db.categoryCode1.distinct('code'):
        for cat2_code in db.categoryCode2.distinct('code'):
            params_cat3['cat1'] = cat1_code
            params_cat3['cat2'] = cat2_code
            params_cat3['contentTypeId'] = content_type_id

            items, total_count, page_no = collect_data(url_cat3, params_cat3)

            if items:
                db.categoryCode3.insert_many(items)

                if page_no == 1:
                    total_count_cat3 = total_count

print("데이터 수집 완료")
