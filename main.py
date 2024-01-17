from kivy.utils import platform
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from app.screens.trivial_screens import TokenScreen, PaylessScreen
from app.screens.login_screen.login_screen import LoginScreen
from app.screens.valid_invalid_used_screen.valid_invalid_used_screen import ValidInvalidUsedScreen
from app.screens.scan_screen.scan_screen import ScanScreen
from app.screens.history_screen.history_screen import HistoryScreen
from app.functions.variables import variables

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


# initiate screen manager, this will allow the app to switch between screens
class Sm(MDScreenManager):
    def __init__(self):
        super(Sm, self).__init__()

        # add all screens to the screen manager, starting with the login screen so this is set as the start screen
        self.add_widget(LoginScreen(name='login'))
        self.add_widget(ScanScreen(name='scan'))
        self.add_widget(TokenScreen(name='token'))
        self.add_widget(ValidInvalidUsedScreen(name='valid_invalid_used'))
        self.add_widget(PaylessScreen(name='payless'))
        self.add_widget(HistoryScreen(name='history'))


# initiate the app itself
class IngeniumApp(MDApp):
    def on_stop(self):  # when the app closes, the camera is closed so the app doesn't crash
        ScanScreen.close_camera(ScanScreen())

    def build(self):  # start the app loop
        variables["pc"] = True  # store if the os is android or not for table visuals
        if platform == 'android':  # when the os is android, permissions for camera use are requested
            variables["pc"] = False
            from pythonforandroid.recipes.android.src.android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA, Permission.RECORD_AUDIO])
        return Sm()  # launch the screen manager so all screens get initiated


if __name__ == '__main__':
    IngeniumApp().run()  # launch the app
