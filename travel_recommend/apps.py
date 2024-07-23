import subprocess
import threading
from django.apps import AppConfig
import sys


class TravelRecommendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "travel_recommend"

    def ready(self):
        # FastApi 서버를 비동기로 실행
        threading.Thread(target=self.start_fastapi_server).start()

    def start_fastapi_server(self):
        subprocess.Popen([sys.executable,"-m", "uvicorn","travel_recommend.fastapi_app.app:app", "--reload"])