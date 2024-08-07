import os
import django
import pymongo
from fastapi import FastAPI, Query
from gensim.models import FastText
from sklearn.metrics.pairwise import cosine_similarity
import random
from collections import Counter
from konlpy.tag import Komoran
from django.http import JsonResponse


app = FastAPI()


from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
import sys
# Django 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(str(BASE_DIR))
# sys.path.append(r'C:/projects/Encore_Final_Project')
# sys.path.append(r'/Users/ychun/projects/Encore_Final_Project')

# 프로젝트의 루트 디렉토리 경로 설정
PROJECT_ROOT = 'myproject.settings'

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', PROJECT_ROOT)
django.setup()
from django.conf import settings

# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
collection = db['areaBaseList']
cat1_collection = db['categoryCode1']
cat2_collection = db['categoryCode2']
cat3_collection = db['categoryCode3']
plan_collection = db['plan']


# komoran 초기화 / fasttext model 로드
komoran = Komoran()
model_path = os.path.join(settings.BASE_DIR, 'diaryapp/models', 'fasttext_model.model')
model = FastText.load(model_path)


# 다이어리 형용사 추출 함수
def extract_adjectives(words):
    xr_xsa_etm = []
    va_etm = []
    etc_etm = ['특별한', '신선한', '아름다운', '기분좋은', '해맑은', '활기찬', '재밌는', '반짝이는']

    for word in words:
        pos_tags_words = komoran.pos(word)  # 각 단어의 품사 태깅
        prev_pos = None

        for token, pos in pos_tags_words:
            # VA ETM 조합
            if prev_pos == 'VA' and pos == 'ETM':
                va_etm.append(word)

            # XR XSA ETM 조합
            elif prev_pos == 'XR' and pos == 'XSA':
                prev_word = word  # 현재 단어 저장
            elif prev_pos == 'XSA' and pos == 'ETM':
                xr_xsa_etm.append(prev_word)

            # 현재 품사 업데이트
            prev_pos = pos

    # 우선순위에 따라 랜덤 선택
    if xr_xsa_etm:
        selected_adjective = random.choice(xr_xsa_etm)
    else:
        selected_adjective = random.choice(va_etm) if va_etm else random.choice(etc_etm)

    return selected_adjective


# 다이어리 명사 추출 함수
def extract_nouns(pos_tags):
    nouns = []
    current_noun = []

    for word, pos in pos_tags:
        if pos in ['NA', 'NF', 'NNG', 'NNP', 'NV']:
            current_noun.append(word)
        else:
            if current_noun:  # 이전에 쌓인 명사가 있다면
                nouns.append(" ".join(current_noun))  # 현재 명사를 합쳐서 추가
                current_noun = []  # 현재 명사 초기화

    # 마지막으로 쌓인 명사가 있을 경우 추가
    if current_noun:
        nouns.append(" ".join(current_noun))

    return nouns


# 빈도 높은 일정 추출 함수
# 빈도 높은 순 > 전체
# 빈도 높은 일정이 다이어리 명사와 매칭이 안되면 전체 반환
def frequent_category(plan_data, nouns):

    updated_documents = []

    for document in plan_data:
        for cat in ['cat1', 'cat2', 'cat3']:
            cat_code = document.get(cat)
            # 카테고리 컬렉션 이름을 동적으로 설정
            category_collection = db[f'categoryCode{cat[-1]}']

            category = category_collection.find_one({'code': cat_code}, {'name': 1, '_id': 0})
            document[cat] = category['name'] if category else cat_code

        updated_documents.append(document)

    for cat in ['cat1', 'cat2', 'cat3']:
        # 카테고리 값 수집
        cat_values = [doc[cat] for doc in updated_documents]
        # 빈도 계산
        cat_counter = Counter(cat_values)
        max_count = max(cat_counter.values())
        most_frequent = [item for item, count in cat_counter.items() if count == max_count]

        # 모든 항목이 다를 경우 전체 항목 반환
        if len(most_frequent) == len(cat_counter):
            most_frequent = list(cat_counter.keys())

        # 조건에 맞는 문서 필터링
        final_documents = [doc for doc in updated_documents if doc[cat] in most_frequent]

    all_nouns_not_found = True  # 모든 문서에서 nouns가 발견되지 않았다고 가정

    for document in final_documents:
        if any(any(noun in str(value) for value in document.values()) for noun in nouns):
            all_nouns_not_found = False  # 하나라도 발견되면 False로 변경
            break

    if all_nouns_not_found:
        final_documents = updated_documents

    return final_documents


# 유사도 계산 명사 추출 함수
def select_noun(nouns, final_documents, model):
    # 각 우선 순위에 따른 명사 저장
    selected_nouns = []

    # 타이틀 유사도 0.999 이상 우선 처리
    for doc in final_documents:
        title = doc.get('title', '')
        if title in model.wv:
            for noun in nouns:
                if noun in model.wv:
                    noun_vector = model.wv[noun].reshape(1, -1)
                    title_vector = model.wv[title].reshape(1, -1)

                    similarity = cosine_similarity(title_vector, noun_vector)[0][0]
                    if (similarity >= 0.999) or (noun in title):
                        selected_nouns.append((title, noun))

    # 타이틀 유사도 높은 명사 반환
    if selected_nouns:
        return random.choice(selected_nouns)  # 랜덤으로 하나 선택

    # 카테고리 유사도로 우선순위 처리
    for cat in ['cat3', 'cat2', 'cat1']:
        for doc in final_documents:
            title = doc.get('title', '')
            cat_value = doc.get(cat, '')
            if cat_value in model.wv:
                for noun in nouns:
                    if noun in model.wv:
                        noun_vector = model.wv[noun].reshape(1, -1)
                        cat_vector = model.wv[cat_value].reshape(1, -1)

                        similarity = cosine_similarity(cat_vector, noun_vector)[0][0]
                        if similarity >= 0.9:
                            selected_nouns.append((title, noun, cat_value, similarity))

    if selected_nouns:
        # 유사도 기준으로 정렬
        selected_nouns.sort(key=lambda x: x[-1], reverse=True)
        best_match = selected_nouns[0]
        return best_match[:3]

    return ('','여행자')

# 별명 추출 함수
def extract_words(plan_data, content):
    pos_tags = komoran.pos(content)
    words = content.split()

    # 다이어리 형용사 추출
    selected_adjective = extract_adjectives(words)

    # 다이어리 명사 추출
    nouns = extract_nouns(pos_tags)

    # 빈도 높은 일정 추출
    final_documents = frequent_category(plan_data, nouns)

    # 유사도 계산 명사 추출
    selected_noun = select_noun(nouns, final_documents, model)

    return selected_noun[0], selected_adjective + ' ' + selected_noun[1].replace(" ", "")


@app.get("/generate-nickname/")
async def generate_nickname(plan_id: str = Query(...), content: str = Query(...)):

    # 일정 여행지 plan_id
    # 일정 id를 받아 와서 일정 데이터를 불러와 title, cat1, cat2, cat3를 뽑기->plan_data
    # plan_id = 'test'
    print('------------------', plan_id)

    # 일정 여행지 list 가져 오기
    if plan_id :
        plan = plan_collection.find_one({'plan_id': plan_id})
        days = plan.get('days', {})

        all_titles = []
        for day, titles in days.items():
            all_titles.extend(titles)

        query = {"title": {"$in": all_titles}}
        projection = {"title": 1, "cat1": 1, "cat2": 1, "cat3": 1, "_id": 0}
        cursor = collection.find(query, projection)

        plan_data = list(cursor)
        print('------------------', plan_data)
    else :
        plan_data = [{"title": '', "cat1": '', "cat2": '', "cat3": ''}]


    # 일정 여행지 list (예시)
    # cursor = collection.find({"title": {"$regex": "우도\\(해양도립공원\\)|세화해변|협재해수욕장|성산일출봉"}},
    #                          {"title": 1, "cat1": 1, "cat2": 1, "cat3": 1, "_id": 0})
    # plan_data = list(cursor)


    # 다이어리 content
    # 일정 여행지 list (예시)
    # content = '''제주도의 푸른 바다와 하얀 모래는 정말 멋지고 차갑고 빨갛다 좋다. 세화 해변을 걷는 것만으로도 마음이 편안해졌어요.
    #         유채꽃 필 때 방문한 우도는 한국의 아름다움을 다시 한 번 느낄 수 있었던 곳이에요.
    #         제주의 풍경은 정말 매력적이었고, 특히 성산 일출봉에서 일출을 보는 것은 잊지 못할 순간이었어요.
    #         협재 해수욕장의 파도 소리와 시원한 바람은 제주에서의 시간을 더욱 특별하게 만들어 주었어요.
    #         제주에서 맛본 흑돼지고기와 감귤은 정말 맛있었고, 다시 방문하고 싶은 마음이 들 정도로 여행이 즐거웠어요.'''

    # content = '산에 갔어요 행복했습니다'

    title, nickname = extract_words(plan_data, content)

    return title, nickname


import uvicorn
if __name__ == "__main__":
    uvicorn.run("nickname_app:app", host='0.0.0.0', port=5012, reload=True)
