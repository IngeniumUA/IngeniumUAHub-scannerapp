import ast

import requests
from pydantic import BaseModel

from data_models import PyStaffTransaction

api_url = "http://127.0.0.1:8000/api/v1/"


class PyToken(BaseModel):
    access_token: str
    refresh_token: str


def authenticate(username: str, password: str) -> PyToken:
    response = requests.post(
        api_url + "auth/token",
        {'username': username, 'password': password})
    if response.status_code == 200:  # OK
        return PyToken(**response.json())


def get_transactions(token: PyToken,
                    checkout_id: str | None = None, user_id: str | None = None, item_id: str | None = None,
                     status: str | None = None, validity: str | int | None = None,
                     limit: int = 50, offset: int = 0, ordering: str | None = None) -> list[PyStaffTransaction]:
    """
    Get list of PyTransaction models by filter parameters, limit and offset, first degree ordering allowed

     Parameters
    ----------
    :param token:
    :param checkout_id:
    :param user_id:
    :param item_id:
    :param status:
    :param validity:
    :param limit:
    :param offset:

    Returns
    -------
    :return: list[
    """
    query_params = "?"
    func_args = locals()
    for non_query_var in ('token', 'query_params'):
        func_args.pop(non_query_var)
    for arg, value in func_args.items():
        if value or value == 0:  # offset=0 is matches on None, solving edge case
            query_params += "&" + str(arg) + "=" + str(value)

    response = requests.get(url=api_url + "staff/transaction" + query_params, headers={"authorization": "Bearer " + token.access_token})
    if response.status_code == 200:
        response_body: list[dict] = response.json()  # Already correctly parsed as list of dictionaries
        return list(PyStaffTransaction(**value) for value in response_body)
