from djongo import models

class categoryCode1(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    rnum = models.IntegerField()

    class Meta:
        db_table = 'categoryCode1'

class categoryCode2(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    cat1_code = models.CharField(max_length=10)
    rnum = models.IntegerField()

    class Meta:
        db_table = 'categoryCode2'

class categoryCode3(models.Model):
    _id = models.CharField(max_length=24, primary_key=True)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    cat2_code = models.CharField(max_length=10)
    rnum = models.IntegerField()

    class Meta:
        db_table = 'categoryCode3'
