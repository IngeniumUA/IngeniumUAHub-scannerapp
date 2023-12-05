from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from camera4kivy import Preview
from PIL import Image

from pyzbar.pyzbar import decode

import random
import requests


class IngeniumAPIReplica:
    def __init__(self, instance):
        self.instance = instance
        self.AcceptableTokens = []
        self.AcceptableResets = []
        self.logindb = {"wout.de.smit@hotmail.be": "RobbieIsMyB", "wout.de.smit@gmail.com": "ILoveSpaghett"}
        self.evendtdb = {"UUID1": {"event": "All-In", "Validity": "Valid"},
                         "UUID2": {"event": "All-In", "Validity": "InValid"},
                         "UUID3": {"event": "All-In", "Validity": "Used"},
                         "UUID4": {"event": "Schachtenkoningcantus", "Validity": "Valid"}}

    def update(self,UUID):
        self.evendtdb[UUID]["Validity"] = "Used"

    def login(self, user_email, user_id):
        if user_email in self.logindb:
            if self.logindb[user_email] == user_id:
                APItoken = random.randint(100000, 999999)
                APIReset = random.randint(100000, 999999)
                self.AcceptableTokens.append(APItoken)
                self.AcceptableResets.append(APIReset)
                return APItoken, APIReset
            else:
                return "LoginError", 0
        else:
            return "LoginError", 0

    def get_validity(self, APIToken, UUID, event):
        if APIToken in self.AcceptableTokens:
            if UUID in self.evendtdb:
                if self.evendtdb[UUID]["event"] == event:
                    validity = self.evendtdb[UUID]["Validity"]
                    return validity
                else:
                    return "eventError"
            else:
                return "UUIDError"
        else:
            return "APITokenError"

    def reset_token(self, APIReset):
        if APIReset in self.AcceptableResets:
            APItoken = random.randint(100000, 999999)
            self.AcceptableTokens.append(APItoken)
            return APItoken
        else:
            return "resetError"

    def resettokens(self):
        self.AcceptableTokens = []

    def resetresets(self):
        self.AcceptableResets = []


class LoginScreen(MDScreen):
    def login(self):
        global Token, Reset, API
        Token, Reset = API.login(self.ids.mail.text, self.ids.passw.text)
        self.ids.validitylabel.text = "data invalid"
        if Token != "LoginError":
            self.ids.validitylabel.text = "data valid"
        else:
            self.ids.validitylabel.text = "data invalid"
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
        global prevresult, prevevent, Token, Reset, API, sm
        if API.get_validity(Token, result, self.ids.event.text) == "APITokenError":
            result = 0
            Token = API.reset_token(Reset)
            if Token == "resetError":
                sm.transition.direction = "right"
                sm.current = "login"
            else:
                sm.transition.direction = "left"
                sm.current = "token"
        elif API.get_validity(Token, result, self.ids.event.text) == "Valid" \
                and (result != prevresult or self.ids.event.text != prevevent):
            sm.transition.direction = "left"
            sm.current = "valid"
            API.update(result)
        elif API.get_validity(Token, result, self.ids.event.text) == "InValid" \
                and (result != prevresult or self.ids.event.text != prevevent):
            sm.transition.direction = "left"
            sm.current = "invalid"
            API.update(result)
        elif API.get_validity(Token, result, self.ids.event.text) == "Used" \
                and (result != prevresult or self.ids.event.text != prevevent):
            sm.transition.direction = "left"
            sm.current = "used"
        elif API.get_validity(Token, result, self.ids.event.text) == ("eventError" or "UUIDError") \
                and (result != prevresult or self.ids.event.text != prevevent):
            sm.transition.direction = "left"
            sm.current = "payless"
        prevresult = result
        prevevent = self.ids.event.text

    def resettokens(self):
        global API
        API.resettokens()

    def resetresets(self):
        global API
        API.resetresets()


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
            from android.permissions import request_permissions, Permission
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
    resultlist = ["All-In, wout.de.smit@hotmail.be", "All-In, wout.de.smit@hotmail.com"]
    prevresult = ""
    prevevent = ""
    Token = 0
    Reset = 0
    API = IngeniumAPIReplica(True)
    sm = 0

    QRScan().run()
