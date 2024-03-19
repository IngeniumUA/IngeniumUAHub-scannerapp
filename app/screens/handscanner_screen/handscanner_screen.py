from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config
from kivy.storage.jsonstore import JsonStore

import datetime

from app.api.hub_api import get_all_events
from app.functions.get_results import get_results
from app.functions.variables import variables
from app.functions.send_to_screen import send_to_screen
from app.functions.setup_prices import set_up_prices

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class HandscannerScreen(MDScreen):
    kv = Builder.load_file('app/screens/handscanner_screen/handscanner_screen.kv')  # load the associated kv file

    # called when going to this screen. prev_result is reset so a scanned code can be rescanned
    # when coming from the login screen, the current active events should be loaded into a dropdown
    def on_pre_enter(self):
        variables["prev_result"] = ""
        self.load_dropdown_events_hand()
        if variables["current_selected_event"] != "":
            variables["main_button_events_hand"].text = variables["current_selected_event"]
        self.ids.response.text = ""
        self.ids.response.cursor = (0,0)
        self.ids.response.focus = True

    def price_is_set(self, event_uuid: str) -> bool:  # returns whether the price of an event is set
        prices_json = JsonStore("app/functions/niet-lid_price_list" + variables["api_suffix"] + ".json")
        prices = dict(prices_json)  # convert the file to a dictionary
        if prices != dict():
            prices = prices["data"]

        if event_uuid in list(prices.keys()):
            return prices[event_uuid] != -1
        else:
            return False

    @mainthread
    def got_result(self):  # called when a qr code is detected, the string from the code is in result
        result = self.ids.response.text

        # when code is the same as the previous code, don't scan again to prevent unneeded api calls
        if result == variables["prev_result"]:
            return

        # store the used result, so it won't be used util user gets sent to other screen
        variables["prev_result"] = result

        # get data from the qr code and store used data for the api call in variables for access on other screens
        response_dict = get_results(variables["token"],
                                    variables["event_items"][variables["main_button_events_hand"].text], uuid=result)
        variables["prev_args"] = {"token": variables["token"], "uuid": result, "id": None,
                                  "event_uuid": variables["event_items"][variables["main_button_events_hand"].text]}

        # when there is data to be gained from the qr code, save them in variables for access on other screens
        if (response_dict["validity"] == "valid"
                or response_dict["validity"] == "invalid"
                or response_dict["validity"] == "consumed"
                or response_dict["validity"] == "manually_verified"
                or response_dict["validity"] == "eventError"):
            variables["voornaam"] = response_dict["voornaam"]
            variables["naam"] = response_dict["naam"]
            variables["email"] = response_dict["email"]
            variables["validity"] = response_dict["validity"]
            variables["lidstatus"] = response_dict["lidstatus"]
            variables["checkout_status"] = response_dict["checkout_status"]
            variables["notes"] = response_dict["notes"]
            variables["table_data"] = response_dict["table_data"]

        # if the event price is set, send user to the right screen, else send user to niet_lid_price page
        if self.price_is_set(variables["event_items"][variables["main_button_events_hand"].text]):
            variables["prev_screen"] = "handscanner"
            send_to_screen(self, response_dict["validity"])
        else:
            self.goto_niet_lid_price_screen()

    def goto_niet_lid_price_screen(self):  # when icon is clicked, the user is sent to the niet_lid_price screen
        variables["prev_screen"] = "handscanner"
        self.manager.transition.direction = "left"
        self.manager.current = "niet_lid_price"

    def load_dropdown_events_hand(self):
        # create dropdown to select which event price should be changed
        self.dropdown_events_hand = DropDown()
        for item in list(variables["event_items"].keys()):
            opts_events_hand = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_events_hand.bind(on_release=
                                   lambda opt_events_hand: self.dropdown_events_hand.select(opt_events_hand.text))
            opts_events_hand.bind(on_release=lambda opt_events_hand: self.save_selected_event(opt_events_hand.text))
            self.dropdown_events_hand.add_widget(opts_events_hand)

        variables["main_button_events_hand"] = Button(
            text='Selecteer een evenement',
            size_hint=(0.9, None),
            height=dp(30),
            pos_hint={'x': 0.05, 'y': 0.92},
            font_name='app/assets/D-DIN.otf')
        variables["main_button_events_hand"].bind(on_release=self.dropdown_events_hand.open)
        variables["main_button_events_hand"].bind(on_release=lambda x: self.reset_event_empty())
        self.dropdown_events_hand.bind(on_select=
                                        lambda instance, x: setattr(variables["main_button_events_hand"], 'text', x))
        self.add_widget(variables["main_button_events_hand"], index=1)

    # when an event is chosen, the error message should disappear and the qr code should be able to be rescanned
    def reset_event_empty(self):
        self.ids.event_empty.opacity = 0
        variables["prev_result"] = ""

    def save_selected_event(self, event):
        variables["current_selected_event"] = event
