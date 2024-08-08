from pymongo import MongoClient

client = MongoClient('mongodb://192.168.0.25:27017/')
db = client['MyDiary']
# collection = db['diaryapp_wishlist']

# # 중복된 문서 확인
# duplicates = collection.aggregate([
#     {"$group": {"_id": {"user_email": "$user_email", "plan_id": "$plan_id"}, "count": {"$sum": 1}}},
#     {"$match": {"count": {"$gt": 1}}}
# ])
#
# for doc in duplicates:
#     print(doc)
#
from pymongo import MongoClient, ASCENDING
#
# # 중복 데이터 삭제
# db.diaryapp_wishlist.delete_many({ "user_email": "neweeee@gmail.com", "plan_id": "" })
#
# # 인덱스 삭제 및 재생성
# db.diaryapp_wishlist.drop_index("diaryapp_wishlist_user_email_plan_id_a7813443_uniq")
# db.diaryapp_wishlist.create_index([("user_email", ASCENDING), ("plan_id", ASCENDING)], unique=True, name="diaryapp_wishlist_user_email_plan_id_a7813443_uniq")

# # 특정 컬렉션의 모든 데이터 삭제
# db.diaryapp_wishlist.delete_many({})

# 특정 컬렉션 삭제 (문서와 인덱스 모두 삭제)
# db.diaryapp_wishlist.drop()



# 컬렉션 삭제
db.diaryapp_wishlist.drop()
# 새 컬렉션 생성 (컬렉션을 사용하려면 데이터를 삽입하면 자동으로 생성됨)
collection = db.diaryapp_wishlist
db.create_collection('diaryapp_wishlist')
# collection.insert_one({
#     "user_email": "example@example.com",
#     "plan_id": "Example Place",
# })
collection.insert_one({
    "user_email": "user_email",
    "plan_id": "plan_id",
    "place": "place",
    "province": "province",
    "city": "city",
    "travel_dates": {}
})


# 데이터베이스의 컬렉션 목록 출력
collections = db.list_collection_names()
if 'diaryapp_wishlist' in collections:
    print(True)
print("Collections:", collections)

# 인덱스 정보를 가져옵니다.
indexes = db.diaryapp_wishlist.index_information()
print(indexes)
#
#
# # 인덱스 추가
# collection.create_index(
#     [("user_email", ASCENDING), ("place", ASCENDING)],
#     unique=True,  # 중복을 방지하기 위한 제약 조건
#     name="diaryapp_wishlist_user_email_place_uniq"
# )