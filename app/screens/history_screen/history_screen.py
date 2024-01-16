from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.datatables import MDDataTable
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.core.window import Window

import json

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class HistoryScreen(MDScreen):
    kv = Builder.load_file('app/screens/history_screen/history_screen.kv')  # load the associated kv file

    def on_pre_enter(self):  # when the screen is entered, load the history table
        self.load_history()

    def on_kv_post(self, obj):  # initiates popup when app is started
        self.ask_reset_history()

    def on_leave(self):  # when the screen is left, remove the history table for safety and hide the popup if shown
        self.remove_widget(self.info_table)
        self.clear_popup()

    def load_history(self):  # load the history table
        try:  # try to load the history file
            with open("app/functions/scan_history.json", "r") as openfile:
                history = json.load(openfile)
            openfile.close()
        except FileNotFoundError:  # if the file does not exist
            pass
        except json.decoder.JSONDecodeError:  # if the file exists but is completely empty
            openfile.close()
            history = dict()

        # set up the table data
        table_data = []
        if history != dict():
            for event in list(history.keys()):
                for mail in list(history[event].keys()):
                    table_data.append((
                        "[size=30]" + event + "[/size]",
                        "[size=30]" + mail + "[/size]",
                        "[size=30]" + history[event][mail]["naam"] + "[/size]",
                        "[size=30]" + history[event][mail]["achternaam"] + "[/size]",
                        "[size=30]" + str(history[event][mail]["count"]) + "[/size]"
                    ))
        else:
            table_data = []

        # create the table
        self.info_table = MDDataTable(
            size_hint_y=0.85,
            size_hint_x=1,
            check=False,
            pos_hint={"x": 0, "y": 0.1},
            column_data=[("[size=30]Event[/size]", dp(Window.width * 0.062 * 0.65)),
                         ("[size=30]Email[/size]", dp(Window.width * 0.062 * 0.65)),
                         ("[size=30]Naam[/size]", dp(Window.width * 0.062 * 0.65)),
                         ("[size=30]Achternaam[/size]", dp(Window.width * 0.062 * 0.65)),
                         ("[size=30]Aanpassingen[/size]", dp(Window.width * 0.062 * 0.65))],
            row_data=table_data,
            background_color=(1, 1, 1, 1),
            background_color_cell=(0, 0, 1, 0),
            background_color_header=(0, 0, 1, 0),
            background_color_selected_cell=(0, 0, 1, 0))
        self.add_widget(self.info_table, index=9)

    def ask_reset_history(self):  # initiate the popup elements
        # initiate the background image so if the table is underneath the popup, everything remains visible
        self.backgroundimage = Image(
            source='app/assets/background.png',
            opacity=0,
            size_hint=(0.9, 0.4),
            pos_hint={"x": 0.05, "y": 0.3},
            fit_mode="fill"
        )
        self.add_widget(self.backgroundimage, index=4)

        self.confirmtext = MDLabel(
            text="Ben je zeker dat je de geschiedenis wilt wissen? Dit kan niet ongedaan gemaakt worden!",
            size_hint=(0.86, 0.3),
            pos_hint={"x": 0.07, "y": 0.4},
            font_name='app/assets/D-DIN.otf',
            opacity=0
        )
        self.add_widget(self.confirmtext, index=2)

        self.cancel_button = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.05, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="annuleer",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.cancel_button.bind(on_release=lambda x: self.clear_popup())
        self.add_widget(self.cancel_button, index=3)

        self.continue_button = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.5, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="Ga verder",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.continue_button.bind(on_release=lambda x: self.reset_history())
        self.continue_button.bind(on_press=lambda x: self.clear_popup())
        # table is now incorrect so remove it
        self.continue_button.bind(on_release=lambda x: self.remove_widget(self.info_table))
        self.add_widget(self.continue_button, index=1)

    def show_popup(self):  # shows the popup
        self.cancel_button.opacity = 1
        self.cancel_button.disabled = False
        self.continue_button.opacity = 1
        self.continue_button.disabled = False
        self.confirmtext.opacity = 1
        self.backgroundimage.opacity = 1

    def clear_popup(self):  # hides the popup
        self.cancel_button.opacity = 0
        self.cancel_button.disabled = True
        self.continue_button.opacity = 0
        self.continue_button.disabled = True
        self.confirmtext.opacity = 0
        self.backgroundimage.opacity = 0

    def reset_history(self):  # set the history file to an empty dictionary
        file = open('app/functions/scan_history.json', 'w')
        json.dump(dict(), file)
        file.close()
