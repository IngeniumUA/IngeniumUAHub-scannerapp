from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from camera4kivy import Preview
from PIL import Image

from pyzbar.pyzbar import decode

import requests


resultlist = ["All-In, wout.de.smit@hotmail.be", "All-In, wout.de.smit@hotmail.com"]
prevresult = ""
prevevent = ""


class LoginScreen(MDScreen):
    pass


class ScanScreen(MDScreen):

    def on_kv_post(self, obj):
        self.ids.preview.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)

    @mainthread
    def got_result(self, result):
        self.ids.ti.text = str(result)
        global prevresult, prevevent
        if self.ids.event.text + ", " + result in resultlist and (result != prevresult or self.ids.event.text != prevevent):
            self.ids.ti.background_color = 0, 1, 0, 1
        elif result != prevresult or self.ids.event.text != prevevent:
            self.ids.ti.background_color = 1, 0, 0, 1
        prevresult = result
        prevevent = self.ids.event.text


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


class QRScan(MDApp):
    def build(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])

        sm = MDScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(ScanScreen(name='scan'))
        return sm


if __name__ == '__main__':
    QRScan().run()
