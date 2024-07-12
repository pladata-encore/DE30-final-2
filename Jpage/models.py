from djongo import models

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
