import requests
from pydantic import BaseModel

api_url = "http://127.0.0.1:8000/"


class PyToken(BaseModel):
    access_token: str
    refresh_token: str


def authenticate(username: str, password: str) -> PyToken:
    response = requests.post(
        api_url + "api/v1/auth/token",
        {'username': username, 'password': password})
    if response.status_code == 200:  # OK
        return PyToken(**response.json())
