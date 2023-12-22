import requests
from pydantic import BaseModel

from app.api.data_models import PyStaffTransaction

api_url = "https://hub.dev.ingeniumua.be/api/v1/"


class PyToken(BaseModel):
    access_token: str
    refresh_token: str


def authenticate(username: str, password: str) -> PyToken | str:
    response = requests.post(
        api_url + "auth/token",
        {'username': username, 'password': password})
    if response.status_code == 200:  # OK
        return PyToken(**response.json())
    else:
        return "login_error"


def refresh_token(token: PyToken) -> PyToken:
    response = requests.post(
        api_url + "auth/refresh",
        {token})
    if response.status_code == 200:  # OK
        return PyToken(**response.json())


def get_userdata(uuid: str | None = None) -> dict:
    response = requests.get(url=api_url + "staff/user/" + uuid)
    if response.status_code == 200:
        return {"lidstatus": response.json()["roles"]["is_lid"],
                "voornaam": response.json()["user_detail"]["voornaam"],
                "achternaam": response.json()["user_detail"]["achternaam"]}
    else:
        return {"lidstatus": False, "voornaam": "", "achternaam": ""}


def update_validity(interaction_id):
    requests.patch(url=api_url + "staff/transaction/" + str(interaction_id), json={"validity": "consumed"})


def get_transactions(token: PyToken,
                     checkout_id: str | None = None, user_id: str | None = None, item: str | None = None,
                     status: str | None = None, validity: str | int | None = None,
                     limit: int = 50, offset: int = 0, ordering: str | None = None) -> list[PyStaffTransaction] | str:
    """
    Get list of PyTransaction models by filter parameters, limit and offset, first degree ordering allowed

     Examples
    --------
    >>> get_transactions(token, limit=50, offset=0, ordering='date_created', status='SUCCESSFUL', validity=1)
    [PyStaffTransaction(), ..]

     Parameters
    ----------
    :param ordering:
    :param token:
    :param checkout_id:
    :param user_id:
    :param item:
    :param status:
    :param validity:
    :param limit:
    :param offset:

    Returns
    -------
    :return: list[PyStaffTransaction]
    """
    query_params = "?"
    func_args = locals()
    for non_query_var in ('token', 'query_params'):
        func_args.pop(non_query_var)
    for arg, value in func_args.items():
        if value or value == 0:  # offset=0 is matches on None, solving edge case
            query_params += "&" + str(arg) + "=" + str(value)

    response = requests.get(url=api_url + "staff/transaction" + query_params,
                            headers={"authorization": "Bearer " + token.access_token})
    if response.status_code == 200:
        response_body: list[dict] = response.json()  # Already correctly parsed as list of dictionaries
        return list(PyStaffTransaction(**value) for value in response_body)
    elif response.status_code == 401 or response.status_code == 500:  # token has expired
        return "login_invalid"
    elif response.status_code == 406:  # uuid has invalid form
        return "uuid_invalid"
    else:
        print(response.json())
