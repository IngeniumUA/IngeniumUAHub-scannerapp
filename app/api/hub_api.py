import requests
from pydantic import BaseModel
import datetime

from app.api.data_models import PyStaffTransaction

api_url = "https://hub.dev.ingeniumua.be/api/v1/"  # main api link that will be appended based on what is required


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
            api_url + "auth/refresh", {token})
    except requests.exceptions.ConnectionError:  # return empty token
        return PyToken()

    if response.status_code == 200:  # OK
        return PyToken(**response.json())
    else:  # return empty token
        return PyToken()


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
    else:  # return empty user
        return {"lidstatus": False, "voornaam": "", "achternaam": ""}


def update_validity(token: PyToken, interaction_id: int, validity: str, count: int) -> None:
    """
    Updates the validity of the interaction with the given count

    Examples
    --------
    >>> update_validity(token, 100, "consumed", 2)
    None

    Parameters
    ----------
    :param token:
    :param interaction_id:
    :param validity:
    :param count:

    Returns
    -------
    :return: None
    """

    try:  # try statement to prevent crashing when unable to connect
        requests.patch(url=api_url + "staff/transaction/" + str(interaction_id),
                       json={"validity": validity, "count": count},
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


def get_niet_lid_price(token: PyToken, product_blueprint_id: int) -> float:
    """
    gets the niet lid price for the product with the given product blueprint

    Examples
    --------
    >>> get_niet_lid_price(token, 100)
    float

    Parameters
    ----------
    :param token:
    :param product_blueprint_id:

    Returns
    -------
    :return: float
    """

    try:  # try statement to prevent crashing when unable to connect
        response = requests.get(url=api_url + "staff/blueprint/" + str(product_blueprint_id),
                                headers={"authorization": "Bearer " + token.access_token})
    except requests.exceptions.ConnectionError:  # return very high price to alarm the user that something went wrong
        return 999

    if response.status_code == 200:  # OK
        policy_list = []
        for policy in response.json()["price_policies"]:
            policy_list.append(policy["price"])
        return max(policy_list)  # find the highest price in the blueprint as this will always be the niet lid price
    else:  # return very high price to alarm the user that something went wrong
        return 999
