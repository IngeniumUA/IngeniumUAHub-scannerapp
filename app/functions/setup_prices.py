from kivy.storage.jsonstore import JsonStore

from app.functions.variables import variables


def set_up_prices():
    # set prices of events that are not in the file to -1
    prices_json = JsonStore("app/functions/niet-lid_price_list.json")
    prices = dict(prices_json)  # convert the file to a dictionary
    if prices != dict():
        prices = prices["data"]

    # check that all events have a niet-lid price
    # if this is not the case, set the price to -1 so this can be detected later
    for event_uuid in list(variables["event_items"].values()):
        if event_uuid not in list(prices.keys()):
            prices[event_uuid] = -1
    prices[""] = 0  # set the price of the select option to 0
    prices_json["data"] = prices  # write the dictionary to the file
