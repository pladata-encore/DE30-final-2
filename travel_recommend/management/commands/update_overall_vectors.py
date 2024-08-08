from pymongo import MongoClient
import numpy as np
import ast

# MongoDB 클라이언트 설정
client = MongoClient('mongodb://localhost:27017')
db = client['MyDiary']


def string_to_numpy_array(s: str, vector_size=768):
    try:
        s = s.strip()
        if s.startswith('[') and s.endswith(']'):
            return np.array(ast.literal_eval(s), dtype=np.float32)
        else:
            return np.zeros(vector_size, dtype=np.float32)
    except Exception as e:
        print(f"Error converting string to numpy array: {e}")
        return np.zeros(vector_size, dtype=np.float32)


def update_bert_vectors(collection_name: str):
    collection = db[collection_name]
    documents = collection.find({"bert_vector": {"$exists": True}})

    for doc in documents:
        if isinstance(doc['bert_vector'], str):
            numpy_vector = string_to_numpy_array(doc['bert_vector'])
            print(f"Updating document {doc['_id']}: {numpy_vector}")
            # 리스트 형태로 변환하여 업데이트
            collection.update_one({"contentid": doc["contentid"]}, {"$set": {"bert_vector": numpy_vector.tolist()}})

def fetch_sample_data(collection_name: str):
    collection = db[collection_name]
    document = collection.find_one({"bert_vector": {"$exists": True}})
    return document

# 사용 예시
sample_data = fetch_sample_data('accommodations')
print(f"Sample data from 'accommodations': {sample_data}")

sample_data = fetch_sample_data('areaBaseList39')
print(f"Sample data from 'areaBaseList39': {sample_data}")

# 사용 예시
# update_bert_vectors('accommodations')
# update_bert_vectors('areaBaseList39')
# update_bert_vectors('areaBaseList12')
# update_bert_vectors('areaBaseList14')
# update_bert_vectors('areaBaseList28')
# update_bert_vectors('areaBaseList38')
