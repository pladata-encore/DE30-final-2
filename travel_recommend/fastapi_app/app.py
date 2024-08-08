import ast

import bson
import pymongo
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Any, Dict, Optional
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
from transformers import BertTokenizer, BertModel
import torch
from geopy.distance import geodesic
from typing import Union
from pydantic import ValidationError
import json
from requests import request
import uuid
import django

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FlaskAPI 애플리케이션 초기화
app = FastAPI()

templates = Jinja2Templates(directory="templates")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
import sys
# Django 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(str(BASE_DIR))

# 프로젝트의 루트 디렉토리 경로 설정
PROJECT_ROOT = 'myproject.settings'

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', PROJECT_ROOT)
django.setup()

# MongoDB 클라이언트 설정
# client = pymongo.MongoClient('mongodb://127.0.0.1:27017')
# db = client['MyDiary']
from django.conf import settings
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]


# Komoran 및 Word2Vec 모델 로드
komoran = Komoran()
model_path = os.path.join(os.path.dirname(__file__), "models", "word2vec_model2.model")
if os.path.exists(model_path):
    model = Word2Vec.load(model_path)
else:
    raise FileNotFoundError(f"Model file not found at {model_path}")

# BERT 모델과 토크나이저 로드
tokenizer = BertTokenizer.from_pretrained('beomi/kcbert-base')
bert_model = BertModel.from_pretrained('beomi/kcbert-base')

# 사용자 여행 취향 입력 정보
# UserInput 클래스를 정의해 사용자 입력 데이터 구조화
class UserInput(BaseModel):
    region: str
    subregion: str
    start_date: str
    end_date: str
    food_preference: List[str]
    tour_type: List[str]
    accommodation_type: List[str]
    travel_preference: str
    food_detail: Optional[str] = None
    activity_detail: Optional[str] = None
    accommodation_detail: Optional[str] = None

class Recommendation(BaseModel):
    title: str

class DayPlan(BaseModel):
    date: str
    recommendations: List[Recommendation]

class Itinerary(BaseModel):
    itinerary: List[DayPlan]


#숙소 cat3 코드 동적으로 가져오는 함수
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

# 사용자 입력을 모델에 사용할 수 있도록 BERT 임베딩 변환
def get_bert_embedding(text, tokenizer, model, max_length=512):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=max_length)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

# 사용자 입력을 텍스트로 받아 Komoran을 이용해 명사, 형용사 추출, 학습된 모델을 이용해 벡터로 변환
def process_user_input_w2v(user_input):
    tokens = komoran.pos(user_input)
    tokens = [word for word, pos in tokens if pos in ['NA','NF','NV','NNG', 'NNP', 'VA']]
    # 학습된 word2vec 모델로 사용자 입력을 벡터로 변환
    w2v_vector = get_average_word2vec(tokens, model)
    return w2v_vector

# 사용자 입력을 텍스트로 받아 학습된 BERT 모델을 이용해 벡터로 변환
def process_user_input_bert(user_input):
    bert_vector = get_bert_embedding(user_input, tokenizer, bert_model).reshape(1, -1)
    return bert_vector

# 벡터 데이터를 numpy 배열로 변환하는 함수 -> 벡터값을 db에 저장할 때 문자열로 저장했기 때문
# Bert 모델의 벡터 차원은 768
def string_to_numpy_array(vector):
    try:
        if isinstance(vector, str):
            vector = ast.literal_eval(vector)
        np_array = np.array(vector, dtype=np.float32)
        if np_array.size == 0:
            return np.zeros(768)
        return np_array
    except (ValueError, SyntaxError) as e:
        print(f"Error in converting string to numpy array: {e}")
        return np.zeros(768)  # 빈 배열 반환



# 벡터 필드를 기본 값으로 채우는 함수
# 벡터 필드를 기본 값으로 채우는 함수
def fill_default_vectors(df, w2v_size, bert_size):
    if 'w2v_vector' not in df.columns or df['w2v_vector'].isnull().any():
        df['w2v_vector'] = df.get('w2v_vector', pd.Series([np.zeros(w2v_size)] * len(df))).apply(lambda x: x if isinstance(x, np.ndarray) else np.zeros(w2v_size))
    if 'bert_vector' not in df.columns or df['bert_vector'].isnull().any():
        df['bert_vector'] = df.get('bert_vector', pd.Series([np.zeros(bert_size)] * len(df))).apply(lambda x: x if isinstance(x, np.ndarray) else np.zeros(bert_size))
    return df

# 일정 추천에 필요하지 않은 데이터 필터링 (캠핑장, 외국인 전용 숙소)
def filter_unwanted_sites(df):
    camping_codes = ['A03021700']
    foreign_keywords = ["외국인", "외국인만", "외국인 전용", "foreigners only"]

    # Debugging: Log the types in 'overview' column
    logger.info(f"Types in df['overview']: {df['overview'].apply(type).unique()}")

    # Convert 'overview' column to string if it's not already
    df['overview'] = df['overview'].astype(str)

    mask_camping = df['cat3'].apply(lambda x: x not in camping_codes)
    mask_foreign = df['overview'].apply(lambda x: not any(keyword in x for keyword in foreign_keywords))
    return df[mask_camping & mask_foreign]

# 여행 일정 경로 최적화
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(float, [lon1, lat1, lon2, lat2]) # 문자열 -> 실수 변환
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    km = 6371 * c
    return km

# 유사도 계산(word2vec, BERT) 함수 -> 코드 가독성을 위해 만듦
def get_similarity(df, preference_w2v_vector, preference_bert_vector, w2v_column='w2v_vector', bert_column='bert_vector'):
    preference_w2v_vector = preference_w2v_vector.reshape(1, -1)
    preference_bert_vector = preference_bert_vector.reshape(1, -1)

    # Ensure vectors in df are 2D and handle NaN values
    df[w2v_column] = df[w2v_column].apply(lambda x: np.nan_to_num(x.reshape(1, -1) if isinstance(x, np.ndarray) and x.ndim == 1 else np.zeros(preference_w2v_vector.shape[1])))
    df[bert_column] = df[bert_column].apply(lambda x: np.nan_to_num(x.reshape(1, -1) if isinstance(x, np.ndarray) and x.ndim == 1 else np.zeros(preference_bert_vector.shape[1])))

    df.loc[:, 'similarity_w2v'] = df[w2v_column].apply(
        lambda x: cosine_similarity(preference_w2v_vector, x).flatten()[0] if np.any(x) else 0)
    df.loc[:, 'similarity_bert'] = df[bert_column].apply(
        lambda x: cosine_similarity(preference_bert_vector, x).flatten()[0] if np.any(x) else 0)
    df.loc[:, 'similarity'] = (df['similarity_w2v'] + df['similarity_bert']) / 2

    return df

# 추천 항목 부족한 경우 거리 계산 함수
def calculate_distance(loc1, loc2):
    return geodesic(loc1, loc2).km

def search_nearby_items(df, base_location, category, radius):
    nearby_items = []
    for index, row in df.iterrows():
        if row['category'] == category:
            item_location = (row['mapy'], row['mapx'])
            distance = calculate_distance(base_location, item_location)
            if distance <= radius:
                nearby_items.append(row)
    return nearby_items


def get_nearby_recommendations(df, base_recommendations, category, required_count, radius=2):
    additional_recommendations = []

    for base_rec in base_recommendations:
        base_location = (base_rec['mapy'], base_rec['mapx'])

        # 근처의 항목 검색
        nearby_recs = search_nearby_items(df, base_location, category, radius)

        for rec in nearby_recs:
            if len(additional_recommendations) >= required_count:
                break
            if rec['_id'] not in [item['_id'] for item in
                                  base_recommendations] and rec not in additional_recommendations:
                additional_recommendations.append(rec)

        if len(additional_recommendations) >= required_count:
            break

    return additional_recommendations


# 사용자 입력 카테고리 매핑
food_map = {
    "한식": ["백반", "한정식", "탕/찌개/전골", "국수/면요리", "분식", "소고기 요리", "돼지고기 요리", "닭고기 요리", "오리고기 요리", "양고기 요리", "곱창/막창", "해물찜/해물탕", "생선회", "생선구이", "조개구이/조개찜", "간장게장"],
    "서양식": ["피자/파스타", "스테이크", "햄버거", "브런치""소고기 요리", "돼지고기 요리", "닭고기 요리", "오리고기 요리", "양고기 요리"],
    "중식": ["짬뽕/짜장면", "양꼬치", "딤섬/중식만두", "소고기 요리", "돼지고기 요리", "닭고기 요리", "오리고기 요리", "양고기 요리"],
    "일식": ["초밥", "일본식 라면", "우동/소바", "소고기 요리", "돼지고기 요리", "닭고기 요리", "오리고기 요리", "양고기 요리"],
    "기타":["태국 음식", "필리핀 음식", "그리스 음식", "멕시코 음식", "스페인 음식", "인도 음식", "소고기 요리", "돼지고기 요리", "닭고기 요리", "오리고기 요리", "양고기 요리"],
    "음료":["소주", "맥주", "와인", "전통주", "칵테일"]
}

# 사용자 입력 카테고리 매핑 (cat3 코드)
def map_user_preference(user_input: UserInput):
    accommodation_map = {
        "호텔": "B02010100",
        "리조트/콘도": "B02010500",
        "유스호스텔": "B02010600",
        "펜션": "B02010700",
        "모텔": "B02010900",
        "민박": "B02011000",
        "게스트하우스": "B02011100",
        "홈스테이": "B02011200",
        "서비스드레지던스": "B02011300",
        "한옥": "B02011600"
    }
    food_category_map = {
        "백반": "A05020100", "한정식": "A05020100", "탕/찌개/전골": "A05020100", "국수/면요리": "A05020100", "분식": "A05020100",
        "소고기 요리": "A05020100", "돼지고기 요리": "A05020100", "닭고기 요리": "A05020100", "오리고기 요리": "A05020100",
        "양고기 요리": "A05020100", "곱창/막창": "A05020100", "해물찜/해물탕": "A05020100", "생선회": "A05020100", "생선구이": "A05020100",
        "조개구이/조개찜": "A05020100", "간장게장": "A05020100",
        "피자/파스타": "A05020200", "스테이크": "A05020200", "햄버거": "A05020200", "브런치": "A05020200",
        "짬뽕/짜장면": "A05020400", "양꼬치": "A05020400", "딤섬/중식만두": "A05020400",
        "초밥": "A05020300", "일본식 라면": "A05020300", "우동/소바": "A05020300",
        "태국 음식": "A05020700", "필리핀 음식": "A05020700", "그리스 음식": "A05020700", "멕시코 음식": "A05020700",
        "스페인 음식": "A05020700", "인도 음식": "A05020700",
    }
    tour_map = {
        "자연 명소": ["A01010100", "A01010200", "A01010300", "A01010400", "A01010500", "A01010600", "A01010700", "A01010800", "A01010900", "A01011100", "A01011300","A01011900", "A01011700", "A01011900", "A01020100", "A01011400", "A01011600"],
        "바닷가/해변": ["A01011100", "A01011200", ""],
        "공원": ["A01010100", "A01010200", "A01010300"],
        "산": "A01010400",
        "계곡/폭포": ["A01010800","A01010900","A01011000"],
        "생태관광지/휴양림": ["A01010500", "A01010600", "A01010700"],
        "고궁/성": ["A02010100", "A02010200", "A02010200"],
        "고택/생가": ["A02010400", "A02010500"],
        "민속마을": "A02010600",
        "유적지/사적지": "A02010700",
        "기녑탑/전망대": "A02050200",
        "절/사찰": "A02010800",
        "종교성지": "A02010900",
        "온천/스파/찜질방": ["A02020300", "A02020400"],
        "테마공원": ["A02020600", "A02020700"],
        "유람선/잠수함": "A02020800",
        "자연 체험": "A02030100",
        "전통 체험": "A02030200",
        "산사 체험": "A02030300",
        "이색 체험": "A02030400",
        "박물관": "A02060100",
        "기념관": "A02060200",
        "전시관": "A02060300",
        "컨벤션센터": "A02060400",
        "미술관/화랑": "A02060500",
        "도서관": "A02060900",
        "수상 레포츠": "A03010200",
        "항공 레포츠": "A03010300",
        "인라인/실내스케이트": "A03020400",
        "자전거하이킹": "A03020500",
        "카트": "A03020600",
        "골프": "A03020700",
        "경마/경륜": ["A03020800", "A03020900"],
        "카지노": "A03021000",
        "승마": "A03021100",
        "스키/스노보드": "A03021200",
        "스케이트": "A03021300",
        "썰매장": "A03021400",
        "수렵/사격": ["A03021500", "A03021600"],
        "암벽등반": "A03021800",
        "서바이벌게임": "A03022000",
        "ATV/MTB" : ["A03022100", "A03022200"],
        "번지점프": "A03022400",
        "트래킹": "A03022700",
        "윈드서핑/제트스키": "A03030100",
        "카약/카누": "A03030200",
        "요트": "A03030300",
        "스노쿨링/스킨스쿠버다이빙": "A03030400",
        "낚시": ["A03030500", "A03030600"],
        "래프팅": "A03030800",
        "스카이다이빙": "A03040100",
        "초경량비행": "A03040200",
        "행글라이딩/패러글라이딩": "A03040300",
        "5일장": "A04010100",
        "상설시장": "A04010200",
        "백화점": "A04010300",
        "면세점": ["A04010400", "A04011000"],
        "대형마트": "A04010500",
        "공예/공방": "A04010700",
        "특산물판매점": "A04010900"
    }

    # 각 사용자 입력이 리스트인지 확인하고 그렇지 않은 경우, 리스트로 변환
    def ensure_list(value):
        if isinstance(value, list):
            return value
        return [value] if value is not None else []

    food_preferences = ensure_list(user_input.food_preference)
    tour_types = ensure_list(user_input.tour_type)
    accommodation_types = ensure_list(user_input.accommodation_type)

    mapped_preferences = {
        'food_preference': [food_category_map[food] for food in food_preferences if food in food_category_map],
        'tour_type': [cat for tour in tour_types for cat in tour_map[tour] if tour in tour_map],
        'accommodation_type': [accommodation_map[acc] for acc in accommodation_types if acc in accommodation_map]
    }

    return mapped_preferences

# 추가 ) bson.objectid.ObjectId를 직렬화할 수 있도록 변환하는 함수
def transform_object_id(data):
    if isinstance(data, list):
        return [transform_object_id(item) for item in data]
    if isinstance(data, dict):
        return {k: (str(v) if isinstance(v, bson.ObjectId) else v) for k, v in data.items()}
    return data

def recommend(user_input, df, day, used_ids):
    if not isinstance(user_input, UserInput):
        user_input = UserInput(**user_input)

    logger.info(f"Day {day} recommendation process started")
    logger.info(f"df shape: {df.shape}")

    # 1차 필터링: 지역 기반 필터링
    filtered_df = df[
        (df['areacode'] == user_input.region) &
        (df['sigungucode'] == user_input.subregion)
    ].copy()

    logger.info(f"Filtered DataFrame for region and subregion: {filtered_df}")
    logger.error(f"filtered_df type: {type(filtered_df)}, shape: {filtered_df.shape}")
    logger.info(f"Filtered DataFrame example: {filtered_df.head()}")


    if filtered_df.empty:
        logger.error("No data found for the specified region and subregion")
        return []

    # 벡터 변환을 적용
    filtered_df['w2v_vector'] = filtered_df['w2v_vector'].apply(lambda x: string_to_numpy_array(x) if isinstance(x, str) else x)
    filtered_df['bert_vector'] = filtered_df['bert_vector'].apply(lambda x: string_to_numpy_array(x) if isinstance(x, str) else x)

    # 벡터 형태 확인 로그
    try:
        logger.info(f"Sample w2v_vector: {filtered_df.iloc[0]['w2v_vector']}, type: {type(filtered_df.iloc[0]['w2v_vector'])}, shape: {filtered_df.iloc[0]['w2v_vector'].shape}")
        logger.info(f"Sample bert_vector: {filtered_df.iloc[0]['bert_vector']}, type: {type(filtered_df.iloc[0]['bert_vector'])}, shape: {filtered_df.iloc[0]['bert_vector'].shape}")
    except Exception as e:
        logger.error(f"Error in vector shape logging: {e}")

    # 벡터 2D 변환
    try:
        filtered_df['w2v_vector'] = filtered_df['w2v_vector'].apply(
            lambda x: x.reshape(1, -1) if isinstance(x, np.ndarray) and x.ndim == 1 else x)
        filtered_df['bert_vector'] = filtered_df['bert_vector'].apply(
            lambda x: x.reshape(1, -1) if isinstance(x, np.ndarray) and x.ndim == 1 else x)
    except Exception as e:
        logger.error(f"Error in reshaping vectors: {e}")


    # 유사도 계산을 위한 벡터 생성
    food_preference_text = " ".join(user_input.food_preference)
    activity_preference_text = " ".join(user_input.tour_type)
    accommodation_preference_text = " ".join(user_input.accommodation_type)

    ## 사용자 추가 입력이 있을 경우 추가
    if user_input.food_detail:
        food_preference_text += " " + user_input.food_detail
    if user_input.activity_detail:
        activity_preference_text += " " + user_input.activity_detail
    if user_input.accommodation_detail:
        accommodation_preference_text += " " + user_input.accommodation_detail

    logger.info(f"Food preference text: {food_preference_text}")
    logger.info(f"Activity preference text: {activity_preference_text}")
    logger.info(f"Accommodation preference text: {accommodation_preference_text}")

    food_preference_w2v_vector = process_user_input_w2v(food_preference_text).reshape(1, -1)
    food_preference_bert_vector = process_user_input_bert(food_preference_text).reshape(1, -1)
    activity_preference_w2v_vector = process_user_input_w2v(activity_preference_text).reshape(1, -1)
    activity_preference_bert_vector = process_user_input_bert(activity_preference_text).reshape(1, -1)
    accommodation_preference_w2v_vector = process_user_input_w2v(accommodation_preference_text).reshape(1, -1)
    accommodation_preference_bert_vector = process_user_input_bert(accommodation_preference_text).reshape(1, -1)

    # 유사도 계산 및 필터링
    mapped_preferences = map_user_preference(user_input)

    # Debugging: Log the types of 'cat3' in filtered_df and mapped_preferences
    logger.info(f"Types in filtered_df['cat3']: {filtered_df['cat3'].apply(type).unique()}")
    logger.info(f"Types in mapped_preferences['food_preference']: {[type(x) for x in mapped_preferences['food_preference']]}")
    logger.info(f"Types in mapped_preferences['tour_type']: {[type(x) for x in mapped_preferences['tour_type']]}")
    logger.info(f"Types in mapped_preferences['accommodation_type']: {[type(x) for x in mapped_preferences['accommodation_type']]}")


    try:
        food_filtered = get_similarity(filtered_df[filtered_df['cat3'].astype(str).isin(mapped_preferences['food_preference'])], food_preference_w2v_vector, food_preference_bert_vector)
        tour_filtered = get_similarity(filtered_df[filtered_df['cat3'].astype(str).isin(mapped_preferences['tour_type'])], activity_preference_w2v_vector, activity_preference_bert_vector)
        accommodation_filtered = get_similarity(filtered_df[filtered_df['cat3'].astype(str).isin(mapped_preferences['accommodation_type'])], accommodation_preference_w2v_vector, accommodation_preference_bert_vector)
    except Exception as e:
        logger.error(f"Error during similarity calculation: {e}")
        return []

    logger.info(f"Filtered Food DataFrame: {food_filtered.shape}")
    logger.info(f"Filtered Tour DataFrame: {tour_filtered.shape}")
    logger.info(f"Filtered Accommodation DataFrame: {accommodation_filtered.shape}")

    # 필요하지 않은 장소 필터링
    food_filtered = filter_unwanted_sites(food_filtered)
    tour_filtered = filter_unwanted_sites(tour_filtered)
    accommodation_filtered = filter_unwanted_sites(accommodation_filtered)

    logger.info(f"Unwanted sites filtered - Food: {food_filtered.shape}")
    logger.info(f"Unwanted sites filtered - Tour: {tour_filtered.shape}")
    logger.info(f"Unwanted sites filtered - Accommodation: {accommodation_filtered.shape}")

    recommendations = []

    # 2차 필터링 : 사용자 입력 추가 텍스트 기반
    if user_input.food_detail:
        food_preference_w2v_vector = process_user_input_w2v(user_input.food_detail)
        food_preference_bert_vector = process_user_input_bert(user_input.food_detail)
        food_filtered = get_similarity(food_filtered, food_preference_w2v_vector, food_preference_bert_vector)

    if user_input.activity_detail:
        tour_preference_w2v_vector = process_user_input_w2v(user_input.activity_detail)
        tour_preference_bert_vector = process_user_input_bert(user_input.activity_detail)
        tour_filtered = get_similarity(tour_filtered, tour_preference_w2v_vector, tour_preference_bert_vector)

    if user_input.accommodation_detail:
        accommodation_preference_w2v_vector = process_user_input_w2v(user_input.accommodation_detail)
        accommodation_preference_bert_vector = process_user_input_bert(user_input.accommodation_detail)
        accommodation_filtered = get_similarity(accommodation_filtered, accommodation_preference_w2v_vector,
                                                accommodation_preference_bert_vector)

    logger.info(f"Post detail filtering - Food: {food_filtered.shape}")
    logger.info(f"Post detail filtering - Tour: {tour_filtered.shape}")
    logger.info(f"Post detail filtering - Accommodation: {accommodation_filtered.shape}")


    # 여행 스타일에 따른 추천 개수 설정
    if "바삐 돌아다니는 여행" in user_input.travel_preference:
        num_food = 3
        num_tour = 4
    else: # 기본 값은 느긋한 여행
        num_food = 2
        num_tour = 2

    logger.info(f"Number of tourist spots to recommend: {num_tour}")

    num_accommodation = 1

    # 이미 추천된 항목 제외 (일자별 추천 항목에 중복을 허용하지 않음)
    food_filtered = food_filtered[~food_filtered['contentid'].isin(used_ids)]
    tour_filtered = tour_filtered[~tour_filtered['contentid'].isin(used_ids)]
    accommodation_filtered = accommodation_filtered[~accommodation_filtered['contentid'].isin(used_ids)]

    recommendations = []

    if len(tour_filtered) < num_tour:
        tour_additional = get_nearby_recommendations(df, tour_filtered, "tour_type", num_tour - len(tour_filtered))
        tour_filtered = pd.concat([tour_filtered, pd.DataFrame(tour_additional)])

    if len(food_filtered) < num_food:
        food_additional = get_nearby_recommendations(df, food_filtered, "food_preference", num_food - len(food_filtered))
        food_filtered = pd.concat([food_filtered, pd.DataFrame(food_additional)])

    if len(accommodation_filtered) < num_accommodation:
        accommodation_additional = get_nearby_recommendations(df, accommodation_filtered, "accommodation_type", num_accommodation - len(accommodation_filtered))
        accommodation_filtered = pd.concat([accommodation_filtered, pd.DataFrame(accommodation_additional)])



    # 괸광지 추천 로직

    # contenttypeid의 데이터 타입 확인 및 필요 시 변환
    tour_filtered['contenttypeid'] = tour_filtered['contenttypeid'].astype(int)

    tour_collections = {
        'areaBaseList12': tour_filtered[tour_filtered['contenttypeid'] == 12],
        'areaBaseList14': tour_filtered[tour_filtered['contenttypeid'] == 14],
        'areaBaseList28': tour_filtered[tour_filtered['contenttypeid'] == 28],
        'areaBaseList38': tour_filtered[tour_filtered['contenttypeid'] == 38],
    }

    # Log the filtered tour collections for debugging
    logger.info(f"Filtered Tour Collections: {[collection_name + ': ' + str(collection_df.shape) for collection_name, collection_df in tour_collections.items()]}")

    for collection_name, collection_df in tour_collections.items():
        logger.info(f"Collection {collection_name} has {len(collection_df)} items")
        logger.info(f"Sample data from {collection_name}: {collection_df.head()}")

    recommendations = []

    for collection_name, collection_df in tour_collections.items():
        if not collection_df.empty:
            logger.info(f"Tour collections is : {tour_collections}")
            logger.info(f"Processing {collection_name} with {collection_df.shape[0]} items")
            collection_df = collection_df.sort_values(by='similarity', ascending=False).head(num_tour)
            recommendations.append(collection_df)

    if recommendations:
        recommended_tourist_spots = pd.concat(recommendations)
    else:
        # 관광지 추천이 없을 경우 마지막으로 필터린된 항목을 사용
        logger.info("No tourist spots recommended, using last filtered items")
        logger.info(f"tour_filtered data : {tour_filtered.head()}")
        recommended_tourist_spots = tour_filtered.sort_values(by='similarity', ascending=False).head(num_tour)

    logger.info(f"Recommended Tourist Spots: {recommended_tourist_spots.shape}")

    if not recommended_tourist_spots.empty:
        logger.info(f"Recommended Tourist Spots data: {recommended_tourist_spots.head()}")

    # 식당 추천 로직
    if not food_filtered.empty:
        recommended_restaurants = food_filtered.sort_values(by='similarity', ascending=False).head(num_food)
    else:
        recommended_restaurants = pd.DataFrame()

    # 숙소 추천 로직
    if not accommodation_filtered.empty:
        selected_accommodation = accommodation_filtered.sort_values(by='similarity', ascending=False).head(1).iloc[0]
    else:
        selected_accommodation = pd.Series({'contentid': '', 'title': '', 'mapx': '', 'mapy': ''})

    if recommended_restaurants.empty and recommended_tourist_spots.empty:
        return [selected_accommodation[['contentid', 'title', 'mapx', 'mapy']].to_dict()]

    accommodation_location = (float(selected_accommodation['mapx']), float(selected_accommodation['mapy']))

    recommended_restaurants['distance'] = recommended_restaurants.apply(
        lambda x: haversine(accommodation_location[1], accommodation_location[0], float(x['mapx']), float(x['mapy'])),
        axis = 1
    )
    recommended_restaurants = recommended_restaurants.sort_values(by='distance').head(num_food)

    recommendations = pd.concat([recommended_restaurants, recommended_tourist_spots])
    recommendations = recommendations.drop(['w2v_vector', 'bert_vector'], axis=1)
    recommendations = recommendations[['contentid','title','mapx','mapy']].to_dict(orient='records')

    selected_accommodation_info = selected_accommodation[['contentid', 'title', 'mapx', 'mapy']].to_dict()
    recommendations.insert(0, selected_accommodation_info)

    logger.info(f"Day {day} recommendation process completed")
    return recommendations

@app.post("/recommend", response_model=Dict[str, Any])
async def recommend_schedule(user_input: UserInput):
    try:
        logger.debug("Received POST request to /recommend")
        logger.debug(f"Raw user input: {user_input}")

        print("Received POST request")

        logger.info(f"User input received: {user_input}")
        print(f"User input received: {user_input}")

        # 입력 받은 날짜를 기반으로 여행 일정 계산
        start_date = datetime.strptime(user_input.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(user_input.end_date, '%Y-%m-%d')
        num_days = (end_date - start_date).days + 1

        # DB에서 추천데이터 가져오기
        accommodations = pd.DataFrame(list(db.accommodations.find())).assign(collection_name='accommodations')
        restaurants = pd.DataFrame(list(db.areaBaseList39.find())).assign(collection_name='areaBaseList39')
        tour_spaces = pd.DataFrame(list(db.areaBaseList12.find())).assign(collection_name='areaBaseList12')
        cultural_facilities = pd.DataFrame(list(db.areaBaseList14.find())).assign(collection_name='areaBaseList14')
        leisure_spots = pd.DataFrame(list(db.areaBaseList28.find())).assign(collection_name='areaBaseList28')
        shopping_facilities = pd.DataFrame(list(db.areaBaseList38.find())).assign(collection_name='areaBaseList38')

        df = pd.concat([pd.DataFrame(accommodations), pd.DataFrame(restaurants), pd.DataFrame(tour_spaces), pd.DataFrame(cultural_facilities), pd.DataFrame(leisure_spots), pd.DataFrame(shopping_facilities)])

        # 벡터 필드 확인
        ## Question 만약 벡터 필드가 존재 하지 않는 데이터라면 어떻게 처리해야 할까 ? -> 기본 벡터로 추가
        df = fill_default_vectors(df, model.vector_size, bert_model.config.hidden_size)

        # 벡터 데이터를 numpy 배열로 변환
        df['w2v_vector'] = df['w2v_vector'].apply(string_to_numpy_array)
        df['bert_vector'] = df['bert_vector'].apply(string_to_numpy_array)

        logger.info(f"Sample w2v_vector: {df.iloc[0]['w2v_vector']}, type: {type(df.iloc[0]['w2v_vector'])}, shape: {df.iloc[0]['w2v_vector'].shape}")
        logger.info(f"Sample bert_vector: {df.iloc[0]['bert_vector']}, type: {type(df.iloc[0]['bert_vector'])}, shape: {df.iloc[0]['bert_vector'].shape}")

        # 벡터 컬럼 형태를 로그에 출력
        logger.info(f"Sample w2v_vector: {df.iloc[0]['w2v_vector']}")
        logger.info(f"Sample bert_vector: {df.iloc[0]['bert_vector']}")

        # 여행 일정을 n박 m일에 맞추어 분배
        used_ids = set()
        itinerary = []

        for day in range(num_days):
            daily_recommendations = recommend(user_input, df, day, used_ids)
            used_ids.update([rec['contentid'] for rec in daily_recommendations])
            itinerary.append({
                'date': (start_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                'recommendations': transform_object_id(daily_recommendations)
            })

        # MongoDB에 일정 저장
        plan_id = str(uuid.uuid4())
        plan_data = {
            'plan_id': plan_id,
            'province': user_input.region,
            'city': user_input.subregion,
            'plan_title': f"{user_input.region}의 여행 일정",
            'email': 'neweeee@gmail.com',  # 이 부분은 실제 이메일로 교체해야 합니다.
            'days': itinerary
        }
        db.plan.insert_one(plan_data)

        logger.info(f"Generated itinerary: {itinerary}")
        print(f"Generated itinerary: {itinerary}")

        return {'itinerary': itinerary, 'plan_id': plan_id}
    except ValidationError as ve:
        logger.error(f"Validation Error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during recommendatiㅁons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plan/{plan_id}", response_model=Itinerary)
async def get_plan(plan_id: str):
    logger.info(f"----------planid: {plan_id}")
    try:
        # MongoDB에서 plan_id에 해당하는 일정을 조회
        plan_data = db.plan.find_one({"plan_id": plan_id})
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")

        itinerary = []
        for day in plan_data["days"]:
            day_plan = DayPlan(
                date=day["date"],
                recommendations=[Recommendation(title=rec["title"]) for rec in day["recommendations"]]
            )
            itinerary.append(day_plan)

        return {"itinerary": itinerary}
    except Exception as e:
        logger.error(f"Error fetching plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Recommendation API!"}
# API 테스트 경로
@app.get("/test")
def test():
    return {"message": "API is working!"}

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI 서버가 시작되었습니다")

if __name__=="__main__":
    # uvicorn.run("fastapi_app.app:app", host="0.0.0.0", port=5000, reload=True)
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)