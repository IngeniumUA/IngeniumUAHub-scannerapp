import pytest
import requests

BASEURL = "http://127.0.0.1:8000"

class TestApiRequest:
    @pytest.fixture
    def setup(self):
        pass

    def test_fetch_main(self):
        response = requests.get(BASEURL)
        assert response.status_code == 200
