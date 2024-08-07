import requests
from pymongo import MongoClient
from django.core.management.base import BaseCommand
from urllib.parse import urlencode


class Command(BaseCommand):
    help = 'Load category codes and insert into MongoDB'

    def handle(self, *args, **kwargs):
        base_url = "http://apis.data.go.kr/B551011/KorService1/categoryCode1"
        service_key = "Sb/v0Bw7bSK6dHNb77i4CJ7crREM7ge1TXIk6MtE2a299gX7LgWJuglX4z2p9tmLTRRtjbjkpOIxRR+OtlK1MA=="

        params = {
            'MobileOS': 'ETC',
            'MobileApp': 'MobileApp',
            'contentTypeId': '32',  # 숙박
            '_type': 'json',
            'serviceKey': service_key
        }

        def get_category_codes(cat1=None, cat2=None):
            if cat1:
                params['cat1'] = cat1
            if cat2:
                params['cat2'] = cat2

            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
                    return data['response']['body']['items']['item']
                else:
                    print(f"Unexpected response format: {data}")
                    return []
            else:
                print(f"API 호출 실패: {response.status_code}")
                print("응답 텍스트:", response.text)
                return []

        all_cat1 = []
        all_cat2 = []
        all_cat3 = []

        # 대분류 코드 가져오기
        cat1_codes = get_category_codes()
        for cat1 in cat1_codes:
            cat1_code = cat1['code']
            all_cat1.append(cat1)

            # 중분류 코드 가져오기
            cat2_codes = get_category_codes(cat1_code)
            for cat2 in cat2_codes:
                cat2_code = cat2['code']
                cat2['parent_code'] = cat1_code
                all_cat2.append(cat2)

                # 소분류 코드 가져오기
                cat3_codes = get_category_codes(cat1_code, cat2_code)
                for cat3 in cat3_codes:
                    cat3['parent_code'] = cat2_code
                    all_cat3.append(cat3)

        # MongoDB Atlas 연결 URI
        mongo_uri = "mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"

        # MongoDB 클라이언트 생성
        client = MongoClient(mongo_uri)

        # 데이터베이스와 컬렉션 선택
        db = client['MyDiary']
        cat1_collection = db['acc_cat1_codes']
        cat2_collection = db['acc_cat2_codes']
        cat3_collection = db['acc_cat3_codes']

        # 기존 컬렉션 삭제 (있을 경우)
        cat1_collection.drop()
        cat2_collection.drop()
        cat3_collection.drop()

        # 데이터 삽입
        if all_cat1:
            cat1_collection.insert_many(all_cat1)
        if all_cat2:
            cat2_collection.insert_many(all_cat2)
        if all_cat3:
            cat3_collection.insert_many(all_cat3)

        self.stdout.write(self.style.SUCCESS('Category codes inserted successfully!'))