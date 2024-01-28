from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config

from app.functions.send_to_screen import send_to_screen

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class PaylessScreen(MDScreen):
    kv = Builder.load_file('app/screens/payless_screen.kv')  # load the associated kv file
    pass


class TokenScreen(MDScreen):
    kv = Builder.load_file('app/screens/token_screen.kv')  # load the associated kv file
    pass


class RedirectScreen(MDScreen):
    kv = Builder.load_file('app/screens/redirect_screen.kv')  # load the associated kv file

    def on_pre_enter(self, *args):
        send_to_screen(self, "valid")
