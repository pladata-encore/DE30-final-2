import urllib.request
from urllib.parse import urlencode, quote_plus
import json
import time
from pymongo import MongoClient

# MongoDB 연결 설정
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client.MyDiary
content_type_collection = db.contentTypeId

# 모든 code 값을 가져옴
content_types = content_type_collection.find({}, {"code": 1, "_id": 0})
content_type_ids = [item['code'] for item in content_types]

url = "http://apis.data.go.kr/B551011/KorService1/areaBasedList1"
key = "자신의 키를 입력하세요"

# 페이지 단위로 데이터 가져오기
num_of_rows =40  # 한번에 가져올 데이터 개수를 줄임
max_retries = 5
retry_delay = 5  # 초
timeout = 40  # 초

def get_last_page_no(collection_name):
    record = db.lastPage.find_one({"collection_name": collection_name})
    return record["page_no"] if record else 1

def update_last_page_no(collection_name, page_no):
    db.lastPage.update_one(
        {"collection_name": collection_name},
        {"$set": {"page_no": page_no}},
        upsert=True
    )

for content_type_id in content_type_ids:
    collection_name = f"areaBaseList{content_type_id}"
    page_no = get_last_page_no(collection_name)
    total_count = 0
    print(f"Starting to fetch data for contentTypeId {content_type_id} from page {page_no}")

    while True:
        queryParams = '?' + urlencode({
            quote_plus('ServiceKey'): key,
            quote_plus('numOfRows'): num_of_rows,
            quote_plus('pageNo'): page_no,
            quote_plus('MobileOS'): 'ETC',
            quote_plus('MobileApp'): 'AppTest',
            quote_plus('_type'): 'json',
            quote_plus('contentTypeId'): content_type_id
        })

        # 반복 시도 설정
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url + queryParams)
                response = urllib.request.urlopen(req, timeout=timeout)
                response_body = response.read()

                # 응답 본문 출력
                response_text = response_body.decode('utf-8')

                # 응답을 JSON 형식의 dict로 변환
                data = json.loads(response_text)

                # 전체 데이터 수 가져오기
                if page_no == 1:
                    total_count = data['response']['body']['totalCount']

                # MongoDB에 데이터 삽입
                items = data['response']['body']['items']['item']
                db[collection_name].insert_many(items)

                # 마지막으로 성공적으로 가져온 페이지 번호 업데이트
                update_last_page_no(collection_name, page_no)

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

        # 모든 데이터를 다 가져왔으면 루프 종료
        if total_count is not None and page_no > (total_count // num_of_rows) + 1:
            break
