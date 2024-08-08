import subprocess
import threading
from django.apps import AppConfig
import sys


class TravelRecommendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "travel_recommend"
