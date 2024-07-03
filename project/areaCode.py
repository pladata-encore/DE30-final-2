import urllib.request
from urllib.parse import urlencode, quote_plus
import json
from pymongo import MongoClient
import time

url = "http://apis.data.go.kr/B551011/KorService1/areaCode1"
key = "sn4p9/xq3HzvfZw7DjDo9gJBjru0dhT62DbDbJFDdiZEYPe2Lyio/NSLbeFkKw1Of4/P8G+dQdTBfr8m0OMoQA=="

# MongoDB 연결 설정
client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority', 27017)
db = client.MyDiary

# 페이지 단위로 데이터 가져오기
page_no = 1
num_of_rows = 100  # 한 번에 가져올 데이터 개수
total_count = None
max_retries = 5
retry_delay = 5  # 초

while True:
    queryParams = '?' + urlencode({
        quote_plus('ServiceKey'): key,
        quote_plus('numOfRows'): num_of_rows,
        quote_plus('pageNo'): page_no,
        quote_plus('MobileOS'): 'ETC',
        quote_plus('MobileApp'): 'AppTest',
        quote_plus('_type'): 'json'
    })

    # 반복 시도 설정
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url + queryParams)
            response = urllib.request.urlopen(req, timeout=10)
            response_body = response.read()

            # 응답 본문 출력
            response_text = response_body.decode('utf-8')
            print(response_text)

            # 응답을 JSON 형식의 dict로 변환
            data = json.loads(response_text)

            # 전체 데이터 수 가져오기
            if total_count is None:
                total_count = data['response']['body']['totalCount']

            # MongoDB에 데이터 삽입
            items = data['response']['body']['items']['item']
            db.areaCode.insert_many(items)

            # 다음 페이지로 이동
            page_no += 1

            # 더 이상 데이터가 없으면 종료
            if len(items) < num_of_rows or page_no > (total_count // num_of_rows) + 1:
                break

            # 성공적으로 데이터를 가져왔으므로 반복 시도 루프 탈출
            break

        except urllib.error.URLError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            break

    # 더 이상 데이터가 없으면 종료
    if total_count is not None and page_no > (total_count // num_of_rows) + 1:
        break
