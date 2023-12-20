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
from hub_api import get_transactions, authenticate, refresh_token, PyToken, get_userdata

Config.set('graphics', 'resizable', True)


def update(api_token, uuid):
    requests.put("http://127.0.0.1:8000" + '/api/v1/staff/transaction/update', data={'access_token': api_token,
                                                                                     'item_id': uuid})


def alg_make_visible(self):
    self.ids.more_info_button.text = "Less info"

    self.ids.voornaam_naam_drop.text = app.voornaam_naam
    self.ids.voornaam_naam_drop.opacity = 1
    self.ids.voornaam_naam_text.opacity = 1

    self.ids.email_drop.text = app.email
    self.ids.email_drop.opacity = 1
    self.ids.email_text.opacity = 1

    self.ids.lidstatus_drop.text = app.lidstatus
    self.ids.lidstatus_drop.opacity = 1
    self.ids.lidstatus_text.opacity = 1

    self.ids.products_count_drop.text = app.products_count
    self.ids.products_count_drop.opacity = 1
    self.ids.products_count_text.opacity = 1

    self.ids.validity_drop.text = app.validity
    self.ids.validity_drop.opacity = 1
    self.ids.validity_text.opacity = 1

    self.ids.checkout_status_drop.text = app.checkout_status
    self.ids.checkout_status_drop.opacity = 1
    self.ids.checkout_status_text.opacity = 1


def alg_make_invisible(self):
    self.ids.more_info_button.text = "More info"

    self.ids.voornaam_naam_drop.opacity = 0
    self.ids.voornaam_naam_text.opacity = 0

    self.ids.email_drop.opacity = 0
    self.ids.email_text.opacity = 0

    self.ids.lidstatus_drop.opacity = 0
    self.ids.lidstatus_text.opacity = 0

    self.ids.products_count_drop.opacity = 0
    self.ids.products_count_text.opacity = 0

    self.ids.validity_drop.opacity = 0
    self.ids.validity_text.opacity = 0

    self.ids.checkout_status_drop.opacity = 0
    self.ids.checkout_status_text.opacity = 0


def get_results(api_token, uuid: str, event):
    """
    :param api_token:
    :param uuid:
    :param event:
    :return:
    """
    transactions: list[PyStaffTransaction] = get_transactions(token=api_token, checkout_id=str(uuid))
    products_str = str()
    transaction_to_save = []
    if transactions == "login_invalid":
        return {"validity": "APITokenError"}
    if transactions == [] or transactions == "uuid_invalid":
        return {"validity": "UUIDError"}
    for transaction in transactions:
        products_str += str(transaction.count) + " x " + str(transaction.interaction.item_name.lower()) + ", "
        if transaction.interaction.item_name.lower() == event:
            transaction_to_save.append(transaction)
    if transaction_to_save != []:
        userdata = get_userdata(transaction_to_save[0].interaction.user_id)
        return {"validity": transaction_to_save[0].validity.value,
                "item_id": transaction_to_save[0].interaction.item_id,
                "products": products_str,
                "email": transaction_to_save[0].interaction.user_email,
                "checkout_status": transaction_to_save[0].status.value,
                "voornaam_naam": userdata["voornaam"] + " " + userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}
    else:
        userdata = get_userdata(transactions[0].interaction.user_id)
        return {"validity": "eventError",
                "products": products_str,
                "email": transactions[0].interaction.user_email,
                "checkout_status": transactions[0].status.value,
                "voornaam_naam": userdata["voornaam"] + " " + userdata["achternaam"],
                "lidstatus": str(userdata["lidstatus"])}


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
            app.sm.transition.direction = "left"
            app.sm.current = "valid"
            update(app.token, response_dict["item_id"])
        elif response_dict["validity"] == "invalid":
            app.sm.transition.direction = "left"
            app.sm.current = "invalid"
            update(app.token, response_dict["item_id"])
        elif response_dict["validity"] == "consumed" or response_dict["validity"] == "eventError":
            app.sm.transition.direction = "left"
            app.sm.current = "used"
        elif response_dict["validity"] == "UUIDError":
            app.sm.transition.direction = "left"
            app.sm.current = "payless"
        else:
            print("ERROR - validity unknown")

        app.prev_result = result
        app.prev_event = self.ids.event.text.lower()


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
    def make_visible(self):
        if not app.visibility:
            alg_make_visible(self)
            app.visibility = True
        elif app.visibility:
            alg_make_invisible(self)
            app.visibility = False

    def set_invisible(self):
        if app.visibility:
            alg_make_invisible(self)
            app.visibility = False
    pass


class InValidScreen(MDScreen):
    def make_visible(self):
        if not app.visibility:
            alg_make_visible(self)
            app.visibility = True
        elif app.visibility:
            alg_make_invisible(self)
            app.visibility = False

    def set_invisible(self):
        if app.visibility:
            alg_make_invisible(self)
            app.visibility = False
    pass


class UsedScreen(MDScreen):
    def make_visible(self):
        if not app.visibility:
            alg_make_visible(self)
            app.visibility = True
        elif app.visibility:
            alg_make_invisible(self)
            app.visibility = False

    def set_invisible(self):
        if app.visibility:
            alg_make_invisible(self)
            app.visibility = False
    pass


class PaylessScreen(MDScreen):
    pass


class QRScan(MDApp):

    def __init__(self):
        super(QRScan, self).__init__()
        self.sm = MDScreenManager()
        self.token: PyToken | None = None
        self.visibility = False

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
        self.sm.add_widget(ValidScreen(name='valid'))
        self.sm.add_widget(InValidScreen(name='invalid'))
        self.sm.add_widget(UsedScreen(name='used'))
        self.sm.add_widget(PaylessScreen(name='payless'))
        return self.sm


if __name__ == '__main__':
    app = QRScan()
    app.run()
