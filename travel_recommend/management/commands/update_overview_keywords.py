import os
import logging
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 한국어 불용어 리스트
korean_stopwords = [
    "가", "의", "이", "은", "는", "을", "를", "에", "와", "과", "도", "으로", "로", "부터", "까지", "에", "에게", "에서", "의", "인",
    "라", "나", "마", "자", "거", "서", "니", "죠", "고", "데", "든", "란", "수", "곳", "층", "개", "등", "전", "후", "점",
    "그", "그녀", "그들", "저", "나", "너", "우리", "너희", "당신", "이것", "저것", "그것", "뭐", "뭔가", "무엇", "어디", "누구", "자신", "서로",
    "안", "못", "잘", "매우", "너무", "정말", "아주", "좀", "조금", "다시", "또", "항상", "결국", "그냥", "잘", "그렇지만", "그러나", "더", "가장",
    "아직", "만약", "이미", "마치", "지금", "빨리", "천천히", "결코", "물론", "꼭", "한번", "때문에", "따라서", "대신", "만큼", "그리", "그래도", "다만",
    "하다", "되다", "이다", "있다", "없다", "되다", "않다", "이다", "아니다", "같다", "보다", "싶다", "좋다", "많다", "적다", "크다", "작다", "알다",
    "모르다", "싶다", "생각하다", "지나다", "필요하다", "원하다", "오다", "가다", "말하다", "주다", "받다", "생기다", "사용하다", "어울리다", "마시다", "먹다",
    "하나", "둘", "셋", "넷", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "몇", "몇몇", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구", "십",
    "백", "천", "만", "억",
    "오늘", "내일", "어제", "그제", "현재", "지금", "이제", "곧", "지금", "당장", "금방", "동안", "앞으로", "앞", "뒤", "전에", "후에", "다음", "이번",
    "마지막", "처음", "중간", "가운데", "초", "분", "시간", "주", "개월", "년",
    "그리고", "그러면", "그러나", "하지만", "그런데", "그래서", "또한", "게다가", "따라서", "때문에", "그러므로", "그러니까", "요즘", "바로", "때문에",
    "정도", "인한", "위한", "이러한", "그러한", "저러한", "모든", "어떤", "각각", "각자", "누구나", "여러", "모든", "어느", "그때", "어느덧"
]

class Command(BaseCommand):
    help = 'Update keywords for places and accommodations in MongoDB'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Connecting to MongoDB...'))
        # client = MongoClient('mongodb://127.0.0.1:27017/')
        # db = client['MyDiary']
        from django.conf import settings
        db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

        collections = [
            'areaBaseList12'
        ]

        for collection_name in collections:
            self.stdout.write(self.style.SUCCESS(f'Processing collection: {collection_name}'))
            collection = db[collection_name]
            documents = list(collection.find({"overview": {"$exists": True}}))

            if not documents:
                self.stdout.write(self.style.WARNING(f'No documents with overview found in {collection_name}'))
                continue

            for doc in documents:
                content_id = doc["contentid"]
                overview = doc.get("overview", "")

                if not overview:
                    self.stdout.write(self.style.WARNING(f'Skipping document with no overview: {content_id}'))
                    continue

                # 키워드 추출
                self.stdout.write(self.style.SUCCESS(f'Extracting keywords for document: {content_id}'))
                keywords = self.extract_keywords([overview], top_n=10)
                if keywords:
                    self.stdout.write(self.style.SUCCESS(f'Keywords extracted for document: {content_id}'))
                else:
                    self.stdout.write(self.style.WARNING(f'No keywords extracted for document: {content_id}'))

                # 컬렉션 업데이트
                collection.update_one(
                    {'contentid': content_id},
                    {'$set': {'keywords': keywords[0] if keywords else []}}
                )

        self.stdout.write(self.style.SUCCESS('Keywords updated successfully in MongoDB'))

    def extract_keywords(self, texts, top_n=10):
        okt = Okt()
        processed_texts = [" ".join([word for word in okt.nouns(text) if word not in korean_stopwords]) for text in texts]
        self.stdout.write(self.style.SUCCESS(f'Processed Texts: {processed_texts}'))

        if not any(processed_texts):  # Check if all processed texts are empty
            self.stdout.write(self.style.ERROR('All processed texts are empty. Skipping TF-IDF keyword extraction.'))
            return [[]] * len(texts)

        tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(processed_texts)
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'Error in TF-IDF vectorization: {e}'))
            return [[]] * len(texts)

        feature_names = tfidf_vectorizer.get_feature_names_out()

        keywords = []
        for i in range(tfidf_matrix.shape[0]):
            tfidf_scores = tfidf_matrix[i].toarray().flatten()
            top_keywords_idx = tfidf_scores.argsort()[-top_n:]
            top_keywords = [feature_names[idx] for idx in top_keywords_idx]
            keywords.append(top_keywords)
        return keywords


if __name__ == "__main__":
    command = Command()
    command.handle()
    logging.info("All processing completed successfully.")