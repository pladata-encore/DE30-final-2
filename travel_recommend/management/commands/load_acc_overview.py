import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Load accommodation overview data from Open API and update MongoDB'

    def handle(self, *args, **kwargs):
        # MongoDB 연결 설정
        client = MongoClient('mongodb://127.0.0.1:27017/')
        db = client['MyDiary']
        collection = db['accommodations']

        # API 설정
        API_URL = "http://apis.data.go.kr/B551011/KorService1/detailCommon1"
        SERVICE_KEY = "cKgW9OjLbXENzsZJvmEUpJWalpOy3KRgzL50EuJDsV2ZzSuDtvz9bk00ugl96WdpbO3N/P2zuqAO+SCXksBByg=="

        params = {
            'MobileOS': 'ETC',
            'MobileApp': 'AppTest',
            '_type': 'xml',
            'contentTypeId': 32,
            'overviewYN': 'Y',
            'serviceKey': SERVICE_KEY,
            'numOfRows': 100,  # 한 번에 가져올 데이터 수
            'pageNo': 1  # 페이지 번호 초기값
        }

        # 컬렉션에서 contentId를 가져와서 API 호출
        accommodations = collection.find({}, {"contentid": 1})
        for accommodation in accommodations:
            content_id = accommodation['contentid']
            params['contentId'] = content_id

            response = requests.get(API_URL, params=params)

            if response.status_code == 200:
                try:
                    # 응답 출력 (디버깅용)
                    print(response.content.decode('utf-8'))

                    root = ET.fromstring(response.content)
                    items = root.findall('.//item')
                    if items:
                        overview = items[0].find('overview').text if items[0].find('overview') is not None else "No overview available"
                        collection.update_one(
                            {'contentid': content_id},
                            {'$set': {'overview': overview}}
                        )
                        self.stdout.write(self.style.SUCCESS(f"Updated contentid {content_id} with overview"))
                    else:
                        self.stdout.write(self.style.WARNING(f"No items found for contentid {content_id}"))
                except ET.ParseError:
                    self.stdout.write(self.style.ERROR(f"Failed to parse XML for contentid {content_id}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to fetch data for contentid {content_id}: {response.status_code}"))

        self.stdout.write(self.style.SUCCESS("Finished updating overviews"))

