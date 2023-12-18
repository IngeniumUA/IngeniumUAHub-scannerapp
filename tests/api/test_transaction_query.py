import pytest
import requests
import hub_api

EMAIL = "admin@ingeniumua.be"
PASSWORD = "pw"


class TestTransactionQuery:
    def test_no_argument(self):
        auth_token = hub_api.authenticate(username=EMAIL, password=PASSWORD)
        assert auth_token

        result = hub_api.get_transactions(auth_token)
        assert result
