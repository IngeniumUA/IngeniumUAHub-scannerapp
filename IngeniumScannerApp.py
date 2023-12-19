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

from data_models import PyStaffTransaction
from hub_api import get_transactions, authenticate, refresh_token, PyToken

Config.set('graphics', 'resizable', True)


def update(api_token, uuid):
    requests.put("http://127.0.0.1:8000" + '/api/v1/staff/transaction/update', data={'access_token': api_token,
                                                                                     'item_id': uuid})


def get_validity(api_token, uuid, event):
    """
    :param api_token:
    :param uuid:
    :param event:
    :return:
    """
    transactions: list[PyStaffTransaction] = get_transactions(token=api_token, checkout_id=str(uuid))
    # With get_transactions we fetch a list of PyStaffTransactions
    # For each item in the list: ( example as "for v in transactions:" )
    #   A unique id has been provided in v.interaction.id
    #   Check the validity with v.validity == 'valid' .. or v.validity == 'invalid'
    #   Display product name v.product['name']

    if transactions is None:
        return "APITokenError", 0
    if transactions == []:
        return "UUIDError", 0
    for transaction in transactions:
        if transaction.interaction.item_name.lower() == event:
            return transaction.validity.value, transaction.interaction.item_id
    return "eventError", 0


class LoginScreen(MDScreen):
    def login(self):
        global token
        token = authenticate(self.ids.mail.text.lower(), self.ids.passw.text)
        if token is None:
            self.ids.validitylabel.text = "Email or Password incorrect"
        else:
            self.ids.validitylabel.text = ""
        pass

    def buttonpress(self):
        global token, sm
        if token is None:
            scanner_allowed = False
        else:
            scanner_allowed = True
        sm.transition.direction = "left"
        sm.current = "scan" if scanner_allowed else "login"
        pass


class ScanScreen(MDScreen):

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    @mainthread
    def got_result(self, result):
        # self.ids.ti.text = str(result)
        global prev_event, prev_result, token, sm
        if result == prev_result and self.ids.event.text.lower() == prev_event:
            return
        validity, item_id = get_validity(token, result, self.ids.event.text.lower())
        if validity == "APITokenError":
            result = ""
            prev_result = ""
            token = refresh_token(token)
            if token is None:
                sm.transition.direction = "right"
                sm.current = "login"
            else:
                sm.transition.direction = "left"
                sm.current = "token"
        elif validity == "valid":
            sm.transition.direction = "left"
            sm.current = "valid"
            update(token, item_id)
        elif validity == "invalid":
            sm.transition.direction = "left"
            sm.current = "invalid"
            update(token, item_id)
        elif validity == "consumed":
            sm.transition.direction = "left"
            sm.current = "used"
        elif validity == ("eventError" or "UUIDError"):
            sm.transition.direction = "left"
            sm.current = "payless"
        else:
            print("ERROR - validity unknown")
        prev_result = result
        prev_event = self.ids.event.text.lower()


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
    def build(self):
        if platform == 'android':
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])

        global sm
        sm = MDScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(ScanScreen(name='scan'))
        sm.add_widget(TokenScreen(name='token'))
        sm.add_widget(ValidScreen(name='valid'))
        sm.add_widget(InValidScreen(name='invalid'))
        sm.add_widget(UsedScreen(name='used'))
        sm.add_widget(PaylessScreen(name='payless'))
        return sm


if __name__ == '__main__':
    token: PyToken
    sm: MDScreenManager
    prev_event = ""
    prev_result = ""

    QRScan().run()
