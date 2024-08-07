import urllib.request
from urllib.parse import urlencode, quote_plus, unquote
import json
from pymongo import MongoClient
import time

# API URL 및 키 설정
base_url = "http://apis.data.go.kr/B551011/KorService1/"
key = "자신의 키를 입력하세요"

# MongoDB 연결 설정
client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority', 27017)
db = client.MyDiary


# 공통 함수: API 요청 보내기
def get_api_response(url, params, timeout=30):
    queryParams = '?' + urlencode(params)
    req = urllib.request.Request(url + queryParams)
    response = urllib.request.urlopen(req, timeout=timeout)
    response_body = response.read()
    return json.loads(response_body.decode('utf-8'))


# 1. 지역 코드 가져오기
area_code_url = base_url + "areaCode1"
area_code_params = {
    quote_plus('ServiceKey'): key,
    quote_plus('numOfRows'): 100,
    quote_plus('pageNo'): 1,
    quote_plus('MobileOS'): 'ETC',
    quote_plus('MobileApp'): 'AppTest',
    quote_plus('_type'): 'json'
}

area_data = get_api_response(area_code_url, area_code_params)
area_codes = [item['code'] for item in area_data['response']['body']['items']['item']]
print("Area codes retrieved:", area_codes)

# 2. 각 지역 코드별 시군구 데이터 가져오기
num_of_rows = 100
max_retries = 5
retry_delay = 5  # 초

for area_code in area_codes:
    page_no = 1
    while True:
        city_district_params = {
            quote_plus('ServiceKey'): key,
            quote_plus('numOfRows'): num_of_rows,
            quote_plus('pageNo'): page_no,
            quote_plus('MobileOS'): 'ETC',
            quote_plus('MobileApp'): 'AppTest',
            quote_plus('areaCode'): area_code,
            quote_plus('_type'): 'json'
        }

        # 반복 시도 설정
        for attempt in range(max_retries):
            try:
                city_district_data = get_api_response(area_code_url, city_district_params, timeout=60)

                # MongoDB에 데이터 삽입
                items = city_district_data['response']['body']['items']['item']
                if items:
                    # 각 아이템에 areacode 추가
                    for item in items:
                        item['areacode'] = area_code
                    db.cityDistrict1.insert_many(items)

                # 다음 페이지로 이동
                page_no += 1

                # 더 이상 데이터가 없으면 종료
                if len(items) < num_of_rows:
                    break

                # 성공적으로 데이터를 가져왔으므로 반복 시도 루프 탈출
                break

            except urllib.error.URLError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                break
            except TimeoutError as e:
                print(f"Timeout error: {e}")
                time.sleep(retry_delay)

            # 더 이상 데이터가 없으면 종료
        if len(items) < num_of_rows:
            break
