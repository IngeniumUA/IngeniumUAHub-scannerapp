from app.api.data_models import PyStaffTransaction
from app.api.hub_api import get_transactions, get_userdata


def get_results(api_token, uuid: str, event_uuid) -> dict:
    """
    :param api_token:
    :param uuid:
    :param event_uuid:
    :return:
    """
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
        amount = '€' + "%.2f" % transaction.amount
        table_data.append(("[size=15]" + products_str + "[/size]",
                           "[size=15]" + str(transaction.validity.value) + "[/size]",
                           "[size=15]" + amount + "[/size]",
                           str(transaction.interaction.id)))
        if transaction.interaction.item_id == event_uuid:
            event_tickets.append(transaction)
    userdata = get_userdata(transactions[0].interaction.user_id)
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
