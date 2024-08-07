import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Load accommodation details and insert into MongoDB'

    def handle(self, *args, **kwargs):
        detail_url = "http://apis.data.go.kr/B551011/KorService1/detailIntro1"
        SERVICE_KEY = "+kSWY4C1LN3XmpqW6LZw0z16ojUYmI3etiqX/R9CpsEFwxASUxdZsoXfuGoDU0BVAmdMznsWODlPn3v6bQ335Q=="

        # MongoDB Atlas 연결 URI
        mongo_uri = "mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"
        client = MongoClient(mongo_uri)
        db = client['MyDiary']
        collection = db['accommodations']

        # MongoDB에서 모든 contentid 가져오기
        accommodations = list(collection.find({}, {'contentid': 1}))

        for accommodation in accommodations:
            content_id = accommodation.get('contentid')
            if content_id is None:
                continue

            params = {
                'MobileOS': 'ETC',
                'MobileApp': 'AppTest',
                'serviceKey': SERVICE_KEY,
                'contentId': content_id,
                'contentTypeId': '32',
                '_type': 'xml'
            }

            for attempt in range(3):  # 최대 3번 재시도
                try:
                    response = requests.get(detail_url, params=params, timeout=10)
                    response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
                    break
                except requests.exceptions.Timeout:
                    self.stdout.write(self.style.WARNING(f'Request timed out for contentid={content_id}, attempt={attempt + 1}'))
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f'Request failed for contentid={content_id}: {str(e)}'))
                    break
            else:
                self.stdout.write(self.style.ERROR(f'Failed to get data for contentid={content_id} after 3 attempts'))
                continue

            try:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                if items:
                    details = {child.tag: child.text for child in items[0]}
                    collection.update_one(
                        {'contentid': content_id},
                        {'$set': details}
                    )
                    self.stdout.write(self.style.SUCCESS(f'Updated details for contentid {content_id}'))
                else:
                    self.stdout.write(self.style.WARNING(f'No details found for contentid {content_id}'))
            except ET.ParseError:
                self.stdout.write(self.style.ERROR(f'Failed to parse XML for contentid {content_id}'))
                self.stdout.write(self.style.ERROR(f'Response content: {response.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred for contentid {content_id}: {str(e)}'))
