import urllib.request
from urllib.parse import urlencode, quote_plus
import json
from pymongo import MongoClient
import time

# MongoDB 연결 설정
# client = MongoClient('mongodb://127.0.0.1:27017/')
# db = client.MyDiary
from django.conf import settings
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# API 키 설정
key = "자신의 키를 입력하세요"

# 페이지 단위로 데이터 가져오기
num_of_rows = 100  # 한 번에 가져올 데이터 개수
max_retries = 5
retry_delay = 5  # 초

# 대분류(category 1) 데이터 수집
url_cat1 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"
page_no = 1
total_count = None
while True:
    queryParams = '?' + urlencode({
        quote_plus('ServiceKey'): key,
        quote_plus('numOfRows'): num_of_rows,
        quote_plus('pageNo'): page_no,
        quote_plus('MobileOS'): 'ETC',
        quote_plus('MobileApp'): 'AppTest',
        quote_plus('_type'): 'json'
    })

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url_cat1 + queryParams)
            response = urllib.request.urlopen(req, timeout=10)
            response_body = response.read()

            response_text = response_body.decode('utf-8')
            data = json.loads(response_text)

            if page_no == 1:
                total_count = data['response']['body']['totalCount']

            items = data['response']['body']['items']['item']
            db.categoryCode1.insert_many(items)

            page_no += 1

            if len(items) < num_of_rows:
                break

            break

        except urllib.error.URLError as e:
            print(f"시도 {attempt + 1} 실패: {e}")
            time.sleep(retry_delay)
        except json.JSONDecodeError as e:
            print(f"JSON 디코딩 오류: {e}")
            break

    if total_count is not None and page_no > (total_count // num_of_rows) + 1:
        break

# 대분류 코드 리스트 추출
cat1_codes = db.categoryCode1.distinct('code')

# 중분류(category 2) 데이터 수집
url_cat2 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"

for cat1_code in cat1_codes:
    page_no = 1
    total_count = None
    while True:
        queryParams = '?' + urlencode({
            quote_plus('ServiceKey'): key,
            quote_plus('numOfRows'): num_of_rows,
            quote_plus('pageNo'): page_no,
            quote_plus('MobileOS'): 'ETC',
            quote_plus('MobileApp'): 'AppTest',
            quote_plus('cat1'): cat1_code,
            quote_plus('_type'): 'json'
        }, encoding='utf-8')

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url_cat2 + queryParams)
                response = urllib.request.urlopen(req, timeout=10)
                response_body = response.read()

                response_text = response_body.decode('utf-8')
                data = json.loads(response_text)

                if page_no == 1:
                    total_count = data['response']['body']['totalCount']

                items = data['response']['body']['items']['item']

                # 각 아이템에 대분류 코드 추가
                for item in items:
                    item['cat1_code'] = cat1_code

                db.categoryCode2.insert_many(items)

                page_no += 1

                if len(items) < num_of_rows:
                    break

                break

            except urllib.error.URLError as e:
                print(f"시도 {attempt + 1} 실패: {e}")
                time.sleep(retry_delay)
            except json.JSONDecodeError as e:
                print(f"JSON 디코딩 오류: {e}")
                break

        if total_count is not None and page_no > (total_count // num_of_rows) + 1:
            break
