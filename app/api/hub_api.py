import requests
from pydantic import BaseModel
import datetime

from app.api.data_models import PyStaffTransaction


# main api link that will be appended based on what is required
# local
# api_url = "http://127.0.0.1:8000/api/v1/"
# dev
# api_url = "https://hub.dev.ingeniumua.be/api/v1/"
# production
api_url = "https://hub.ingeniumua.be/api/v1/"


class PyToken(BaseModel):  # the token used for verifying user
    access_token: str
    refresh_token: str


def authenticate(username: str, password: str) -> PyToken | str:
    """
    Authenticate the user based on credentials and return the token if successful, otherwise return what error occurred

    Examples
    --------
    >>> authenticate(username, password)
    PyToken(access_token="<PASSWORD>", refresh_token="<PASSWORD>")
    or "server_error" when unable to connect to the server
    or "login_error" when unable to authenticate the user (likely invalid credentials)

    Parameters
    ----------
    :param username:
    :param password:

    Returns
    -------
    if successful
    :return: PyToken

    else
    :return: error in string form
    """

    try:  # try statement to prevent crashing when unable to connect
        response = requests.post(
            api_url + "auth/token",
            {'username': username, 'password': password})
    except requests.exceptions.ConnectionError:
        return "server_error"

    if response.status_code == 200:  # OK
        return PyToken(**response.json())
    else:
        return "login_error"


def refresh_token(token: PyToken) -> PyToken:
    """
    Refresh the access token based on the refresh token

    Examples
    --------
    >>> refresh_token(token)
    PyToken(access_token="<PASSWORD>", refresh_token="<PASSWORD>")
    or PyToken(access_token="", refresh_token="") when unable to refresh the access token

    Parameters
    ----------
    :param token:

    Returns
    -------
    :return: PyToken
    """

    try:  # try statement to prevent crashing when unable to connect
        response = requests.post(
            api_url + "auth/refresh", json={"access_token":  token.access_token,
                                            "refresh_token": token.refresh_token, "token_type": "Bearer"})
    except requests.exceptions.ConnectionError:  # return empty token
        return PyToken(access_token="", refresh_token="")

    if response.status_code == 200:  # OK
        return PyToken(**response.json())
    else:  # return empty token
        return PyToken(access_token="", refresh_token="")


def check_new_user(token: PyToken, user_email: str) -> dict | str:
    """
    Check if the user is lid or not and get its uuid, return error message if user not found

    Examples
    --------
    >>> check_new_user(token, user_email="<EMAIL>")
    {"lid": True, "uuid": "<UUID>"} or
    "User not found"

    Parameters
    ----------
    :param token:
    :param user_email:

    Returns
    -------
    if user exists
    :return: dict
    else
    :return: str
    """

    try:  # try statement to prevent crashing when unable to connect
        response = requests.get(url=api_url + "staff/user?limit=50&offset=0&user_email="+user_email.replace("@", "%40"),
                                headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:  # return user does not exist
        return "User not found"

    response_dict = dict()
    if response.status_code == 200:  # OK
        if response.json():
            response_dict["lid"] = response.json()[0]["roles"]["is_lid"]
            response_dict["uuid"] = response.json()[0]["uuid"]
            return response_dict
        else:  # user does not exist
            return "User not found"
    elif response.status_code == 401:  # user not found or token expired
        return "User not found"


def get_userdata(token: PyToken, uuid: str | None = None) -> dict:
    """
    gets userdata based on uuid from database

    Examples
    --------
    >>> get_userdata(token, uuid="<UUID>")
    {"lidstatus": bool, "voornaam": str, "achternaam": str}

    Parameters
    ----------
    :param token:
    :param uuid:

    Returns
    -------
    :return: dict()
    """

    try:  # try statement to prevent crashing when unable to connect
        response = requests.get(url=api_url + "staff/user/" + uuid,
                                headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:  # return empty user
        return {"lidstatus": False, "voornaam": "", "achternaam": ""}

    if response.status_code == 200:  # OK
        return {"lidstatus": response.json()["roles"]["is_lid"],
                "voornaam": response.json()["user_detail"]["voornaam"],
                "achternaam": response.json()["user_detail"]["achternaam"]}
    elif response.status_code == 401:  # token expired
        return {"error": "expired token"}
    else:  # return empty user
        return {"lidstatus": False, "voornaam": "", "achternaam": ""}


def patch_transaction(token: PyToken, interaction_id: int,
                      validity: str | None = None, count: int | None = None,
                      user: str | None = None, force_patch: bool = True) -> None:
    """
    Updates the transaction of the interaction with the given parameters

    Examples
    --------
    >>> patch_transaction(token, 100, "consumed", 2)
    None

    Parameters
    ----------
    :param token:
    :param interaction_id:
    :param validity:
    :param count:
    :param user:
    :param force_patch:

    Returns
    -------
    :return: None
    """

    # set up dict for api call using given parameters except for token
    query_params = dict()
    func_args = locals()
    for non_query_var in ('token', 'query_params', 'interaction_id'):
        func_args.pop(non_query_var)
    func_args_for = func_args.copy()
    for arg, value in func_args_for.items():
        if not value:
            func_args.pop(arg)

    try:  # try statement to prevent crashing when unable to connect
        requests.patch(url=api_url + "staff/transaction/" + str(interaction_id),
                       json=func_args,
                       headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:  # nothing gets returned anyway so just pass
        pass


def get_transactions(token: PyToken,
                     checkout_id: str | None = None, user_id: str | None = None, item: str | None = None,
                     status: str | None = None, validity: str | int | None = None,
                     limit: int = 50, offset: int = 0, ordering: str | None = None) -> list[PyStaffTransaction] | str:
    """
    Get list of PyTransaction models by filter parameters, limit and offset, first degree ordering allowed

     Examples
    --------
    >>> get_transactions(token, limit=50, offset=0, ordering='date_created', status='SUCCESSFUL', validity=1)
    [PyStaffTransaction(), ...]
    or "login_invalid" when unable to connect to server or invalid credentials
    or "uuid_error" when uuid is not correctly structured (when uuid was most likely fabricated by the user)

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
    if successful
    :return: list[PyStaffTransaction]

    else
    :return: error in string form
    """

    # set up string for api call using given parameters except for token
    query_params = "?"
    func_args = locals()
    for non_query_var in ('token', 'query_params'):
        func_args.pop(non_query_var)
    for arg, value in func_args.items():
        if value or value == 0:  # offset=0 is matches on None, solving edge case
            query_params += "&" + str(arg) + "=" + str(value)

    try:  # try statement to prevent crashing when unable to connect
        response = requests.get(url=api_url + "staff/transaction" + query_params,
                                headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:
        return "login_invalid"

    if response.status_code == 200:  # OK
        response_body: list[dict] = response.json()  # Already correctly parsed as list of dictionaries
        return list(PyStaffTransaction(**value) for value in response_body)
    elif response.status_code == 401 or response.status_code == 500:  # token has expired
        return "login_invalid"
    elif response.status_code == 406:  # uuid has invalid form
        return "uuid_invalid"


def get_all_events(token: PyToken, current_date: datetime.datetime) -> dict:
    """
    gets all current ongoing events and returns them in a dictionary with the name as key and the uuid as value

    Examples
    --------
    >>> get_all_events(token, datetime.datetime.now())
    {"event_name": event_uuid, ...}

    Parameters
    ----------
    :param token:
    :param current_date:

    Returns
    -------
    :return: dict()
    """

    current_date -= datetime.timedelta(days=1)  # add 1 day just in case
    moment = "&end_date_ge=" + str(current_date).replace(":", "%3A").replace(" ", "T") + "%2B00%3A00"
    try:  # try statement to prevent crashing when unable to connect
        response = requests.get(url=api_url + "staff/event?limit=50&offset=0&available=true&disabled=false" + moment,
                                headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:  # return empty dictionary
        return dict()

    if response.status_code == 200:  # OK
        return_dict: dict = dict()
        for event in response.json():
            if event["event_item"] is not None:
                return_dict[event["item"]["name"]] = event["item"]["uuid"]
        return return_dict
    else:  # return empty dictionary
        return dict()
