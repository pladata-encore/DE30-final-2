import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Load tourspace overview data from Open API and update MongoDB'

    def handle(self, *args, **kwargs):
        # MongoDB 연결 설정
        mongo_uri = "mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"
        client = MongoClient(mongo_uri)
        db = client['MyDiary']
        collection = db['areaBaseList28']

        # API 설정
        API_URL = "http://apis.data.go.kr/B551011/KorService1/detailCommon1"
        SERVICE_KEY = "Sb/v0Bw7bSK6dHNb77i4CJ7crREM7ge1TXIk6MtE2a299gX7LgWJuglX4z2p9tmLTRRtjbjkpOIxRR+OtlK1MA=="

        params = {
            'MobileOS': 'ETC',
            'MobileApp': 'MobileApp',
            '_type': 'xml',
            'contentTypeId': 28,
            'overviewYN': 'Y',
            'serviceKey': SERVICE_KEY,
            'numOfRows': 10,  # 한 번에 가져올 데이터 수
            'pageNo': 1  # 페이지 번호 초기값
        }

        # 컬렉션에서 contentId를 가져와서 API 호출
        accommodations = collection.find({}, {"contentid": 1})
        for accommodation in accommodations:
            content_id = accommodation['contentid']
            params['contentId'] = content_id

            retry_attempts = 3  # 최대 재시도 횟수
            for attempt in range(retry_attempts):
                try:
                    response = requests.get(API_URL, params=params, timeout=10)  # 요청 타임아웃 설정

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
                            break  # 성공적으로 데이터를 가져왔으므로 루프 종료
                        except ET.ParseError:
                            self.stdout.write(self.style.ERROR(f"Failed to parse XML for contentid {content_id}"))
                            break
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to fetch data for contentid {content_id}: {response.status_code}"))
                        break
                except requests.exceptions.Timeout:
                    self.stdout.write(self.style.ERROR(f"Request timed out for contentid {content_id}, attempt {attempt + 1}/{retry_attempts}"))
                    if attempt + 1 < retry_attempts:
                        time.sleep(5)  # 재시도 전 5초 대기
                    else:
                        self.stdout.write(self.style.ERROR(f"Max retry attempts reached for contentid {content_id}"))
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"Request failed for contentid {content_id}: {e}"))
                    break

        self.stdout.write(self.style.SUCCESS("Finished updating overviews"))