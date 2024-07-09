import urllib.request
from urllib.parse import urlencode, quote_plus
import json
import time
from pymongo import MongoClient

# MongoDB 연결 설정
client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority',
                     27017)
db = client.MyDiary

url = "http://apis.data.go.kr/B551011/KorService1/detailIntro1"
key = "sn4p9/xq3HzvfZw7DjDo9gJBjru0dhT62DbDbJFDdiZEYPe2Lyio/NSLbeFkKw1Of4/P8G+dQdTBfr8m0OMoQA=="

# 페이지 단위로 데이터 가져오기
num_of_rows = 100  # 한번에 가져올 데이터 개수를 줄임
max_retries = 5
retry_delay = 5  # 초
timeout = 10  # 초

# 처리할 컬렉션 이름 목록
collection_names = ["areaBaseList12", "areaBaseList14", "areaBaseList28", "areaBaseList38", "areaBaseList39"]


def get_last_page_no(collection_name, content_id):
    record = db.lastPage.find_one({"collection_name": collection_name, "content_id": content_id})
    return record["page_no"] if record else 1


def update_last_page_no(collection_name, content_id, page_no):
    db.lastPage.update_one(
        {"collection_name": collection_name, "content_id": content_id},
        {"$set": {"page_no": page_no}},
        upsert=True
    )


def fetch_data_for_collection(collection_name):
    collection = db[collection_name]

    # 모든 code 값을 가져옴
    areaBaseList = collection.find({}, {"contentid": 1, "_id": 0})
    areaBaseList_ids = [item['contentid'] for item in areaBaseList]

    for areaBaseList_id in areaBaseList_ids:
        page_no = get_last_page_no(collection_name, areaBaseList_id)
        total_count = 0
        print(
            f"Starting to fetch data for contentId {areaBaseList_id} from page {page_no} in collection {collection_name}")

        while True:
            queryParams = '?' + urlencode({
                quote_plus('ServiceKey'): key,
                quote_plus('numOfRows'): num_of_rows,
                quote_plus('pageNo'): page_no,
                quote_plus('MobileOS'): 'ETC',
                quote_plus('MobileApp'): 'AppTest',
                quote_plus('_type'): 'json',
                quote_plus('contentId'): areaBaseList_id,
                quote_plus('contentTypeId'): int(collection_name[-2:])  # 예: areaBaseList14 -> contentTypeId 14
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
                    db["detailInfo" + collection_name[-2:]].insert_many(items)

                    # 마지막으로 성공적으로 가져온 페이지 번호 업데이트
                    update_last_page_no(collection_name, areaBaseList_id, page_no)

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


def main():
    while True:
        try:
            for collection_name in collection_names:
                fetch_data_for_collection(collection_name)
        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Attempting to restart in 60 seconds...")
            time.sleep(60)  # 60초 후 재시도

        answer = input("Would you like to restart the data fetching process? (y/n): ").lower()
        if answer != 'y':
            print("Exiting...")
            break


if __name__ == "__main__":
    main()