from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.config import Config

from app.functions.variables import variables

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


class SettingsScreen(MDScreen):
    kv = Builder.load_file('app/screens/settings_screen/settings_screen.kv')  # load the associated kv file

    def goto_niet_lid_price_screen(self):  # when icon is clicked, the user is sent to the niet_lid_price screen
        variables["prev_screen"] = "scan"
        self.manager.transition.direction = "left"
        self.manager.current = "niet_lid_price"

    def turn_on_camera_capture(self, switch_object, switch_value):
            variables["options"]["enable_image_capture"] = switch_value

    def enable_auto_return(self, switch_object, switch_value):
        variables["options"]["auto_return"] = switch_value
