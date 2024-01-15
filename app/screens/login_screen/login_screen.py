from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config

from app.api.hub_api import authenticate
from app.functions.variables import variables

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class LoginScreen(MDScreen):
    kv = Builder.load_file('app/screens/login_screen/login_screen.kv')  # load the associated kv file

    def login(self):  # try to get token with given credentials and save gotten token
        variables["token"] = authenticate(self.ids.mail.text.lower(), self.ids.passw.text)
        if variables["token"] == "login_error":  # when incorrect credentials
            self.ids.validitylabel.text = "Email of wachtwoord incorrect"
        elif variables["token"] == "server_error":  # when unable to connect with server
            self.ids.validitylabel.text = "Kon geen verbinding met de server maken"
        else:  # reset label after successfully logging in
            self.ids.validitylabel.text = ""

    def buttonpress(self):  # always called right after login. when successfully logged in, change to scan screen
        if variables["token"] != "login_error" and variables["token"] != "server_error":
            variables["prev_screen"] = "login"
            self.manager.transition.direction = "left"
            self.manager.current = "scan"
