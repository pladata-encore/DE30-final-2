import pymongo
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel
import numpy as np
import pandas as pd
import random
import math
import os
from konlpy.tag import Komoran
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# MongoDM 클라이언트 설정
client = pymongo.MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority')
db = client['MyDiary']

# Komoran 및 Word2Vec 모델 로드
komoran = Komoran()
model_path = os.path.join(os.path.dirname(__file__), "models", "word2vec_model2.model")
if os.path.exists(model_path):
    model = Word2Vec.load(model_path)
else:
    raise FileNotFoundError(f"Model file not found at {model_path}")

# 사용자 여행 취향 입력 정보
class UserInput(BaseModel):
    region: str
    subregion: str
    start_date: str
    end_date: str
    pets_allowed: str
    pet_size: str
    food_preference: List[str]
    tour_type: List[str]
    accommodation_type: List[str]
    travel_preference: List[str]


# 숙소 cat3 코드 동적으로 가져오는 함수
def get_accommodation_codes():
    codes = db.cat3_codes.find({"parent_code": "B0201"})
    accommodation_codes = {code['name']: code['code'] for code in codes}
    return accommodation_codes

# 사용자 입력을 모델에 사용할 수 있도록 word2vec 변환
def get_average_word2vec(tokens, model):
    valid_tokens = [token for token in tokens if token in model.wv]
    if not valid_tokens:
        return np.zeros(model.vector_size)
    return np.mean(model.wv[valid_tokens], axis=0)

# 사용자가 입력을 텍스트로 받아 Komoran을 이용해 명사, 형용사 추출, 학습된 모델을 이용해 벡터로 변환
def process_user_input(user_input):
    tokens = komoran.pos(user_input)
    tokens = [word for word, pos in tokens if pos in ['NA','NF','NV','NNG', 'NNP', 'VA']]
    # 학습된 word2vec 모델로 사용자 입력을 벡터로 변환
    vector = get_average_word2vec(tokens, model)
    return vector

def filter_unwanted_sites(df):
    camping_codes = ['A03021700']
    foreign_keywords = ["외국인", "외국인만", "외국인 전용", "foreigners only"]
    mask_camping = df['cat3'].apply(lambda x: x not in camping_codes)
    mask_foreign = df['overview'].apply(lambda x: not any(keyword in x for keyword in foreign_keywords))
    return df[mask_camping & mask_foreign]

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(float, [lon1, lat1, lon2, lat2]) # 문자열 -> 실수 변환
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    km = 6371 * c
    return km

def recommend(user_input, df, day):
    logger.info(f"Day {day} recommendation process started")

    preference = (
        user_input.get('food_preference', []) +
        user_input.get('tour_type', []) +
        user_input.get('accommodation_type', []) +
        user_input.get('travel_preference', [])
    )
    user_text = " ".join(preference)

    user_vector = process_user_input(user_text)
    logger.info(f"User vector calculated: {user_vector}")

    df['content_vector'] = df['text'].apply(lambda x: get_average_word2vec(process_user_input(x), model))
    logger.info(f"Content vectors calculated for DataFrame")

    df['similarity'] = df['content_vector'].apply(
        lambda x: cosine_similarity([user_vector], [x]).flatten()[0] if np.any(x) else 0
    )
    df['final_score'] = df['similarity'] * 0.7 + df['normalized_sentiment_score'] * 0.3
    df_sorted = df.sort_values(by='final_score', ascending=False)

    accommodation_codes = get_accommodation_codes()
    accommodation_type = user_input.get('accommodation_type', [])
    accommodation_codes_filtered = [accommodation_codes[atype] for atype in accommodation_type]

    # 추천에 필요하지 않은 유형의 데이터 필터링
    df_sorted = filter_unwanted_sites(df_sorted)
    logger.info(f"Unwanted sites filtered")

    # 숙소 추천 로직
    recommended_accommodations = df_sorted[(df_sorted['cat3'].isin(accommodation_codes_filtered)) &
                                         (df_sorted['areacode'] == user_input['region']) &
                                         (df_sorted['sigungucode'] == user_input['subregion'])]
    if recommended_accommodations.empty:
        recommended_accommodations = df_sorted[(df_sorted['contenttypeid'] == '32') &
                                             (df_sorted['areacode'] == user_input['region']) &
                                             (df_sorted['sigungucode'] == user_input['subregion'])]
        if not recommended_accommodations.empty:
            recommended_accommodations = recommended_accommodations.sample(n=1, random_state=random.randint(1, 1000))
    else:
        recommended_accommodations = recommended_accommodations.sample(n=1, random_state=random.randint(1, 1000))

    if recommended_accommodations.empty:
        return []

    selected_accommodation = recommended_accommodations.iloc[0]

    accommodation_text = user_input.get('accommodation_preference', '')
    accommodation_vector = process_user_input(accommodation_text)

    recommended_accommodations['accommodation_similarity'] = recommended_accommodations['content_vector'].apply(
        lambda x: cosine_similarity([accommodation_vector], [x]).flatten()[0] if np.any(x) else 0)
    recommended_accommodations = recommended_accommodations.sort_values(by='accommodation_similarity', ascending=False)

    if not recommended_accommodations.empty:
        selected_accommodation = recommended_accommodations.iloc[0]

    # 관광지 컬렉션별로 세분화하여 처리
    tour_collections = {
        'tour_space': df_sorted[(df_sorted['contenttypeid'] == '12') &
                                (df_sorted['areacode'] == user_input['region']) &
                                (df_sorted['sigungucode'] == user_input['subregion'])],
        'cultural_facilities': df_sorted[(df_sorted['contenttypeid'] == '14') &
                                         (df_sorted['areacode'] == user_input['region']) &
                                         (df_sorted['sigungucode'] == user_input['subregion'])],
        'leisure_spots': df_sorted[(df_sorted['contenttypeid'] == '28') &
                                   (df_sorted['areacode'] == user_input['region']) &
                                   (df_sorted['sigungucode'] == user_input['subregion'])],
        'shopping_facilities': df_sorted[(df_sorted['contenttypeid'] == '38') &
                                         (df_sorted['areacode'] == user_input['region']) &
                                         (df_sorted['sigungucode'] == user_input['subregion'])]
    }

    recommendations = []

    # 관광지 추천 로직
    for collection_name, collection_df in tour_collections.items():
        if not collection_df.empty:
            preference_text = " ".join(user_input.get('tour_type', []))
            preference_tokens = process_user_input(preference_text)
            preference_vector = get_average_word2vec(preference_tokens, model)

            collection_df['similarity'] = collection_df['content_vector'].apply(
                lambda x: cosine_similarity([preference_vector], [x]).flatten()[0] if np.any(x) else 0)
            collection_df = collection_df.sort_values(by='similarity', ascending=False).head(2)  # 각 컬렉션에서 상위 2개씩 추천(baseline) -> 이후에 로직 수정하기
            recommendations.append(collection_df)

    recommended_tourist_spots = pd.concat(recommendations)
    logger.info(f"Tourist spots recommended")

    # 식당 추천 로직
    recommended_restaurants = df_sorted[(df_sorted['contenttypeid'] == '39') &
                                        (df_sorted['areacode'] == user_input['region']) &
                                        (df_sorted['sigungucode'] == user_input['subregion'])]

    food_preference_text = " ".join(user_input.get('food_preference', []))
    food_preference_vector = process_user_input(food_preference_text)

    if not recommended_restaurants.empty:
        recommended_restaurants['food_similarity'] = recommended_restaurants['content_vector'].apply(
            lambda x: cosine_similarity([food_preference_vector], [x]).flatten()[0] if np.any(x) else 0)
        recommended_restaurants = recommended_restaurants.sort_values(by='food_similarity', ascending=False).head(3)

    tour_preference_text = " ".join(user_input.get('tour_type', []))
    tour_preference_vector = process_user_input(tour_preference_text)

    if not recommended_tourist_spots.empty:
        recommended_tourist_spots['tour_similarity'] = recommended_tourist_spots['content_vector'].apply(
            lambda x: cosine_similarity([tour_preference_vector], [x]).flatten()[0] if np.any(x) else 0)
        recommended_tourist_spots = recommended_tourist_spots.sort_values(by='tour_similarity', ascending=False).head(4)

    if recommended_restaurants.empty and recommended_tourist_spots.empty:
        return [selected_accommodation.to_dict()]

    accommodation_location = (float(selected_accommodation['mapx']), float(selected_accommodation['mapy']))

    recommended_restaurants['distance'] = recommended_restaurants.apply(
        lambda x: haversine(accommodation_location[1], accommodation_location[0], float(x['mapx']), float(x['mapy'])),
        axis=1
    )
    recommended_restaurants = recommended_restaurants.sort_values(by=['distance', 'final_score']).head(3)

    recommended_tourist_spots['distance'] = recommended_tourist_spots.apply(
        lambda x: haversine(accommodation_location[1], accommodation_location[0], float(x['mapx']), float(x['mapy'])),
        axis=1
    )
    recommended_tourist_spots = recommended_tourist_spots.sort_values(by=['distance','final_score']).head(4)

    recommendations = pd.concat([recommended_restaurants, recommended_tourist_spots])
    recommendations = recommendations[['contentid','title','mapx','mapy','final_score']].to_dict(orient='records')

    recommendations.insert(0, selected_accommodation.to_dict())

    logger.info(f"Day {day} recommendation process completed")
    return recommendations


@app.post("/recommend")
async def recommend_schedule(user_input: UserInput, request: Request):
    try:
        logger.info(f"User input received: {user_input}")

        # 입력 받은 날짜를 기반으로 여행 일정 계산
        start_date = datetime.strptime(user_input.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(user_input.end_date, '%Y-%m-%d')
        num_days = (end_date - start_date).days

        # 사용자 입력 데이터
        user_data = user_input.dict()

        # MongoDB 쿼리
        query = {
            "cat3" : {"$in": user_data['tour_type']}
        }

        # DB에서 추천데이터 가져오기
        accommodations = list(db.accommodations.find(query))
        restaurants = list(db.areaBaseList39.find(query))
        tour_spaces = list(db.areaBaseList12.find(query))
        cultural_facilities = list(db.areaBaseList14.find(query))
        leisure_spots = list(db.areaBaseList28.find(query))
        shopping_facilities = list(db.areaBaseList38.find(query))

        df = pd.concat([pd.DataFrame(accommodations), pd.DataFrame(restaurants), pd.DataFrame(tour_spaces), pd.DataFrame(cultural_facilities), pd.DataFrame(leisure_spots), pd.DataFrame(shopping_facilities)])


        # 여행 일정을 n박 m일에 맞추어 분배
        itinerary = []

        for day in range(num_days):
            daily_recommendations = recommend(user_data, df, day)
            itinerary.append({
                'date': (start_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                'recommendations': daily_recommendations
            })
        return {'itinerary': itinerary}
    except Exception as e:
        logger.error(f"Error during recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result")
async def result_page(request: Request):
    itinerary = request.session.get('itinerary', [])
    return templates.TemplateResponse('result.html', {'request': request, 'itinerary': itinerary})


@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Recommendation API!"}
# API 테스트 경로
@app.get("/test")
def test():
    return {"message": "API is working!"}


if __name__=="__main__":
    uvicorn.run("fastapi_app.app:app", host="0.0.0.0", port=8001, reload=True)