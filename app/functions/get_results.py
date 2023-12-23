from app.api.data_models import PyStaffTransaction
from app.api.hub_api import get_transactions, get_userdata


def get_results(api_token, uuid: str, event):
    """
    :param api_token:
    :param uuid:
    :param event:
    :return:
    """
    transactions: list[PyStaffTransaction] = get_transactions(token=api_token, checkout_id=str(uuid))
    table_data = []
    transaction_to_save = []
    if transactions == "login_invalid":
        return {"validity": "APITokenError"}
    if transactions == [] or transactions == "uuid_invalid":
        return {"validity": "UUIDError"}
    for transaction in transactions:
        products_str = str()
        validities_str = str()
        products_str += (str(transaction.count) + " x "
                         + str(transaction.interaction.item_name.lower()) + ':\n'
                         + str(transaction.product["name"]))
        validities_str += str(transaction.validity.value)
        amount = '€' + "%.2f" % transaction.amount
        table_data.append(("[size=15]" + products_str + "[/size]",
                           "[size=15]" + validities_str + "[/size]",
                           "[size=15]" + amount + "[/size]"))
        if transaction.interaction.item_name.lower() == event:
            transaction_to_save.append(transaction)
    if transaction_to_save:
        userdata = get_userdata(transaction_to_save[0].interaction.user_id)

        transaction_to_save_len = len(transaction_to_save)
        item_to_return = 0
        for item_to_return in range(transaction_to_save_len):
            if (transaction_to_save[item_to_return].validity.value != "consumed"
                    or item_to_return == transaction_to_save_len - 1):
                break

        return {"validity": transaction_to_save[item_to_return].validity.value,
                "id": transaction_to_save[item_to_return].interaction.id,
                "table_data": table_data,
                "email": transaction_to_save[item_to_return].interaction.user_email,
                "checkout_status": transaction_to_save[item_to_return].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}
    else:
        userdata = get_userdata(transactions[0].interaction.user_id)
        return {"validity": "eventError",
                "table_data": table_data,
                "email": transactions[0].interaction.user_email,
                "checkout_status": transactions[0].status.value,
                "voornaam": userdata["voornaam"],
                "naam": userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}
