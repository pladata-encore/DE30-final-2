import requests

def create_nickname():
    response = requests.post('http://localhost:5000/generate-nickname/')
    if response.status_code == 200:
        return response.json()
