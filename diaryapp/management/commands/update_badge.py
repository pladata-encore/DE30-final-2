from django.conf import settings
from pymongo import MongoClient
from django.core.management.base import BaseCommand
import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import base64


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        db = client[settings.DATABASES['default']['NAME']]
        area_base_list_collection = db['areaBaseList']
        badge_collection = db['badge']

        # Change Stream 설정 및 감시
        pipeline = [{'$match': {'operationType': 'insert'}}]

        with area_base_list_collection.watch(pipeline) as stream:
            for change in stream:
                document = change['fullDocument']
                if 'firstimage' in document and document['firstimage'].startswith('http'):
                    self.save_to_db(document, badge_collection)

    # MongoDB에 저장할 함수
    def save_to_db(self, document, badge_collection):
        areaBaseList_id = document['_id']
        title = document['title']
        firstimage_url = document['firstimage']

        # 이미지 로드 및 처리
        cartoon_image = self.process_image(firstimage_url)

        # 이미지를 base64로 인코딩
        buffered = BytesIO()
        Image.fromarray(cartoon_image).save(buffered, format="PNG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # MongoDB에 저장
        badge_collection.insert_one({"areaBaseList_id": areaBaseList_id, "title": title, "badge": encoded_image})

    # 이미지 로드 및 처리 함수
    def process_image(self, image_url):
        response = requests.get(image_url)
        image_data = BytesIO(response.content)
        image = Image.open(image_data).convert('RGB')

        # 이미지 스타일 변경
        cartoon_image = self.cartoonify(np.array(image))

        # 이미지 보정
        adjusted_image = self.adjust_image(cartoon_image)

        return adjusted_image

    # 이미지 스타일 변경 함수
    def cartoonify(self, image):

        height, width, _ = image.shape

        # 사이즈가 큰 이미지 조절
        if width > 1000:
            new_width = 1000
            new_height = int(height * (new_width / width))
            image = cv2.resize(image, (new_width, new_height))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 9)
        edges = cv2.Laplacian(gray, cv2.CV_8U, ksize=5)
        edges = 255 - edges
        edges = cv2.threshold(edges, 50, 255, cv2.THRESH_BINARY)[1]
        color = cv2.bilateralFilter(image, 5, 100, 100)
        data = np.float32(color).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, palette = cv2.kmeans(data, 7, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        quantized = palette[labels.flatten()]
        quantized = quantized.reshape(color.shape).astype(np.uint8)
        cartoon = cv2.bitwise_and(quantized, quantized, mask=edges)
        return cartoon

    # 이미지 보정 함수
    def adjust_image(self, image):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv_image)
        s = cv2.multiply(s, 5)
        s = np.clip(s, 0, 255).astype(np.uint8)
        hsv_image = cv2.merge([h, s, v])
        image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
        image = cv2.convertScaleAbs(image, alpha=1, beta=7)
        image = cv2.convertScaleAbs(image, alpha=1.2, beta=0)
        return image



