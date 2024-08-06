from djongo import models
from mongoengine import Document, StringField, DictField

class categoryCode1(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    rnum = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categoryCode1'

class categoryCode2(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    cat1_code = models.CharField(max_length=10)
    rnum = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categoryCode2'

class categoryCode3(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    cat2_code = models.CharField(max_length=10)
    rnum = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categoryCode3'

class areaBaseList(models.Model):
    areacode = models.CharField(max_length=10)
    sigungucode = models.CharField(max_length=10)
    cat3 = models.CharField(max_length=10)
    title = models.CharField(max_length=50)
    mapx = models.CharField(max_length=50)
    mapy = models.CharField(max_length=50)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'areaBaseList'

class areaCode(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'areaCode'

class cityDistrict(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=10)
    areacode = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'cityDistrict'

class jPlan:
    def __init__(self, plan_id, city, province, plan_title, email, days):
        self.plan_id =plan_id
        self.province = province
        self.city = city
        self.plan_title = plan_title
        self.email = email
        self.days = days

    def to_dict(self):
        return {
            'plan_id':self.plan_id,
            'province': self.province,
            'city': self.city,
            'plan_title': self.plan_title,
            'email': self.email,
            'days': self.days
        }

    @staticmethod
    def from_dict(data):
        return jPlan(
            plan_id=data.get('plan_id'),
            province=data.get('province'),
            city=data.get('city'),
            plan_title=data.get('plan_title'),
            email=data.get('email'),
            days=data.get('days')
        )
