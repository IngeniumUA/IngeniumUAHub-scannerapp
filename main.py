from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from camera4kivy import Preview
from PIL import Image
from pyzbar.pyzbar import decode

from app.api.hub_api import PyToken, refresh_token, update_validity, authenticate
from app.functions.get_results import get_results
from app.screens.token_screen import TokenScreen
from app.screens.payless_screen import PaylessScreen

Config.set('graphics', 'resizable', True)


def alg_make_visible(self, visibility: bool):
    if visibility:
        self.ids.more_info_button.text = "Less info"
    else:
        self.ids.more_info_button.text = "More info"

    self.ids.voornaam_naam_drop.text = app.voornaam_naam
    self.ids.email_drop.text = app.email
    self.ids.lidstatus_drop.text = app.lidstatus
    self.ids.products_count_drop.text = app.products_count
    self.ids.validity_drop.text = app.validity
    self.ids.checkout_status_drop.text = app.checkout_status

    objs = [self.ids.voornaam_naam_drop,
            self.ids.voornaam_naam_text,
            self.ids.email_drop,
            self.ids.email_text,
            self.ids.lidstatus_drop,
            self.ids.lidstatus_text,
            self.ids.products_count_drop,
            self.ids.products_count_text,
            self.ids.validity_drop,
            self.ids.validity_text,
            self.ids.checkout_status_drop,
            self.ids.checkout_status_text]

    for obj in objs:
        obj.opacity = int(visibility)


class LoginScreen(MDScreen):
    def login(self):
        app.token = authenticate(self.ids.mail.text.lower(), self.ids.passw.text)
        if app.token == "login_error":
            self.ids.validitylabel.text = "Email or Password incorrect"
        else:
            self.ids.validitylabel.text = ""
        pass

    def buttonpress(self):
        if app.token is None:
            scanner_allowed = False
        else:
            scanner_allowed = True
        app.sm.transition.direction = "left"
        app.sm.current = "scan" if scanner_allowed else "login"
        pass


class ScanScreen(MDScreen):
    def on_enter(self):
        app.prev_result = ""

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    def stopping(self):
        self.ids.preview.disconnect_camera()

    @mainthread
    def got_result(self, result):

        if result == app.prev_result and self.ids.event.text.lower() == app.prev_event:
            return

        response_dict = get_results(app.token, result, self.ids.event.text.lower())
        if (response_dict["validity"] == "valid"
                or response_dict["validity"] == "invalid"
                or response_dict["validity"] == "consumed"
                or response_dict["validity"] == "eventError"):
            app.voornaam_naam = response_dict["voornaam_naam"]
            app.email = response_dict["email"]
            app.validity = response_dict["validity"]
            app.lidstatus = response_dict["lidstatus"]
            app.checkout_status = response_dict["checkout_status"]
            app.products_count = response_dict["products"]

        if response_dict["validity"] == "APITokenError":
            result = ""
            app.prev_result = ""
            app.token = refresh_token(app.token)
            if app.token is None:
                app.sm.transition.direction = "right"
                app.sm.current = "login"
            else:
                app.sm.transition.direction = "left"
                app.sm.current = "token"
        elif response_dict["validity"] == "valid":
            app.iconpath = "app/assets/checkmark.png"
            app.sm.transition.direction = "left"
            app.sm.current = "valid_invalid_used"
            update_validity(response_dict["id"])
        elif response_dict["validity"] == "invalid":
            app.iconpath = "app/assets/dashmark.png"
            app.sm.transition.direction = "left"
            app.sm.current = "valid_invalid_used"
            update_validity(response_dict["id"])
        elif response_dict["validity"] == "consumed" or response_dict["validity"] == "eventError":
            app.iconpath = "app/assets/xmark.png"
            app.sm.transition.direction = "left"
            app.sm.current = "valid_invalid_used"
        elif response_dict["validity"] == "UUIDError":
            app.sm.transition.direction = "left"
            app.sm.current = "payless"
        else:
            print("ERROR - validity unknown")

        app.prev_result = result
        app.prev_event = self.ids.event.text.lower()


class ValidInvalidUsedScreen(MDScreen):
    def on_pre_enter(self):
        self.ids.validity_image.source = app.iconpath

    def make_visible(self):
        alg_make_visible(self, not app.visibility)
        app.visibility = not app.visibility

    def set_invisible(self):
        if app.visibility:
            alg_make_visible(self, False)
            app.visibility = False
    pass


class ScanAnalyze(Preview):
    extracted_data = ObjectProperty(None)

    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):
        pimage = Image.frombytes(mode='RGBA', size=image_size, data=pixels)
        list_of_all_barcodes = decode(pimage)

        if list_of_all_barcodes:
            if self.extracted_data:
                self.extracted_data(list_of_all_barcodes[0].data.decode('utf-8'))
            else:
                print("Not found")


class IngeniumApp(MDApp):

    def __init__(self):
        super(IngeniumApp, self).__init__()
        self.sm = MDScreenManager()
        self.token: PyToken | None = None
        self.visibility = False
        self.iconpath = ""

        self.prev_event = ""
        self.prev_result = ""
        self.voornaam_naam = ""
        self.email = ""
        self.lidstatus = ""
        self.products_count = ""
        self.validity = ""
        self.checkout_status = ""

    def on_stop(self):
        ScanScreen.stopping(ScanScreen())

    def build(self):
        if platform == 'android':
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])

        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(ScanScreen(name='scan'))
        self.sm.add_widget(TokenScreen(name='token'))
        self.sm.add_widget(ValidInvalidUsedScreen(name='valid_invalid_used'))
        self.sm.add_widget(PaylessScreen(name='payless'))
        return self.sm


if __name__ == '__main__':
    app = IngeniumApp()
    app.run()
