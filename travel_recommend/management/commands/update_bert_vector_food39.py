import pandas as pd
import numpy as np
from pymongo import MongoClient
from tqdm import tqdm
import ast

# MongoDB 연결 설정 (로컬 MongoDB 사용)
# client = MongoClient('mongodb://localhost:27017/')
# db = client['MyDiary']

# CSV 파일 읽기
df = pd.read_csv('bert_embeddings_food.csv')

print(df['bert_vector'].head())
print(df['bert_vector'].apply(lambda x: type(x)).unique())
print(df['bert_vector'].apply(lambda x: np.array(x).shape).unique())

# MongoDB에 데이터 업데이트
collection_names = ['areaBaseList39']

bert_vector_size = 768


# 문자열로 저장된 벡터를 numpy 배열로 변환하는 함수
def string_to_numpy_array(s):
    try:
        if isinstance(s, float) and np.isnan(s):
            return np.zeros(bert_vector_size)  # NaN 값을 모두 0으로 대체
        s = s.strip('[]').replace('\n', ' ')
        return np.fromstring(s, sep=' ', dtype=float)
    except Exception as e:
        print(f"Error converting string to numpy array: {e}")
        return np.zeros(bert_vector_size)

# `bert_vector` 컬럼의 NaN 값을 0으로 대체
df['bert_vector'] = df['bert_vector'].fillna(' '.join(['0.0'] * bert_vector_size))

# `bert_vector` 컬럼의 문자열을 numpy 배열로 변환
df['bert_vector'] = df['bert_vector'].apply(string_to_numpy_array)

# 변환된 벡터의 형태 확인
print(df['bert_vector'].apply(lambda x: x.shape).unique())
print(df['bert_vector'].apply(lambda x: type(x)).unique())
print(df['bert_vector'].head())

# for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Updating MongoDB"):
#     contentid = row['contentid']
#     bert_vector = row['bert_vector'].tolist()  # 리스트 형태로 변환
#
#     # 각 컬렉션에 대해 업데이트 시도
#     for collection_name in collection_names:
#         result = db[collection_name].update_one(
#             {'contentid': str(contentid)},
#             {'$set': {'bert_vector': bert_vector}}
#         )
#         if result.modified_count > 0:
#             print(f'Updated contentid {contentid} in collection {collection_name}')
#             break  # 한 컬렉션에서 업데이트가 성공하면 나머지는 시도하지 않음
#
# print("Update complete")
