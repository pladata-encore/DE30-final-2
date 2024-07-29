import pymongo
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sessions.backends import SessionBackend
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.backends.session_backend import SessionModel
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier
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
from transformers import BertTokenizer, BertModel
import torch
import secrets
from starlette.middleware.sessions import SessionMiddleware
from uuid import UUID, uuid4

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

# MongoDB 클라이언트 설정
client = pymongo.MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority')
db = client['MyDiary']


# 세션 설정

SECRET_KEY = '6271'
cookie_params = CookieParameters()
backend = InMemoryBackend[UUID, dict]()
cookie = SessionCookie(
    cookie_name="session",
    identifier="general_verifier",
    auto_error=True,
    secret_key=SECRET_KEY,
    cookie_params=cookie_params
)

class BasicVerifier(SessionVerifier[UUID, dict]):
    def __init__(
            self,
            *,
            identifier: str,
            auto_error: bool,
            backend: InMemoryBackend[UUID, dict],
            auth_http_exception: HTTPException,
    ):
            self._identifier = identifier
            self._auto_error = auto_error
            self._backend = backend
            self._auth_http_exception = auth_http_exception

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def backend(self) -> InMemoryBackend[UUID, dict]:
        return self._backend

    @property
    def auto_error(self) -> bool:
        return self._auto_error

    @property
    def auth_http_exception(self) -> HTTPException:
        return self._auth_http_exception

    async def verify_session(self, model: dict) -> bool:
        try:
            session_data = await self._backend.read(model['session_id'])
            logger.info(f"Session data found: {session_data}")
            return session_data is not None
        except Exception as e:
            logger.error(f"Session verification failed: {e}")
            return False

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session")
)

app.add_middleware(SessionMiddleware, secret_key = SECRET_KEY)

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
    pets_allowed: str = None
    pet_size: str = None
    food_preference: List[str] = []
    tour_type: List[str] = []
    accommodation_type: List[str] = []
    travel_preference: List[str] = []   # 느긋한 여행, 빡센 여행 중 하나 선택 -> 선택에 따른 추천 갯수 조절에 필요
    food_detail: str = None     # 사용자가 추가로 입력하는 음식 취향 텍스트
    activity_detail: str = None   # 사용자가 추가로 입력하는 관광지 취향 텍스트
    accommodation_detail: str = None   # 사용자가 추가로 입력하는 숙소 취향 텍스트


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
    bert_vector = get_bert_embedding(user_input, tokenizer, bert_model)
    return bert_vector

# 일정 추천에 필요하지 않은 데이터 필터링 (캠핑장, 외국인 전용 숙소)
def filter_unwanted_sites(df):
    camping_codes = ['A03021700']
    foreign_keywords = ["외국인", "외국인만", "외국인 전용", "foreigners only"]
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
    df['similarity_w2v'] = df[w2v_column].apply(
        lambda x: cosine_similarity([preference_w2v_vector], [x]).flatten()[0] if np.any(x) else 0)
    df['similarity_bert'] = df[bert_column].apply(
        lambda x: cosine_similarity([preference_bert_vector], [x]).flatten()[0] if np.any(x) else 0)
    df['similarity'] = (df['similarity_w2v'] + df['similarity_bert']) / 2
    return df

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


def recommend(user_input, df, day):
    logger.info(f"Day {day} recommendation process started")

    logger.info(f"df ******************* {df}")


    # 1차 필터링: 지역 기반 필터링
    filtered_df = df[
        (df['areacode'] == user_input['region']) &
        (df['sigungucode'] == user_input['subregion'])
    ]
    logger.info(f"Filtered DataFrame for region and subregion: {filtered_df}")

    # 유사도 계산을 위한 벡터 생성
    food_preference_text = " ".join(user_input.get('food_preference', []))
    activity_preference_text = " ".join(user_input.get('tour_type', []))
    accommodation_preference_text = " ".join(user_input.get('accommodation_type', []))

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

    food_preference_w2v_vector = process_user_input_w2v(food_preference_text)
    food_preference_bert_vector = process_user_input_bert(food_preference_text)
    activity_preference_w2v_vector = process_user_input_w2v(activity_preference_text)
    activity_preference_bert_vector= process_user_input_bert(activity_preference_text)
    accommodation_preference_w2v_vector = process_user_input_w2v(accommodation_preference_text)
    accommodation_preference_bert_vector = process_user_input_bert(accommodation_preference_text)

    # 유사도 계산 및 필터링
    food_filtered = get_similarity(filtered_df[filtered_df['cat3'].isin(user_input.get('food_preference', []))], food_preference_w2v_vector, food_preference_bert_vector)
    tour_filtered = get_similarity(filtered_df[filtered_df['cat3'].isin(user_input.get('tour_type', []))], activity_preference_w2v_vector, activity_preference_bert_vector)
    accommodation_filtered = get_similarity(filtered_df[filtered_df['cat3'].isin(user_input.get('accommodation_type', []))], accommodation_preference_w2v_vector, accommodation_preference_bert_vector)

    # 필요하지 않은 장소 필터링
    food_filtered = filter_unwanted_sites(food_filtered)
    tour_filtered = filter_unwanted_sites(tour_filtered)
    accommodation_filtered = filter_unwanted_sites(accommodation_filtered)

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

    # 여행 스타일에 따른 추천 개수 설정
    if "바삐 돌아다니는 여행" in user_input.travel_preference:
        num_food = 3
        num_tour = 4
    else: # 기본 값은 느긋한 여행
        num_food = 2
        num_tour = 2

    # 괸광지 추천 로직
    tour_collections = {
        'areaBaseList12': tour_filtered[filtered_df['contenttypeid'] == '12'],
        'areaBaseList14': tour_filtered[filtered_df['contenttypeid'] == '14'],
        'areaBaseList28': tour_filtered[filtered_df['contenttypeid'] == '28'],
        'areaBaseList38': tour_filtered[filtered_df['contenttypeid'] == '38'],
    }

    for collection_name, collection_df in tour_collections.items():
        if not collection_df.empty:
            collection_df = collection_df.sort_values(by='similarity', ascending=False).head(num_tour // len(tour_collections))
            recommendations.append(collection_df)

    recommended_tourist_spots = pd.concat(recommendations)
    logger.info(f"Tourist spots recommmended")

    # 식당 추천 로직
    if not food_filtered.empty:
        recommended_restaurants = food_filtered.sort_values(by='similarity', ascending=False).head(num_food)
    else:
        recommended_restaurants = pd.DataFrame()

    # 숙소 추천 로직
    if not accommodation_filtered.empty:
        selected_accommodation = accommodation_filtered.sort_values(by='similarity', ascending=False).head(1).iloc[0]
    else:
        selected_accommodation = pd.DataFrame()

    if recommended_restaurants.empty and recommended_tourist_spots.empty:
        return [selected_accommodation.to_dict()]

    accommodation_location = (float(selected_accommodation['mapx']), float(selected_accommodation['mapy']))

    recommended_restaurants['distance'] = recommended_restaurants.apply(
        lambda x: haversine(accommodation_location[1], accommodation_location[0], float(x['mapx']), float(x['mapy'])),
        axis = 1
    )
    recommended_restaurants = recommended_restaurants.sort_values(by=['distance', 'final_score']).head(num_food)

    recommendations = pd.concat([recommended_restaurants, recommended_tourist_spots])
    recommendations = recommendations[['contentid','title','mapx','mapy','final_score']].to_dict(orient='records')

    recommendations.insert(0, selected_accommodation.to_dict())

    logger.info(f"Day {day} recommendation process completed")
    return recommendations

class Item(BaseModel):
    name: str

@app.post("/items/")
async def test_post(item: Item):
    return {"item":item}

# @app.post("/recommend", response_model=dict)
@app.post("/recommend", response_model=dict)
async def recommend_schedule(user_input: UserInput, request: Request, response: Response):
    try:
        print(f"User input received: {user_input}")
        logger.info(f"User input received: {user_input}")

        # 입력 받은 날짜를 기반으로 여행 일정 계산
        start_date = datetime.strptime(user_input.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(user_input.end_date, '%Y-%m-%d')
        num_days = (end_date - start_date).days

        # 사용자 입력 데이터
        user_data = user_input.dict()

        # MongoDB 쿼리
        query = {
            "cat3": {"$in": user_data['tour_type']}
        }

        # DB에서 추천데이터 가져오기
        accommodations = list(db.accommodations.find(query))
        restaurants = list(db.areaBaseList39.find(query))
        tour_spaces = list(db.areaBaseList12.find(query))
        cultural_facilities = list(db.areaBaseList14.find(query))
        leisure_spots = list(db.areaBaseList28.find(query))
        shopping_facilities = list(db.areaBaseList38.find(query))

        df = pd.concat([pd.DataFrame(accommodations), pd.DataFrame(restaurants), pd.DataFrame(tour_spaces), pd.DataFrame(cultural_facilities), pd.DataFrame(leisure_spots), pd.DataFrame(shopping_facilities)])

        # 벡터 필드 확인
        ## Question 만약 벡터 필드가 존재 하지 않는 데이터라면 어떻게 처리해야 할까 ? -> 기본 벡터로 추가
        required_fields = ['w2v_vector','bert_vector']
        for field in required_fields:
            if field not in df.columns:
                logger.warning(f"{field} not found in dataframe. Filling with default vectors")
                if field == 'w2v_vector':
                    df[field] = [np.zeros(model.vector_size)] * len(df)
                elif field == 'bert_vector':
                    df[field] = [np.zeros(bert_model.config.hidden_size)] * len(df)

        # 여행 일정을 n박 m일에 맞추어 분배
        itinerary = []

        for day in range(num_days):
            daily_recommendations = recommend(user_data, df, day)
            itinerary.append({
                'date': (start_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                'recommendations': daily_recommendations
            })

        # 세션 데이터 생성 및 저장
        session_id = uuid4()
        await backend.create(session_id, {"itinerary": itinerary})
        cookie.attach_to_response(response, session_id)

        # 추천 결과 페이지로 리다이렉트하는 URL
        redirect_url = "/result/"

        return {'redirect_url': redirect_url}
    except Exception as e:
        logger.error(f"Error during recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result", dependencies=[Depends(cookie)])
async def result_page(request: Request, session_data: dict = Depends(verifier)):
    itinerary = session_data.get('itinerary', [])
    return templates.TemplateResponse('recommendations/result.html', {'request': request, 'itinerary': itinerary})



@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Recommendation API!"}
# API 테스트 경로
@app.get("/test")
def test():
    return {"message": "API is working!"}

if __name__=="__main__":
    uvicorn.run("fastapi_app.app:app", host="0.0.0.0", port=5000, reload=True)