from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.label import MDLabel
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

from app.functions.variables import variables
from app.functions.setup_prices import set_up_prices

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class NietLidPriceScreen(MDScreen):
    kv = Builder.load_file('app/screens/niet_lid_price_screen/niet_lid_price_screen.kv')  # load the associated kv file

    def on_pre_enter(self):
        self.load_dropdown_events_price()
        if variables["current_selected_event"] == "":
            self.set_price_label('Selecteer een evenement')
        else:
            self.set_price_label(variables["current_selected_event"])
            variables["main_button_events_price"].text = variables["current_selected_event"]

    def on_leave(self):  # when the screen is left, hide the popup if shown
        try:
            self.popup_reset_prijslijst.dismiss()
        except AttributeError:
            pass

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = variables["prev_screen"]

    def load_dropdown_events_price(self):
        # create dropdown to select which event price should be changed
        self.dropdown_events_price = DropDown()
        for item in list(variables["event_items"].keys()):
            opts_events_price = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_events_price.bind(on_release=
                                   lambda opt_events_price: self.dropdown_events_price.select(opt_events_price.text))
            opts_events_price.bind(on_release=lambda opt_events_price: self.set_price_label(opt_events_price.text))
            self.dropdown_events_price.add_widget(opts_events_price)

        variables["main_button_events_price"] = Button(
            text='Selecteer een evenement',
            size_hint=(0.9, None),
            height=dp(30),
            pos_hint={'x': 0.05, 'y': 0.92},
            font_name='app/assets/D-DIN.otf')
        variables["main_button_events_price"].bind(on_release=self.dropdown_events_price.open)
        self.dropdown_events_price.bind(on_select=
                                        lambda instance, x: setattr(variables["main_button_events_price"], 'text', x))
        self.add_widget(variables["main_button_events_price"], index=1)

    def set_price_label(self, event):  # set the text of the label to the curren price of the selected event
        prices_json = JsonStore("app/functions/niet-lid_price_list"+variables["api_suffix"]+".json")
        prices = dict(prices_json)  # convert the file to a dictionary
        if prices != dict():
            prices = prices["data"]

        if prices[variables["event_items"][event]] != -1:
            self.ids.niet_lid_price.text = 'Niet lid prijs: €' + "%.2f" % prices[variables["event_items"][event]]
        else:
            self.ids.niet_lid_price.text = 'Niet lid prijs: Niet ingesteld'

    def apply(self):  # apply the made changes
        prices_json = JsonStore("app/functions/niet-lid_price_list"+variables["api_suffix"]+".json")
        prices = dict(prices_json)  # convert the file to a dictionary
        if prices != dict():
            prices = prices["data"]

        # if no price is given, and the price has been set, keep the current price
        if (self.ids.new_price.text == "" and
                prices[variables["event_items"][variables["main_button_events_price"].text]] != -1):
            self.ids.new_price.text = str(prices[variables["event_items"][variables["main_button_events_price"].text]])
        # check if given price is a valid float, else return error message
        if not self.ids.new_price.text.replace(".", "").isnumeric():
            self.ids.price_not_num.opacity = 1
            return
        self.ids.price_not_num.opacity = 0  # reset the error message

        # set the new price
        prices[variables["event_items"][variables["main_button_events_price"].text]] = float(self.ids.new_price.text)
        prices_json["data"] = prices  # write the dictionary to the file

        self.manager.transition.direction = "right"
        self.manager.current = variables["prev_screen"]

    def show_reset_prijslijst(self):
        self.popup_reset_prijslijst = MDDialog(
            title="Prijslijst verwijderen",
            text="Ben je zeker dat je de prijslijst wilt wissen? Dit kan niet ongedaan gemaakt worden!",
            buttons=[
                MDFlatButton(
                    text="Annuleer",
                    font_name='app/assets/D-DIN.otf',
                    on_release=lambda x:self.close_reset_prijslijst()
                ),
                MDFlatButton(
                    text="Ga verder",
                    font_name='app/assets/D-DIN.otf',
                    on_release=lambda x: self.reset_prices()
                )
            ],
        )
        self.popup_reset_prijslijst.open()
    def close_reset_prijslijst(self):
        self.popup_reset_prijslijst.dismiss()

    def reset_prices(self):  # set the price list file to an empty dictionary
        JsonStore("app/functions/niet-lid_price_list"+variables["api_suffix"]+".json").clear()
        set_up_prices()
        self.popup_reset_prijslijst.dismiss()
