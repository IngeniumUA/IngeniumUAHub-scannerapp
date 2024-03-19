from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivy.lang import Builder
from kivy.config import Config
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

from app.functions.variables import variables

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class HistoryScreen(MDScreen):
    kv = Builder.load_file('app/screens/history_screen/history_screen.kv')  # load the associated kv file

    def on_pre_enter(self):  # when the screen is entered, load the history table
        self.load_history()

    def on_leave(self):  # when the screen is left, remove the history table for safety and hide the popup if shown
        self.remove_widget(self.info_table)
        try:
            self.popup_reset_history.dismiss()
        except AttributeError:
            pass

    def load_history(self):  # load the history table
        history_json = JsonStore("app/functions/scan_history"+variables["api_suffix"]+".json")
        history = dict(history_json)  # convert the file to a dictionary
        if history != dict():
            history = history["data"]

        # set up the table data
        table_data = []
        if history != dict():
            for event in list(history.keys()):
                for mail in list(history[event].keys()):
                    for mode in list(history[event][mail].keys()):
                        table_data.append((
                            "[size=30]" + event + "[/size]",
                            "[size=30]" + mail + "[/size]",
                            "[size=30]" + history[event][mail][mode]["naam"] + "[/size]",
                            "[size=30]" + history[event][mail][mode]["achternaam"] + "[/size]",
                            "[size=30]" + str(history[event][mail][mode]["count"]) + "[/size]",
                            "[size=30]" + mode + "[/size]",
                            "[size=30]" + history[event][mail][mode]["uuid"] + "[/size]"
                        ))

        # create the table
        self.info_table = MDDataTable(
            size_hint_y=0.85,
            size_hint_x=1,
            check=False,
            pos_hint={"x": 0, "y": 0.1},
            # add 1 to width scaling when on pc
            column_data=[("[size=30]Event[/size]", dp(Window.width * 0.062 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Email[/size]", dp(Window.width * 0.062 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Naam[/size]", dp(Window.width * 0.062 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Achternaam[/size]", dp(Window.width * 0.062 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Aanpassingen[/size]", dp(Window.width * 0.025 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Aanpassingswijze[/size]", dp(Window.width * 0.062 *
                                                                 (0.65 + float(variables["pc"])))),
                         ("[size=30]UUID[/size]", dp(Window.width * 0.087 * (0.65 + float(variables["pc"]))))],
            row_data=table_data,
            background_color=(1, 1, 1, 1),
            background_color_cell=(0, 0, 1, 0),
            background_color_header=(0, 0, 1, 0),
            background_color_selected_cell=(0, 0, 1, 0))
        self.add_widget(self.info_table, index=9)

        variables["history_table"] = table_data

    def show_reset_history(self):
        self.popup_reset_history = MDDialog(
            title="Geschiedenis verwijderen",
            text="Ben je zeker dat je de geschiedenis wilt wissen? Dit kan niet ongedaan gemaakt worden!",
            buttons=[
                MDFlatButton(
                    text="Annuleer",
                    font_name='app/assets/D-DIN.otf',
                    on_release=lambda x:self.close_reset_history()
                ),
                MDFlatButton(
                    text="Ga verder",
                    font_name='app/assets/D-DIN.otf',
                    on_release=lambda x: self.reset_history()
                )
            ],
        )
        self.popup_reset_history.open()
    def close_reset_history(self):
        self.popup_reset_history.dismiss()

    def reset_history(self):  # set the history file to an empty dictionary
        JsonStore("app/functions/scan_history"+variables["api_suffix"]+".json").clear()
        setattr(self.info_table, "row_data", [])
        self.popup_reset_history.dismiss()
