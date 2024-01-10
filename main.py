from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.config import Config
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.datatables import MDDataTable

from camera4kivy import Preview
from PIL import Image
from pyzbar.pyzbar import decode
import datetime

from app.api.hub_api import PyToken, refresh_token, update_validity, authenticate, get_all_events
from app.functions.get_results import get_results
from app.screens.trivial_screens import TokenScreen, PaylessScreen

Config.set('graphics', 'resizable', True)


def alg_make_visible(self, visibility: bool):
    if visibility:
        self.ids.more_info_button.text = "Minder info"
    else:
        self.ids.more_info_button.text = "Meer info"

    self.ids.voornaam_drop.text = app.voornaam
    self.ids.naam_drop.text = app.naam
    self.ids.email_drop.text = app.email
    self.ids.lidstatus_drop.text = app.lidstatus
    self.ids.validity_drop.text = app.validity
    self.ids.checkout_status_drop.text = app.checkout_status

    self.product_table.disabled = not visibility
    self.ids.validity_button.disabled = not visibility
    self.ids.count_input.disabled = not visibility
    self.main_button.disabled = not visibility

    if app.iconpath == "app/assets/dashmark.png" and visibility:
        self.remove_widget(self.main_button_invalids)
        self.remove_widget(self.confirm_button_invalids)
    elif app.iconpath == "app/assets/dashmark.png":
        self.add_widget(self.main_button_invalids, index=2)
        self.add_widget(self.confirm_button_invalids, index=1)

    objs = [self.ids.voornaam_drop,
            self.ids.voornaam_text,
            self.ids.naam_drop,
            self.ids.naam_text,
            self.ids.email_drop,
            self.ids.email_text,
            self.ids.lidstatus_drop,
            self.ids.lidstatus_text,
            self.product_table,
            self.ids.validity_drop,
            self.ids.validity_text,
            self.ids.checkout_status_drop,
            self.ids.checkout_status_text,
            self.main_button,
            self.ids.validity_button,
            self.ids.count_input]

    for obj in objs:
        obj.opacity = int(visibility)

    if app.show_count_error:
        self.ids.count_error.opacity = int(visibility)


class LoginScreen(MDScreen):
    def login(self):
        app.token = authenticate(self.ids.mail.text.lower(), self.ids.passw.text)
        if app.token == "login_error":
            self.ids.validitylabel.text = "Email of wachtwoord incorrect"
        elif app.token == "server_error":
            self.ids.validitylabel.text = "Kon geen verbinding met de server maken"
        else:
            self.ids.validitylabel.text = ""

    def buttonpress(self):
        if app.token != "login_error" and app.token != "server_error":
            app.prev_screen = "login"
            self.manager.transition.direction = "left"
            self.manager.current = "scan"


class ScanScreen(MDScreen):
    def on_pre_enter(self):
        app.prev_result = ""
        if app.prev_screen == "login":
            self.load_dropdown_events()

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    def stopping(self):
        self.ids.preview.disconnect_camera()

    @mainthread
    def got_result(self, result):

        if result == app.prev_result:
            return

        response_dict = get_results(app.token, result, app.event_items[app.main_button_events.text])
        app.prev_args = {"token": app.token, "uuid": result,
                         "event_uuid": app.event_items[app.main_button_events.text]}
        if (response_dict["validity"] == "valid"
                or response_dict["validity"] == "invalid"
                or response_dict["validity"] == "consumed"
                or response_dict["validity"] == "manually_verified"
                or response_dict["validity"] == "eventError"):
            app.voornaam = response_dict["voornaam"]
            app.naam = response_dict["naam"]
            app.email = response_dict["email"]
            app.validity = response_dict["validity"]
            app.lidstatus = response_dict["lidstatus"]
            app.checkout_status = response_dict["checkout_status"]
            app.table_data = response_dict["table_data"]

        if response_dict["validity"] == "APITokenError":
            result = ""
            app.prev_result = ""
            app.token = refresh_token(app.token)
            if app.token == PyToken():
                app.prev_screen = "scan"
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            else:
                self.manager.transition.direction = "left"
                self.manager.current = "token"
        elif response_dict["validity"] == "valid":
            app.iconpath = "app/assets/checkmark.png"
            app.prev_screen = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"
        elif response_dict["validity"] == "invalid":
            app.iconpath = "app/assets/dashmark.png"
            app.prev_screen = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"
        elif (response_dict["validity"] == "consumed" or response_dict["validity"] == "eventError"
              or response_dict["validity"] == "manually_verified"):
            app.prev_screen = "scan"
            app.iconpath = "app/assets/xmark.png"
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"
        elif response_dict["validity"] == "UUIDError":
            app.prev_screen = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "payless"
        elif response_dict["validity"] == "emptyEvent":
            self.ids.event_empty.opacity = 1
        else:
            print("ERROR - validity unknown")

        app.prev_result = result

    def load_dropdown_events(self):
        self.dropdown_events = DropDown()
        app.event_items = get_all_events(app.token, datetime.datetime.now())
        app.event_items['Selecteer een evenement'] = ""

        for item in list(app.event_items.keys()):
            opts_events = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_events.bind(on_release=lambda opt_events: self.dropdown_events.select(opt_events.text))
            self.dropdown_events.add_widget(opts_events)

        app.main_button_events = Button(
            text='Selecteer een evenement',
            size_hint=(0.9, None),
            height=dp(30),
            pos_hint={'x': 0.05, 'y': 0.92},
            font_name='app/assets/D-DIN.otf')
        app.main_button_events.bind(on_release=self.dropdown_events.open)
        app.main_button_events.bind(on_release=lambda x: self.reset_event_empty())
        self.dropdown_events.bind(on_select=lambda instance, x: setattr(app.main_button_events, 'text', x))

        self.add_widget(app.main_button_events, index=1)

    def reset_event_empty(self):
        self.ids.event_empty.opacity = 0
        app.prev_result = ""


class ValidInvalidUsedScreen(MDScreen):
    def __init__(self, **kwargs):
        super(ValidInvalidUsedScreen, self).__init__(**kwargs)

        self.product_table: MDDataTable = MDDataTable()
        self.added_item: int = 0

    def on_pre_enter(self):
        self.ids.validity_image.source = app.iconpath
        self.load_table(False)
        if app.iconpath == "app/assets/checkmark.png":
            self.add_first_nonconsumed()
            self.change_validity(True)
            app.id_list = dict()
        if app.iconpath == "app/assets/dashmark.png":
            self.load_dropdown_invalids()

    def on_kv_post(self, obj):
        self.load_dropdown()

    def on_leave(self):
        app.id_list = dict()
        self.remove_widget(self.product_table)
        self.ids.count_input.text = "alle"
        if app.iconpath == "app/assets/dashmark.png":
            self.remove_widget(self.main_button_invalids)
            self.remove_widget(self.confirm_button_invalids)

    def change_validity(self, by_entry: bool, count: int | str = 1):
        if by_entry:
            validity = "consumed"
        else:
            validity = self.main_button.text.lower()
        for ids in list(app.id_list.keys()):
            if count == "alle":
                count = app.id_list[ids]
            if count > app.id_list[ids]:
                count = app.id_list[ids]
            update_validity(app.token, ids, validity, count)
        response_dict = get_results(app.prev_args["token"], app.prev_args["uuid"], app.prev_args["event_uuid"], False)
        app.table_data = response_dict["table_data"]
        self.remove_widget(self.product_table)
        if by_entry:
            self.load_table(False)
        else:
            self.load_table(True)

    def change_validity_button(self):
        if self.ids.count_input.text.isdigit():
            count = int(self.ids.count_input.text)
            self.change_validity(False, count)
            app.show_count_error = False
            self.ids.count_error.opacity = 0
        elif self.ids.count_input.text.lower() == "alle":
            self.change_validity(False, "alle")
            app.show_count_error = False
            self.ids.count_error.opacity = 0
        else:
            app.show_count_error = True
            self.ids.count_error.opacity = 1
        app.id_list = dict()

    def load_table(self, start_visible: bool = False):
        self.product_table = MDDataTable(
            size_hint_y=0.575,
            size_hint_x=1,
            check=True,
            pos_hint={"x": 0, "y": 0.15},
            column_data=[("[size=15]Item[/size]", dp(Window.width * 0.062 * 1.55)),
                         ("[size=15]Validity[/size]", dp(Window.width * 0.023 * 1.55)),
                         ("[size=15]To Pay[/size]", dp(Window.width * 0.015 * 1.55)),
                         ("[size=15]id[/size]", dp(Window.width * 0.015 * 1.55))],
            row_data=app.table_data,
            opacity=int(start_visible),
            disabled=not start_visible,
            background_color=(1, 1, 1, 1),
            background_color_cell=(0, 0, 1, 0),
            background_color_header=(0, 0, 1, 0),
            background_color_selected_cell=(0, 0, 1, 0))
        self.product_table.bind(on_check_press=self.check_press)
        self.add_widget(self.product_table, index=9)

    def check_press(self, instance_table, current_row):
        if int(current_row[3].replace('[size=15]', '').replace("[/size]", "")) in list(app.id_list.keys()):
            del app.id_list[int(current_row[3].replace('[size=15]', '').replace("[/size]", ""))]
        else:
            app.id_list[int(current_row[3].replace('[size=15]', '').replace("[/size]", ""))] = (
                int(current_row[0].replace('[size=15]', '').replace("[/size]", "").split(" x ")[0]))

    def add_first_nonconsumed(self):
        for row in app.table_data:
            if row[1] != '[size=15]consumed[/size]':
                app.id_list[int(row[3].replace('[size=15]', '').replace("[/size]", ""))] = (
                    int(row[0].replace('[size=15]', '').replace("[/size]", "").split(" x ")[0]))
                break

    def make_visible(self):
        alg_make_visible(self, not app.visibility)
        app.visibility = not app.visibility

    def set_invisible(self):
        if app.visibility:
            alg_make_visible(self, False)
            app.visibility = False

    def load_dropdown(self):
        self.dropdown_validity = DropDown()
        items = ["Consumed", "Valid", "Invalid"]

        for item in items:
            opts = Button(
                text=item,
                size_hint_y=None,
                height=30,
                font_name='app/assets/D-DIN.otf')
            opts.bind(on_release=lambda opt: self.dropdown_validity.select(opt.text))
            self.dropdown_validity.add_widget(opts)

        self.main_button = Button(
            text='Valid',
            opacity=0,
            disabled=True,
            size_hint=(0.4, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.main_button.bind(on_release=self.dropdown_validity.open)
        self.dropdown_validity.bind(on_select=lambda instance, x: setattr(self.main_button, 'text', x))

        self.add_widget(self.main_button, index=3)

    def load_dropdown_invalids(self):
        self.dropdown_invalids = DropDown()
        first = True
        huidig = ""
        floatalle = 0
        self.saved_i = 0
        for i in range(len(app.table_data)):
            amount = app.table_data[i][2].replace("[size=15]€", "").replace("[/size]", "").replace("[size=15]NVT", "0")
            amount = float(amount)
            if first and int(amount) != 0:
                huidig = "%.2f" % (amount / int(app.table_data[i][0].split(" x ")[0]))
                self.saved_i = i
                first = False
            floatalle += amount
        if huidig == "":
            huidig = "%.2f" % 0
        huidig = "Huidig ticket: €" + huidig
        alle = "Alle Tickets: €" + "%.2f" % floatalle
        self.invalids_items = [huidig, alle]

        for item in self.invalids_items:
            opts_invalids = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_invalids.bind(on_release=lambda opt_invalids: self.dropdown_invalids.select(opt_invalids.text))
            self.dropdown_invalids.add_widget(opts_invalids)

        self.main_button_invalids = Button(
            text=huidig,
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.main_button_invalids.bind(on_release=self.dropdown_invalids.open)
        self.dropdown_invalids.bind(on_select=lambda instance, x: setattr(self.main_button_invalids, 'text', x))

        self.add_widget(self.main_button_invalids, index=2)

        self.confirm_button_invalids = Button(
            text="Valideer",
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0.5, 'y': 0.1},
            font_name='app/assets/D-DIN.otf',
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png')
        self.confirm_button_invalids.bind(on_release=lambda x: self.validate())
        self.add_widget(self.confirm_button_invalids, index=1)

    def validate(self):
        if self.main_button_invalids.text.startswith("Huidig ticket"):
            ids = int(self.product_table.row_data[self.saved_i][3].replace('[size=15]', '').replace("[/size]", ""))
            update_validity(app.token, ids, "consumed", 1)
            # to_subtract = float(self.main_button_invalids.text.replace('Huidig ticket: €', ''))
            # new_to_pay = float(self.product_table.row_data[self.saved_i][2].replace('[size=15]€', '')
            #                    .replace("[/size]", "")) - to_subtract
            # self.product_table.update_row(self.product_table.row_data[self.saved_i],
            #                               [self.product_table.row_data[self.saved_i][0],
            #                                "[size=15]" + "consumed" + "[/size]",
            #                                '[size=15]€' + "%.2f" % new_to_pay + "[/size]",
            #                                self.product_table.row_data[self.saved_i][3]])
            response_dict = get_results(app.prev_args["token"], app.prev_args["uuid"],
                                        app.prev_args["event_uuid"], False)
            app.table_data = response_dict["table_data"]
            self.remove_widget(self.product_table)
            self.load_table(True)
        else:
            for i in range(len(app.table_data)):
                if self.product_table.row_data[i][1] == "[size=15]invalid[/size]":
                    ids = int(self.product_table.row_data[i][3].replace('[size=15]', '').replace("[/size]", ""))
                    count = int(self.product_table.row_data[i][0]
                                .replace('[size=15]', '').replace("[/size]", "").split(" x ")[0])
                    update_validity(app.token, ids, "consumed", count)
            response_dict = get_results(app.prev_args["token"], app.prev_args["uuid"],
                                        app.prev_args["event_uuid"], False)
            app.table_data = response_dict["table_data"]
            self.remove_widget(self.product_table)
            self.load_table(True)


class ScanAnalyze(Preview):
    extracted_data = ObjectProperty(None)

    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):
        pimage = Image.frombytes(mode='RGBA', size=image_size, data=pixels)
        list_of_all_barcodes = decode(pimage)

        if list_of_all_barcodes:
            if self.extracted_data:
                self.extracted_data(list_of_all_barcodes[0].data.decode('utf-8'))


class Sm(MDScreenManager):
    def __init__(self):
        super(Sm, self).__init__()

        self.add_widget(LoginScreen(name='login'))
        self.add_widget(ScanScreen(name='scan'))
        self.add_widget(TokenScreen(name='token'))
        self.add_widget(ValidInvalidUsedScreen(name='valid_invalid_used'))
        self.add_widget(PaylessScreen(name='payless'))


class IngeniumApp(MDApp):

    def __init__(self):
        super(IngeniumApp, self).__init__()
        self.token: PyToken | None = None
        self.visibility: bool = False
        self.iconpath: str = ""
        self.show_count_error: bool = False

        self.prev_screen: str = ""
        self.prev_result: str = ""
        self.prev_args: dict = dict()

        self.voornaam: str = ""
        self.naam: str = ""
        self.email: str = ""
        self.lidstatus: str = ""
        self.table_data: str = ""
        self.validity: str = ""
        self.checkout_status: str = ""
        self.id_list: dict = dict()

        self.main_button_events: Button | None = None
        self.event_items: dict = dict()

    def on_stop(self):
        ScanScreen.stopping(ScanScreen())

    def build(self):
        if platform == 'android':
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])
        return Sm()


if __name__ == '__main__':
    app = IngeniumApp()
    app.run()
