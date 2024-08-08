from django.db import models
from django.conf import settings

class Region(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Subregion(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

## 숙소 컬렉션
class Accommodation(models.Model):
    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    telephone = models.CharField(max_length=20)
    image_url = models.URLField(blank=True, null=True)
    mapx = models.FloatField()
    mapy = models.FloatField()
    rating = models.FloatField()
    def __str__(self):
        return self.title

## 여행지 컬렉션 (통합된 컬렉션)
class Destination(models.Model):
    addr1 = models.CharField(max_length=255)
    addr2 = models.CharField(max_length=255, blank=True)
    areacode = models.ForeignKey(Region, on_delete=models.CASCADE)
    sigungucode = models.ForeignKey(Subregion, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    overview = models.TextField()
    mapx = models.FloatField()  # 추가된 필드
    mapy = models.FloatField()  # 추가된 필드
    category = models.CharField(max_length=50)  # 추가된 필드: 카테고리 (예: 관광지, 문화시설 등)

    def __str__(self):
        return self.title

class UserPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    region = models.CharField(max_length=100)
    subregion = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    pets_allowed = models.CharField(max_length=3, choices=[('yes','Yes'), ('no','No')])
    pet_size = models.CharField(max_length=6, choices=[('small','Small'),('medium','Medium'),('large','Large')], blank=True, null=True)
    preferred_foods = models.JSONField()
    preferred_activities = models.JSONField()
    preferred_accommodation = models.JSONField()

    def __str__(self):
        return f"Preferences of {self.user.username}"

class TravelPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    destinations = models.ManyToManyField(Destination, through='PlanDestination')

    def __str__(self):
        return f"Travel Plan from {self.start_date} to {self.end_date} for {self.user.username}"

class PlanDestination(models.Model):
    travel_plan = models.ForeignKey(TravelPlan, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = ('travel_plan', 'order')
        ordering = ['order']

    def __str__(self):
        return f"{self.destination.title} in Plan {self.travel_plan.id} at Order {self.order}"
