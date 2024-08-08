import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Load tourspace overview data from Open API and update MongoDB'

    def handle(self, *args, **kwargs):
        # MongoDB 연결 설정
        client = MongoClient('mongodb://127.0.0.1:27017/')
        db = client['MyDiary']
        collection = db['areaBaseList39']

        # API 설정
        API_URL = "http://apis.data.go.kr/B551011/KorService1/detailCommon1"
        service_keys = [
            "Sb/v0Bw7bSK6dHNb77i4CJ7crREM7ge1TXIk6MtE2a299gX7LgWJuglX4z2p9tmLTRRtjbjkpOIxRR+OtlK1MA==",
            "+kSWY4C1LN3XmpqW6LZw0z16ojUYmI3etiqX/R9CpsEFwxASUxdZsoXfuGoDU0BVAmdMznsWODlPn3v6bQ335Q==",
            "cKgW9OjLbXENzsZJvmEUpJWalpOy3KRgzL50EuJDsV2ZzSuDtvz9bk00ugl96WdpbO3N/P2zuqAO+SCXksBByg==",
            # 추가 서비스키를 여기에 추가
        ]

        params = {
            'MobileOS': 'ETC',
            'MobileApp': 'MobileApp',
            '_type': 'xml',
            'contentTypeId': 39,
            'overviewYN': 'Y',
            'numOfRows': 10,  # 한 번에 가져올 데이터 수
            'pageNo': 1  # 페이지 번호 초기값
        }

        # 컬렉션에서 contentId를 가져와서 API 호출
        accommodations = collection.find({}, {"contentid": 1})
        service_key_index = 0  # 서비스키 인덱스 초기값

        for accommodation in accommodations:
            content_id = accommodation['contentid']
            params['contentId'] = content_id
            params['serviceKey'] = service_keys[service_key_index]

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

            # 다음 요청 시 서비스키 순환
            service_key_index = (service_key_index + 1) % len(service_keys)

        self.stdout.write(self.style.SUCCESS("Finished updating overviews"))