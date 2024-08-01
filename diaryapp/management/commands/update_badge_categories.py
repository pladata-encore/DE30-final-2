from django.conf import settings
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from diaryapp.models import CommandFlag  # 플래그 모델 임포트


class Command(BaseCommand):
    help = 'Update categoryCode1 and categoryCode3 in the Badge collection'
    # 업데이트는 나중에 추가하기...

    def handle(self, *args, **kwargs):
        flag_name = 'update_badge_categories'

        # Check if the command has already been executed
        flag, created = CommandFlag.objects.get_or_create(name=flag_name)
        if flag.executed:
            self.stdout.write(self.style.SUCCESS('Command has already been executed.'))
            return

        client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        db = client[settings.DATABASES['default']['NAME']]
        badge_collection = db['diaryapp_badge']
        categoryCode1_collection = db['categoryCode1']
        categoryCode3_collection = db['categoryCode3']

        def update_badge_categories():
            for badge in badge_collection.find():
                name = badge.get('name')
                cat3 = categoryCode3_collection.find_one({'name':name})
                if cat3 :
                    categoryCode1_code = cat3.get('cat1_code')
                    categoryCode3_code = cat3.get('code')
                else :
                    cat1 = categoryCode1_collection.find_one({'name': name})
                    if cat1 :
                        categoryCode1_code = cat1.get('code')
                        categoryCode3_code = None
                    else :
                        categoryCode1_code = None
                        categoryCode3_code = None

                # Badge 문서 업데이트
                badge_collection.update_one(
                    {'_id': badge['_id']},
                    {'$set': {'categoryCode1': categoryCode1_code, 'categoryCode3': categoryCode3_code}}
                )

        # 명령어 실행
        self.stdout.write(self.style.SUCCESS('Starting badge category update...'))
        update_badge_categories()
        self.stdout.write(self.style.SUCCESS('Badge category update completed!'))

        # Set the flag as executed
        flag.executed = True
        flag.save()

