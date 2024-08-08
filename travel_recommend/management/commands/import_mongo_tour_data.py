# import_mongo_tour_data.py
from pymongo import MongoClient
from myproject.settings import DATABASES
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from travel_recommend.models import Region, Subregion, Destination

client = MongoClient(DATABASES['default']['CLIENT']['host'])
db = client[DATABASES['default']['NAME']]

# Region 데이터 삽입
print("Inserting Region data...")
area_codes = db.areaCode.find()
for area_code in area_codes:
    region, created = Region.objects.get_or_create(code=area_code['code'], name=area_code['name'])
print("Region data inserted.")

# Subregion 데이터 삽입
print("Inserting Subregion data...")
city_districts = db.cityDistrict.find()
for city_district in city_districts:
    try:
        region = Region.objects.get(code=city_district['areacode'])
        subregion, created = Subregion.objects.get_or_create(region=region, code=city_district['code'], name=city_district['name'])
    except Exception as e:
        print(f"Error inserting subregion with code {city_district['code']}: {e}")
print("Subregion data inserted.")

# Destination 데이터 삽입
print("Inserting Destination data...")
destinations = db.destinations.find()
for destination in destinations:
    try:
        region = Region.objects.get(code=destination['areacode'])
        subregion = Subregion.objects.get(region=region, code=destination['sigungucode'])
        Destination.objects.create(
            addr1=destination['addr1'],
            addr2=destination.get('addr2', ''),
            areacode=region,
            sigungucode=subregion,
            title=destination['title'],
            overview=destination['overview'],
            mapx=destination.get('mapx', None),
            mapy=destination.get('mapy', None)
        )
    except Exception as e:
        print(f"Error inserting destination with title {destination['title']}: {e}")
print("Destination data inserted.")
print("Data import completed.")
