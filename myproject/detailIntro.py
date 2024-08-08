import urllib.request
from urllib.parse import urlencode, quote_plus
import json
from pymongo import MongoClient
import time

client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority', 27017)
db = client.MyDiary

# API URL 및 키 설정
urls = "http://apis.data.go.kr/B551011/KorService1/detailCommon1"
key = "메롱"

contentTypeIds = [12, 14, 28, 38, 39]

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
            'contentId': content_id,
            'contentTypeId': contentTypeId,
            'numOfRows': 10,
            'pageNo': 1,
            'serviceKey': key
        }

        # URL 인코딩
        query_string = urlencode(params, quote_via=quote_plus)
        request_url = f"{urls}?{query_string}"

        try:
            # API 요청 및 응답 데이터 읽기
            response = urllib.request.urlopen(request_url)
            response_body = response.read()
            data = json.loads(response_body)

            # 응답 데이터에서 원하는 정보 추출
            if "response" in data and "body" in data["response"] and "items" in data["response"]["body"]:
                items = data["response"]["body"]["items"]["item"]

                # detailCommon{contentTypeId} 컬렉션에 데이터 저장
                detail_collection_name = f"detailIntro{contentTypeId}"
                detail_collection = db[detail_collection_name]
                if isinstance(items, list):
                    detail_collection.insert_many(items)
                else:
                    detail_collection.insert_one(items)

                # 처리된 contentId 기록
                processed_ids_collection.insert_one({"contentId": content_id, "contentTypeId": contentTypeId})

                print(f"Stored {len(items)} items in {detail_collection_name} for contentId {content_id}")

        except Exception as e:
            print(f"Failed to process contentId {content_id}: {e}")

        # 요청 사이의 지연 시간 설정 (API 호출 제한을 피하기 위해)
        time.sleep(5)
