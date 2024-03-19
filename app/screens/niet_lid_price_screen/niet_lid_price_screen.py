from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.label import MDLabel
from kivy.storage.jsonstore import JsonStore

from app.functions.variables import variables
from app.functions.send_to_screen import send_to_screen
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

    def on_kv_post(self, obj):  # initiates popup when app is started (create the needed elements)
        self.ask_reset_prices()

    def on_leave(self):  # when the screen is left, hide the popup if shown
        self.clear_popup_price()

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

    def ask_reset_prices(self):  # initiate the popup elements
        # initiate the background image so if the table is underneath the popup, everything remains visible
        self.backgroundimage_price = Image(
            source='app/assets/background.png',
            opacity=0,
            size_hint=(0.9, 0.4),
            pos_hint={"x": 0.05, "y": 0.3},
            fit_mode="fill"
        )
        self.add_widget(self.backgroundimage_price, index=2)

        self.confirmtext_price = MDLabel(
            text="Ben je zeker dat je de prijslijst wilt wissen? Dit kan niet ongedaan gemaakt worden!",
            size_hint=(0.86, 0.3),
            pos_hint={"x": 0.07, "y": 0.4},
            font_name='app/assets/D-DIN.otf',
            opacity=0
        )
        self.add_widget(self.confirmtext_price, index=1)

        self.cancel_button_price = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.05, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="annuleer",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.cancel_button_price.bind(on_release=lambda x: self.clear_popup_price())
        self.add_widget(self.cancel_button_price, index=1)

        self.continue_button_price = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.5, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="Ga verder",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.continue_button_price.bind(on_release=lambda x: self.reset_prices())
        self.continue_button_price.bind(on_press=lambda x: self.clear_popup_price())
        self.add_widget(self.continue_button_price, index=1)

    def show_popup_price(self):  # shows the popup
        self.ids.apply_button.disabled = True
        self.cancel_button_price.opacity = 1
        self.cancel_button_price.disabled = False
        self.continue_button_price.opacity = 1
        self.continue_button_price.disabled = False
        self.confirmtext_price.opacity = 1
        self.backgroundimage_price.opacity = 1

    def clear_popup_price(self):  # hides the popup
        self.ids.apply_button.disabled = False
        self.cancel_button_price.opacity = 0
        self.cancel_button_price.disabled = True
        self.continue_button_price.opacity = 0
        self.continue_button_price.disabled = True
        self.confirmtext_price.opacity = 0
        self.backgroundimage_price.opacity = 0

    def reset_prices(self):  # set the price list file to an empty dictionary
        JsonStore("app/functions/niet-lid_price_list"+variables["api_suffix"]+".json").clear()
        set_up_prices()
