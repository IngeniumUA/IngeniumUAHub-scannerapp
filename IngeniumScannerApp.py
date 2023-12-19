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

import requests

from data_models import PyStaffTransaction, ValidityEnum
from hub_api import get_transactions, authenticate, refresh_token, PyToken

Config.set('graphics', 'resizable', True)


def update(api_token, uuid):
    requests.put("http://127.0.0.1:8000" + '/api/v1/staff/transaction/update', data={'access_token': api_token,
                                                                                     'item_id': uuid})


def get_validity(api_token, uuid: str, event):
    """
    :param api_token:
    :param uuid:
    :param event:
    :return:
    """
    transactions: list[PyStaffTransaction] = get_transactions(token=api_token, checkout_id=str(uuid))
    if transactions == "login_invalid":
        return "APITokenError", 0
    if transactions == [] or transactions == "uuid_invalid":
        return "UUIDError", 0
    for transaction in transactions:
        if transaction.interaction.item_name.lower() == event:
            return transaction.validity, transaction.interaction.item_id
    return "eventError", 0


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

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    def stopping(self):
        self.ids.preview.disconnect_camera()

    @mainthread
    def got_result(self, result):

        try:
            if self.prev_event == "" and self.prev_result == "":
                pass
        except AttributeError:
            self.prev_event = ""
            self.prev_result = ""

        if result == self.prev_result and self.ids.event.text.lower() == self.prev_event:
            return
        validity, item_id = get_validity(app.token, result, self.ids.event.text.lower())
        if validity == "APITokenError":
            result = ""
            self.prev_result = ""
            app.token = refresh_token(app.token)
            if app.token is None:
                app.sm.transition.direction = "right"
                app.sm.current = "login"
            else:
                app.sm.transition.direction = "left"
                app.sm.current = "token"
        elif validity == ValidityEnum.valid:
            app.sm.transition.direction = "left"
            app.sm.current = "valid"
            update(app.token, item_id)
        elif validity == ValidityEnum.invalid:
            app.sm.transition.direction = "left"
            app.sm.current = "invalid"
            update(app.token, item_id)
        elif validity == ValidityEnum.consumed:
            app.sm.transition.direction = "left"
            app.sm.current = "used"
        elif validity == "eventError" or validity == "UUIDError":
            app.sm.transition.direction = "left"
            app.sm.current = "payless"
        else:
            print("ERROR - validity unknown")
        self.prev_result = result
        self.prev_event = self.ids.event.text.lower()


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


class TokenScreen(MDScreen):
    pass


class ValidScreen(MDScreen):
    pass


class InValidScreen(MDScreen):
    pass


class UsedScreen(MDScreen):
    pass


class PaylessScreen(MDScreen):
    pass


class QRScan(MDApp):

    def __init__(self):
        super(QRScan, self).__init__()
        self.sm = MDScreenManager()
        self.token: PyToken | None = None

    def on_stop(self):
        ScanScreen.stopping(ScanScreen())

    def build(self):
        if platform == 'android':
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])

        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(ScanScreen(name='scan'))
        self.sm.add_widget(TokenScreen(name='token'))
        self.sm.add_widget(ValidScreen(name='valid'))
        self.sm.add_widget(InValidScreen(name='invalid'))
        self.sm.add_widget(UsedScreen(name='used'))
        self.sm.add_widget(PaylessScreen(name='payless'))
        return self.sm


if __name__ == '__main__':
    app = QRScan()
    app.run()
