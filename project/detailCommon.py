import urllib.request
from urllib.parse import urlencode, quote_plus
import json
from pymongo import MongoClient
import time

# API URL 및 키 설정
urls = "http://apis.data.go.kr/B551011/KorService1/detailCommon1"
key = "sn4p9/xq3HzvfZw7DjDo9gJBjru0dhT62DbDbJFDdiZEYPe2Lyio/NSLbeFkKw1Of4/P8G+dQdTBfr8m0OMoQA=="

# MongoDB 연결 설정
client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority',
                     27017)
db = client.MyDiary

# contentTypeId 리스트
contentTypeIds = [12, 14, 28, 38, 39]

# 이미 처리된 ID를 저장하는 컬렉션
processed_ids_collection = db['processed_ids']

# 각 contentTypeId에 대해 데이터 처리
for contentTypeId in contentTypeIds:
    # base_collection에서 contentId 가져오기
    base_collection_name = f"areaBaseList{contentTypeId}"
    base_collection = db[base_collection_name]

    areaBaseList = base_collection.find({}, {"contentid": 1, "_id": 0})
    areaBaseList_ids = [item['contentid'] for item in areaBaseList]

    # 각 contentId에 대해 API 호출 및 데이터 저장
    for content_id in areaBaseList_ids:
        # 이미 처리된 경우 건너뛰기
        if processed_ids_collection.find_one({"contentId": content_id, "contentTypeId": contentTypeId}):
            print(f"Skipping already processed contentId {content_id}")
            continue

        # API 요청 파라미터 설정
        params = {
            'MobileOS': 'ETC',
            'MobileApp': 'MobileApp',
            '_type': 'json',
            'defaultYN': 'Y',
            'contentId': content_id,
            'contentTypeId': contentTypeId,
            'numOfRows': 10,
            'pageNo': 1,
            'serviceKey': key
        }

        # URL 인코딩
        query_string = urlencode(params, quote_via=quote_plus)
        request_url = f"{urls}?{query_string}"

        retries = 3
        for attempt in range(retries):
            try:
                req = urllib.request.Request(request_url)
                response = urllib.request.urlopen(req, timeout=10)  # 요청 시간 초과를 10초로 설정
                status_code = response.getcode()

                if status_code == 200:
                    response_body = response.read().decode('utf-8')

                    if response_body:
                        print(f"Response Body for contentId {content_id}: {response_body}")
                        data = json.loads(response_body)

                        # 응답 데이터에서 원하는 정보 추출
                        if "response" in data and "body" in data["response"] and "items" in data["response"]["body"]:
                            items = data["response"]["body"]["items"]["item"]

                            # detailCommon{contentTypeId} 컬렉션에 데이터 저장
                            detail_collection_name = f"detailCommon{contentTypeId}"
                            detail_collection = db[detail_collection_name]
                            detail_collection.insert_many(items)

                            print(f"Stored {len(items)} items in {detail_collection_name} for contentId {content_id}")
                        else:
                            print(f"No items found in response for contentId {content_id}")

                        # 처리된 contentId 기록
                        processed_ids_collection.insert_one({"contentId": content_id, "contentTypeId": contentTypeId})

                        break  # 성공 시 반복 종료
                    else:
                        print(f"Empty response body for contentId {content_id}")

                else:
                    print(f"Request failed with status code {status_code} for contentId {content_id}")

            except urllib.error.URLError as e:
                print(f"URL error for contentId {content_id}: {e}")

            except urllib.error.HTTPError as e:
                print(f"HTTP error for contentId {content_id}: {e}")

            except json.JSONDecodeError as e:
                print(f"JSON decode error for contentId {content_id}: {e}")

            except Exception as e:
                print(f"Failed to process contentId {content_id}: {e}")

            # 요청 실패 시 백오프 후 재시도
            time.sleep(60)  # 60초 대기 후 재시도

        # 요청 사이의 지연 시간 설정 (API 호출 제한을 피하기 위해)
        time.sleep(5)