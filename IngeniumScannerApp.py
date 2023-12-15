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


Config.set('graphics', 'resizable', True)


def update(APIToken, UUID):
    requests.post("http://127.0.0.1:8000" + '/api/v1/staff/transaction/update', data={'access_token': APIToken, 'item_id': UUID})


def login(user_email, user_id):
    login = requests.post("http://127.0.0.1:8000" + "/api/v1/auth/token", data={'username': user_email, 'password': user_id})
    if login.status_code == 200:
        APIToken = login.json()['access_token']
        APIReset = login.json()['refresh_token']
        return APIToken, APIReset
    else:
        return "LoginError", 0


def get_validity(APIToken, UUID, event):
    checkout = requests.get("http://127.0.0.1:8000" + "/api/v1/staff/transaction", params={'access_token': APIToken, "limit": 50, "offset": 0, 'checkout_id': UUID})
    if checkout.status_code == 200:
        if checkout.json() != []:
            i = 0
            while i <= len(checkout.json()):
                if checkout.json()[i][1]["interaction"]["item_name"].lower() == event:
                    item_id = checkout.json()[i][1]["interaction"]["id"]
                    validity = checkout.json()[i][1]["valid_policy"]
                    return validity, item_id
                else:
                    i += 1
            return "eventError"
        else:
            return "UUIDError"
    else:
        return "APITokenError"


def reset_token(APIReset):
    reset = requests.post("http://127.0.0.1:8000" + "/api/v1/auth/refresh", data={'refresh_token': APIReset})
    if reset.status_code == 200:
        APIToken = reset.json()['access_token']
        return APIToken
    else:
        return "resetError"


class LoginScreen(MDScreen):
    def login(self):
        global Token, Reset
        Token, Reset = login(self.ids.mail.text.lower(), self.ids.passw.text)
        self.ids.validitylabel.text = "data invalid"
        if Token != "LoginError":
            self.ids.validitylabel.text = ""
        else:
            self.ids.validitylabel.text = "Email or Password incorrect"
    pass

    def buttonpress(self):
        global Token, sm
        if Token != "LoginError":
            ScannerAlowed = True
        else:
            ScannerAlowed = False
        sm.transition.direction = "left"
        sm.current = "scan" if ScannerAlowed else "login"
        pass


class ScanScreen(MDScreen):

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    @mainthread
    def got_result(self, result):
        # self.ids.ti.text = str(result)
        global prevevent, prevresult, Token, Reset, sm

        validity, item_id = get_validity(Token, result, self.ids.event.text.lower())
        if validity == "APITokenError":
            result = ""
            Token = reset_token(Reset)
            if Token == "resetError":
                sm.transition.direction = "right"
                sm.current = "login"
            else:
                sm.transition.direction = "left"
                sm.current = "token"
        elif validity == "Valid" and (result != prevresult or self.ids.event.text.lower() != prevevent):
            sm.transition.direction = "left"
            sm.current = "valid"
            update(Token, item_id)
        elif validity == "InValid" and (result != prevresult or self.ids.event.text.lower() != prevevent):
            sm.transition.direction = "left"
            sm.current = "invalid"
            update(Token, item_id)
        elif validity == "Used" and (result != prevresult or self.ids.event.text.lower() != prevevent):
            sm.transition.direction = "left"
            sm.current = "used"
        elif validity == ("eventError" or "UUIDError") and (result != prevresult or self.ids.event.text.lower() != prevevent):
            sm.transition.direction = "left"
            sm.current = "payless"
        prevresult = result
        prevevent = self.ids.event.text.lower()


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
    Token = 0
    Reset = 0
    sm = 0
    prevevent = ""
    prevresult = ""

    QRScan().run()
