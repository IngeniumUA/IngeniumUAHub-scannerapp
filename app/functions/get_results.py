from app.api.data_models import PyStaffTransaction
from app.api.hub_api import get_transactions, get_userdata, get_niet_lid_price


def get_results(api_token, uuid: str, event_uuid, run_userdata: bool = True) -> dict:
    """
    :param api_token:
    :param uuid:
    :param event_uuid:
    :return:
    """
    if event_uuid == "":
        return {"validity": "emptyEvent"}
    transactions: list[PyStaffTransaction] = get_transactions(token=api_token, checkout_id=str(uuid))
    table_data = []
    event_tickets = []
    if transactions == "login_invalid":
        return {"validity": "APITokenError"}
    if transactions == [] or transactions == "uuid_invalid":
        return {"validity": "UUIDError"}
    for transaction in transactions:
        if transaction.validity.value == "forbidden":
            event_tickets = ["forbidden"]
            break
        products_str = str()
        products_str += (str(transaction.count) + " x "
                         + str(transaction.interaction.item_name.lower()) + ':\n'
                         + str(transaction.product["name"]))
        if transaction.interaction.item_id == event_uuid:
            event_tickets.append(transaction)
            if transaction.validity.value == "invalid":
                niet_lid_price = get_niet_lid_price(api_token, transaction.product_blueprint_id)
                to_pay = niet_lid_price*transaction.count - float(transaction.amount)
            else:
                to_pay = 0
            to_pay = '€' + "%.2f" % to_pay
        else:
            to_pay = "NVT"
        table_data.append(("[size=30]" + products_str + "[/size]",
                           "[size=30]" + str(transaction.validity.value) + "[/size]",
                           "[size=30]" + to_pay + "[/size]",
                           "[size=30]" + str(transaction.interaction.id) + "[/size]"))
    if run_userdata:
        userdata = get_userdata(api_token, transactions[0].interaction.user_id)
    else:
        userdata = {"voornaam": "", "achternaam": "", "lidstatus": False}
    i = 0
    if event_tickets != [] and event_tickets != ["forbidden"]:
        for i in range(len(event_tickets)):
            if event_tickets[i].validity.value != "consumed":
                break
        return {"validity": event_tickets[i].validity.value,
                "table_data": table_data,
                "email": event_tickets[i].interaction.user_email,
                "checkout_status": event_tickets[i].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}
    elif event_tickets == ["forbidden"]:
        return {"validity": "UUIDError"}
    else:
        return {"validity": "eventError",
                "table_data": table_data,
                "email": transactions[0].interaction.user_email,
                "checkout_status": transactions[0].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}
