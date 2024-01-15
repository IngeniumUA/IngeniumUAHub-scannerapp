from kivy.utils import platform
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from app.screens.trivial_screens import TokenScreen, PaylessScreen
from app.screens.login_screen.login_screen import LoginScreen
from app.screens.valid_invalid_used_screen.valid_invalid_used_screen import ValidInvalidUsedScreen
from app.screens.scan_screen.scan_screen import ScanScreen

Config.set('graphics', 'resizable', True)


class Sm(MDScreenManager):
    def __init__(self):
        super(Sm, self).__init__()

        self.add_widget(LoginScreen(name='login'))
        self.add_widget(ScanScreen(name='scan'))
        self.add_widget(TokenScreen(name='token'))
        self.add_widget(ValidInvalidUsedScreen(name='valid_invalid_used'))
        self.add_widget(PaylessScreen(name='payless'))


class IngeniumApp(MDApp):

    def on_stop(self):
        ScanScreen.stopping(ScanScreen())

    def build(self):
        if platform == 'android':
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])
        return Sm()


if __name__ == '__main__':
    app = IngeniumApp()
    app.run()
