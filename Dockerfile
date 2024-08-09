# Python 3.9 이미지를 기반으로 합니다.
FROM python:3.12

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일들을 컨테이너로 복사
COPY requirements.txt /app/
COPY . /app/

# 필요한 패키지 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# MongoDB 클라이언트 설치 (만약 필요하다면)
RUN pip install --upgrade pip && apt-get update && apt-get install -y mongodb-clients

# 포트 설정 (Django의 기본 포트는 8000입니다)
EXPOSE 8000

# 서버 실행
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]