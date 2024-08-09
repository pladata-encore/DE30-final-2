import requests
import pandas as pd
from pymongo import MongoClient
from django.core.management.base import BaseCommand
from urllib.parse import urlencode

class Command(BaseCommand):
    help = 'Load data from Open API and insert into MongoDB'

    def handle(self, *args, **kwargs):
        API_URL = "http://apis.data.go.kr/B551011/KorService1/searchStay1"
        SERVICE_KEY = "Sb/v0Bw7bSK6dHNb77i4CJ7crREM7ge1TXIk6MtE2a299gX7LgWJuglX4z2p9tmLTRRtjbjkpOIxRR+OtlK1MA=="

        params = {
            'numOfRows': 100,
            'pageNo': 1,
            'MobileOS': 'ETC',
            'MobileApp': 'AppTest',
            '_type': 'json',
            'listYN': 'Y',
            'arrange': 'A',
            'serviceKey': SERVICE_KEY
        }

        # 초기 API 호출
        response = requests.get(API_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            total_count = data['response']['body']['totalCount']
            num_of_rows = params['numOfRows']
            total_pages = (total_count // num_of_rows) + (1 if total_count % num_of_rows > 0 else 0)
            all_accommodations = data['response']['body']['items']['item']

            # 페이지를 순차적으로 호출하여 모든 데이터를 가져옴
            for page in range(2, total_pages + 1):
                params['pageNo'] = page
                response = requests.get(API_URL, params=params)
                if response.status_code == 200:
                    data = response.json()
                    accommodations = data['response']['body']['items']['item']
                    all_accommodations.extend(accommodations)

            # MongoDB Atlas 연결 URI
            # MongoDB 클라이언트 생성
            # client = MongoClient('mongodb://127.0.0.1:27017/')
            # 데이터베이스와 컬렉션 선택
            # db = client['MyDiary']
            from django.conf import settings
            db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

            collection = db['accommodations']

            # 기존 컬렉션 삭제 (있을 경우)
            collection.drop()

            # 데이터 삽입
            collection.insert_many(all_accommodations)

            self.stdout.write(self.style.SUCCESS('Data inserted successfully!'))

        else:
            self.stdout.write(self.style.ERROR(f"API 호출 실패: {response.status_code}"))
            self.stdout.write(self.style.ERROR(f"응답 텍스트: {response.text}"))