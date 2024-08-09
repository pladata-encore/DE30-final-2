import os
import json
import logging
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from travel_recommend.knusl import KnuSL

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

base_dir = os.path.dirname(os.path.abspath(__file__))
stopwords_path = os.path.join(base_dir, 'stopwords-ko.txt')

with open(stopwords_path, 'r', encoding='utf-8') as file:
    korean_stopwords = file.read().splitlines()

# 한국어 불용어 리스트
user_stopwords = [
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

# 불용어 리스트 합치기 (중복은 제거)
combined_stopwords = list(set(korean_stopwords + user_stopwords))

class Command(BaseCommand):
    help = 'Update sentiment scores and keywords for reviews in MongoDB'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'SentiWord_info.json')
        knusl = KnuSL(path=json_path)
        self.update_reviews_with_sentiment_scores(knusl)

    def update_reviews_with_sentiment_scores(self, knusl):
        logging.info('Connecting to MongoDB...')
        # client = MongoClient('mongodb://127.0.0.1:27017/')
        # db = client['MyDiary']
        from django.conf import settings
        db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

        # 카테고리와 컬렉션 매핑
        categories = ['accommodations', 'areaBaseList14', 'areaBaseList39']

        for category in categories:
            reviews_collection = db[f'{category}_reviews']
            logging.info(f'Processing collection: {category}_reviews')

            reviews = list(reviews_collection.find())
            logging.info(f'Found {len(reviews)} reviews in {category}_reviews collection.')

            for review in tqdm(reviews, desc=f'Processing {category} reviews'):
                kospacing_review = review.get('kospacing_reviews', '')
                if not isinstance(kospacing_review, str) or not kospacing_review:
                    logging.warning(f'Skipping empty or invalid review: {review["_id"]}')
                    continue

                # 감성 점수 계산
                score = knusl.get_sentence_score(kospacing_review)
                normalized_score = self.convert_to_10_point_scale(score)
                logging.debug(f'Review ID: {review["_id"]}, Score: {score}, Normalized Score: {normalized_score}')

                # 키워드 추출
                keywords = self.extract_keywords([kospacing_review], top_n=10)
                if keywords:
                    logging.debug(f'Review ID: {review["_id"]}, Keywords: {keywords[0]}')
                else:
                    logging.debug(f'Review ID: {review["_id"]}, No keywords extracted')

                # 리뷰 컬렉션 업데이트
                result = reviews_collection.update_one(
                    {'_id': review['_id']},
                    {'$set': {'keywords': keywords[0] if keywords else [], 'sentiment_score': normalized_score}}
                )
                logging.debug(f'Update Result: {result.raw_result}')

        logging.info("Keywords and sentiment scores updated successfully in MongoDB")

    def extract_keywords(self, texts, top_n=10):
        okt = Okt()
        processed_texts = [" ".join(okt.nouns(text)) for text in texts]
        logging.debug(f'Processed Texts: {processed_texts}')

        if not any(processed_texts):  # Check if all processed texts are empty
            logging.error('All processed texts are empty. Skipping TF-IDF keyword extraction.')
            return [[]] * len(texts)

        tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words=combined_stopwords)
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(processed_texts)
        except ValueError as e:
            logging.error(f'Error in TF-IDF vectorization: {e}')
            return [[]] * len(texts)

        feature_names = tfidf_vectorizer.get_feature_names_out()

        keywords = []
        for i in range(tfidf_matrix.shape[0]):
            tfidf_scores = tfidf_matrix[i].toarray().flatten()
            top_keywords_idx = tfidf_scores.argsort()[-top_n:]
            top_keywords = [feature_names[idx] for idx in top_keywords_idx]
            keywords.append(top_keywords)
        return keywords

    def convert_to_10_point_scale(self, score, min_score=-10, max_score=10):
        return ((score - min_score) / (max_score - min_score)) * 10


if __name__ == "__main__":
    command = Command()
    command.handle()
    logging.info("All processing completed successfully.")