import urllib.request
from urllib.parse import urlencode, quote_plus
import json
from pymongo import MongoClient
import time

# MongoDB 연결 설정
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client.MyDiary

# API 키 설정
key = "자신의 키를 입력하세요"

# 페이지 단위로 데이터 가져오기
num_of_rows = 100  # 한 번에 가져올 데이터 개수
max_retries = 5
retry_delay = 5  # 초

# 중분류(category 2) 데이터에 대한 대분류 코드와 중분류 코드 가져오기
cat2_data = db.categoryCode2.find({}, {'_id': 0, 'code': 1, 'cat1_code': 1})

# 중분류 코드별로 소분류(category 3) 데이터 수집
url_cat3 = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"

for item in cat2_data:
    cat1_code = item['cat1_code']
    cat2_code = item['code']

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
            quote_plus('cat2'): cat2_code,
            quote_plus('_type'): 'json'
        }, encoding='utf-8')

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url_cat3 + queryParams)
                response = urllib.request.urlopen(req, timeout=10)
                response_body = response.read()

                response_text = response_body.decode('utf-8')
                data = json.loads(response_text)

                if page_no == 1:
                    total_count = data['response']['body']['totalCount']

                items = data['response']['body']['items']['item']

                # 각 아이템에 대분류 코드와 중분류 코드 추가
                for item in items:
                    item['cat1_code'] = cat1_code
                    item['cat2_code'] = cat2_code

                db.categoryCode3.insert_many(items)

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
