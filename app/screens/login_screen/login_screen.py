from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config

from app.api.hub_api import authenticate
from app.functions.variables import variables

Config.set('graphics', 'resizable', True)


class LoginScreen(MDScreen):
    kv = Builder.load_file('app/screens/login_screen/login_screen.kv')

    def login(self):
        variables["token"] = authenticate(self.ids.mail.text.lower(), self.ids.passw.text)
        if variables["token"] == "login_error":
            self.ids.validitylabel.text = "Email of wachtwoord incorrect"
        elif variables["token"] == "server_error":
            self.ids.validitylabel.text = "Kon geen verbinding met de server maken"
        else:
            self.ids.validitylabel.text = ""

    def buttonpress(self):
        if variables["token"] != "login_error" and variables["token"] != "server_error":
            variables["prev_screen"] = "login"
            self.manager.transition.direction = "left"
            self.manager.current = "scan"
