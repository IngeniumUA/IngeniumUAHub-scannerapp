from kivymd.uix.screen import MDScreen
from kivy.lang import Builder


class PaylessScreen(MDScreen):
    kv = Builder.load_file('app/screens/payless_screen.kv')
    pass


class TokenScreen(MDScreen):
    kv = Builder.load_file('app/screens/token_screen.kv')
    pass
