import hub_api

EMAIL = "admin@ingeniumua.be"
PASSWORD = "pw"


class TestAuthentication:
    def test_authenticate(self):
        auth_token = hub_api.authenticate(username=EMAIL, password=PASSWORD)
        assert auth_token

