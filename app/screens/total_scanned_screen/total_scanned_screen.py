from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import dp

from app.functions.variables import variables
from app.functions.send_to_screen import send_to_screen
from app.api.hub_api import get_event_stats


Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class TotalScannedScreen(MDScreen):
    kv = Builder.load_file('app/screens/total_scanned_screen/total_scanned_screen.kv')  # load the associated kv file

    def on_pre_enter(self):
        self.load_dropdown_events_totals()
        if variables["current_selected_event"] != "":
            variables["main_button_events_totals"].text = variables["current_selected_event"]
            self.show_totals(variables["main_button_events_totals"].text)

    def load_dropdown_events_totals(self):
        # create dropdown to select which event totals should be displayed
        self.dropdown_events_totals = DropDown()
        for item in list(variables["event_items"].keys()):
            opts_events_totals = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_events_totals.bind(on_release=
                                   lambda opt_events_totals: self.dropdown_events_totals.select(opt_events_totals.text))
            opts_events_totals.bind(on_release=lambda opt_events_totals: self.show_totals(opt_events_totals.text))
            self.dropdown_events_totals.add_widget(opts_events_totals)

        variables["main_button_events_totals"] = Button(
            text='Selecteer een evenement',
            size_hint=(0.9, None),
            height=dp(30),
            pos_hint={'x': 0.05, 'y': 0.92},
            font_name='app/assets/D-DIN.otf')
        variables["main_button_events_totals"].bind(on_release=self.dropdown_events_totals.open)
        self.dropdown_events_totals.bind(on_select=
                                        lambda instance, x: setattr(variables["main_button_events_totals"], 'text', x))
        self.add_widget(variables["main_button_events_totals"], index=1)

    def show_totals(self, event):  # actually display the totals
        if event == "Selecteer een evenement":  # if select event then don't display any results
            self.ids.total_scanned_global_var.text = ""
            self.ids.total_scanned_local_var.text = ""
            return
        global_total = get_event_stats(variables["token"],
                                       variables["event_items"][event],
                                       "consumed")
        if isinstance(global_total, str):  # if str is returned, there is a problem with the token so refresh
            send_to_screen(self, "APITokenError")
        else:
            self.ids.total_scanned_global_var.text = str(global_total)
            local_total = 0
            for action in variables["history_table"]:  # check in history all actions that would lead to a consumed ticket
                if action[0] == "[size=30]"+event+"[/size]" or event == "Alle evenementen":
                    if (action[5] == "[size=30]manueel aangepast naar consumed[/size]"
                            or action[5] == "[size=30]automatisch geverifieerd[/size]"):
                        local_total += int(action[4].replace("[size=30]", "").replace("[/size]", ""))
            self.ids.total_scanned_local_var.text = str(local_total)
