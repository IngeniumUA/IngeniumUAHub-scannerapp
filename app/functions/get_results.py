from kivy.storage.jsonstore import JsonStore
from app.api.data_models import PyStaffTransaction
from app.api.hub_api import get_transactions, get_userdata

from app.functions.variables import variables


def get_results(token, event_uuid: str, uuid: str | None = None, ids: int | None = None, run_userdata: bool = True) -> dict:
    """
    combine the results of get_transactions and get_userdata and return them in a dictionary that the app can use
                                                                                or an error with the "validity" key

    Examples
    --------
    >>> get_results(token, "<UUID>", "<UUID>", True)
    {"validity": validity, "table_data": table_data, "email": user_email, "checkout_status": status,
                "voornaam": voornaam, "naam": achternaam, "lidstatus": lidstatus}
    or {"validity": "emptyEvent"} when no event was selected
    or {"validity": "APITokenError"} when problems with connecting to the server
    or {"validity": "UUIDError"} when problems with the scanned UUID

    Parameters
    ----------
    :param token:
    :param event_uuid:
    :param uuid:
    :param ids:
    :param run_userdata:

    Returns
    -------
    :return: dict()
    """

    if event_uuid == "":  # if no event is selected
        return {"validity": "emptyEvent"}

    if uuid is not None:
        uuid = str(uuid)
    transactions: list[PyStaffTransaction] = get_transactions(token=token, interaction_uuid=uuid, interaction_id=ids)
    table_data = []
    event_tickets = []

    if transactions == "login_invalid":  # break out when login error
        return {"validity": "APITokenError"}

    # break out when UUID error or when UUID has no transactions
    if transactions == [] or transactions == "uuid_invalid":
        return {"validity": "UUIDError"}

    # loop through all found transactions to get info in the correct form
    for transaction in transactions:
        # this should be impossible, when detected everything should be stopped and an error should be thrown
        if transaction.validity.value == "forbidden":
            return {"validity": "UUIDError"}

        # if the transaction wasn't successful, handle ticket as if it is consumed
        if transaction.status.value != "SUCCESSFUL":
            transaction.validity.value = "consumed"

        # get products in form eg "1 x event \n sub-event"
        products_str = str()
        products_str += (str(transaction.interaction.item_name.lower()) + ':\n'
                         + str(transaction.product["name"]))

        # save tickets when they are for the given event
        if transaction.interaction.item_id == event_uuid or event_uuid == "alle":
            event_tickets.append(transaction)
            if transaction.validity.value == "invalid":  # if invalid, the "to pay" price has to be calculated
                prices_json = JsonStore("app/functions/niet-lid_price_list"+variables["api_suffix"]+".json")
                prices = dict(prices_json)  # convert the file to a dictionary
                if prices != dict():
                    prices = prices["data"]

                niet_lid_price = prices[event_uuid]
                to_pay = niet_lid_price - float(transaction.amount)  # niet lid price - already paid
            else:
                to_pay = 0
            to_pay = '€' + "%.2f" % to_pay  # set to pay to form "€00.00"
        else:
            to_pay = "NVT"  # tickets for other events should be ignored

        # set up table data for dropdown table
        table_data.append(("[size=30]" + products_str + "[/size]",
                           "[size=30]" + str(transaction.validity.value) + "[/size]",
                           "[size=30]" + to_pay + "[/size]",
                           "[size=30]" + str(transaction.interaction.id) + "[/size]"))

    # run when userdata is asked
    if run_userdata:
        userdata = get_userdata(token, transactions[0].interaction.user_id)
        if "error" in list(userdata.keys()):
            if userdata["error"] == "expired token":
                return {"validity": "APITokenError"}  # return expired token
    else:
        userdata = {"voornaam": "", "achternaam": "", "lidstatus": False}

    i = 0
    if event_tickets:  # when there are tickets for given events
        for i in range(len(event_tickets)):
            # find first non consumed ticket, if none, give last ticket
            if event_tickets[i].validity.value != "consumed":
                break
        # return data for first non consumed item or last item
        return {"validity": event_tickets[i].validity.value,
                "table_data": table_data,
                "email": event_tickets[i].interaction.user_email,
                "checkout_status": event_tickets[i].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"]),
                "notes": event_tickets[i].note}
    else:
        # the scanned UUID was valid but no tickets for the given event were found, return all acquired data
        return {"validity": "eventError",
                "table_data": table_data,
                "email": transactions[0].interaction.user_email,
                "checkout_status": transactions[0].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"]),
                "notes": transactions[0].note}
