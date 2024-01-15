from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config

from camera4kivy import Preview
from PIL import Image
from pyzbar.pyzbar import decode
import datetime

from app.api.hub_api import PyToken, refresh_token, get_all_events
from app.functions.get_results import get_results
from app.functions.variables import variables

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class ScanScreen(MDScreen):
    kv = Builder.load_file('app/screens/scan_screen/scan_screen.kv')  # load the associated kv file

    # called when going to this screen. prev_result is reset so a scanned code can be rescanned
    # when coming from the login screen, the current active events should be loaded into a dropdown
    def on_pre_enter(self):
        variables["prev_result"] = ""
        if variables["prev_screen"] == "login":
            self.load_dropdown_events()

    def on_kv_post(self, obj):  # called when the app is started, opens the camera when permission is given
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    def close_camera(self):  # called when the app is stopped, closes the camera to prevent crashing
        self.ids.preview.disconnect_camera()

    @mainthread
    def got_result(self, result):  # called when a qr code is detected, the string from the code is in result

        # when code is the same as the previous code, don't scan again to prevent unneeded api calls
        if result == variables["prev_result"]:
            return

        # get data from the qr code and store used data for the api call in variables for access on other screens
        response_dict = get_results(variables["token"], result,
                                    variables["event_items"][variables["main_button_events"].text])
        variables["prev_args"] = {"token": variables["token"], "uuid": result,
                                  "event_uuid": variables["event_items"][variables["main_button_events"].text]}

        # when there is data to be gained from the qr code, save them in variables for access on other screens
        if (response_dict["validity"] == "valid"
                or response_dict["validity"] == "invalid"
                or response_dict["validity"] == "consumed"
                or response_dict["validity"] == "manually_verified"
                or response_dict["validity"] == "eventError"):
            variables["voornaam"] = response_dict["voornaam"]
            variables["naam"] = response_dict["naam"]
            variables["email"] = response_dict["email"]
            variables["validity"] = response_dict["validity"]
            variables["lidstatus"] = response_dict["lidstatus"]
            variables["checkout_status"] = response_dict["checkout_status"]
            variables["table_data"] = response_dict["table_data"]

        # detect which validity or error the qr code has and send user to the appropriate screen
        if response_dict["validity"] == "APITokenError":
            result = ""
            variables["prev_result"] = ""
            variables["token"] = refresh_token(variables["token"])
            # when the token is expired, attempt to refresh the token. if this fails, bring user back to login screen
            if variables["token"] == PyToken():
                variables["prev_screen"] = "scan"
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            else:
                self.manager.transition.direction = "left"
                self.manager.current = "token"

        elif response_dict["validity"] == "valid":
            variables["iconpath"] = "app/assets/checkmark.png"  # set icon to green checkmark
            variables["prev_screen"] = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"

        elif response_dict["validity"] == "invalid":
            variables["iconpath"] = "app/assets/dashmark.png"  # set icon to orange "stop sign"
            variables["prev_screen"] = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"

        # when ticket is invalid but data was still acquired
        elif (response_dict["validity"] == "consumed" or response_dict["validity"] == "eventError"
              or response_dict["validity"] == "manually_verified"):
            variables["prev_screen"] = "scan"
            variables["iconpath"] = "app/assets/xmark.png"  # set icon to red cross
            self.manager.transition.direction = "left"
            self.manager.current = "valid_invalid_used"

        elif response_dict["validity"] == "UUIDError":
            variables["prev_screen"] = "scan"
            self.manager.transition.direction = "left"
            self.manager.current = "payless"

        elif response_dict["validity"] == "emptyEvent":  # when no event was given
            self.ids.event_empty.opacity = 1
        else:
            print("ERROR - validity unknown")  # this should never happen, print for debugging

        # store the used result, so it won't be used util user gets sent to other screen
        variables["prev_result"] = result

    def load_dropdown_events(self):  # load the dropdown from which the user can select the correct event
        self.dropdown_events = DropDown()
        variables["event_items"] = get_all_events(variables["token"], datetime.datetime.now())
        variables["event_items"]['Selecteer een evenement'] = ""

        for item in list(variables["event_items"].keys()):
            opts_events = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_events.bind(on_release=lambda opt_events: self.dropdown_events.select(opt_events.text))
            self.dropdown_events.add_widget(opts_events)

        variables["main_button_events"] = Button(
            text='Selecteer een evenement',
            size_hint=(0.9, None),
            height=dp(30),
            pos_hint={'x': 0.05, 'y': 0.92},
            font_name='app/assets/D-DIN.otf')
        variables["main_button_events"].bind(on_release=self.dropdown_events.open)
        variables["main_button_events"].bind(on_release=lambda x: self.reset_event_empty())
        self.dropdown_events.bind(on_select=lambda instance, x: setattr(variables["main_button_events"], 'text', x))

        self.add_widget(variables["main_button_events"], index=1)

    # when an event is chosen, the error message should disappear and the qr code should be able to be rescanned
    def reset_event_empty(self):
        self.ids.event_empty.opacity = 0
        variables["prev_result"] = ""


class ScanAnalyze(Preview):  # decodes camera data and returns the scanned string when qr code is detected
    extracted_data = ObjectProperty(None)

    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):
        pimage = Image.frombytes(mode='RGBA', size=image_size, data=pixels)
        list_of_all_barcodes = decode(pimage)

        if list_of_all_barcodes:
            if self.extracted_data:
                self.extracted_data(list_of_all_barcodes[0].data.decode('utf-8'))
