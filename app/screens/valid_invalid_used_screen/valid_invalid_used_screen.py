from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.lang import Builder
from kivymd.uix.datatables import MDDataTable
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.config import Config
from kivy.storage.jsonstore import JsonStore

from app.functions.variables import variables
from app.api.hub_api import patch_transaction
from app.api.hub_api import check_new_user
from app.api.hub_api import get_userdata
from app.functions.get_results import get_results
from app.functions.send_to_screen import send_to_screen

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


def add_to_history(event: str, mail: str, edit_mode: str, naam: str, achternaam: str,
                   uuid: str, count: int = 1) -> None:
    """
    adds the validated ticket with the given info the history file, if the file doesn't exist, it will be created

    Examples
    --------
    >>> add_to_history("All-In", "<EMAIL>", "automatic verification", "<NAME>", "<LAST NAME>", "<UUID>", 1)

    Parameters
    ----------
    :param event:
    :param mail:
    :param naam:
    :param achternaam:
    :param count:
    :param edit_mode:
    :param uuid:

    Returns
    -------
    :return: None
    """

    history_json = JsonStore("app/functions/scan_history.json")
    history = dict(history_json)  # convert the file to a dictionary
    if history != dict():
        history = history["data"]

    if event in list(history.keys()):
        if mail in list(history[event].keys()):  # if the ticket was already scanned, but there were still valids
            if edit_mode in list(history[event][mail].keys()):  # pass the edit mode
                count += history[event][mail][edit_mode]["count"]
                history[event][mail][edit_mode] = {"naam": naam, "achternaam": achternaam, "count": count, "uuid": uuid}
            else:
                history[event][mail][edit_mode] = {"naam": naam, "achternaam": achternaam, "count": count, "uuid": uuid}
        else:  # if the event was already used
            history[event][mail] = {edit_mode: {"naam": naam, "achternaam": achternaam, "count": count, "uuid": uuid}}
    else:  # if the event was not yet used
        history[event] = {mail: {edit_mode: {"naam": naam, "achternaam": achternaam, "count": count, "uuid": uuid}}}
    history_json["data"] = history  # write the dictionary to the file


def alg_make_visible(self, visibility: bool) -> None:
    """
    will set all the elements of the "more info" dropdown to visible or invisible depending on visibility

    Examples
    --------
    >>> alg_make_visible(self, False)
    None

    Parameters
    ----------
    :param self:
    :param visibility:

    Returns
    -------
    :return: None
    """

    if visibility:
        self.ids.more_info_button.text = "Minder info"
    else:
        self.ids.more_info_button.text = "Meer info"

    self.ids.voornaam_drop.text = variables["voornaam"]
    self.ids.naam_drop.text = variables["naam"]
    self.ids.email_drop.text = variables["email"]
    self.ids.lidstatus_drop.text = variables["lidstatus"]
    self.ids.validity_drop.text = variables["validity"]
    self.ids.checkout_status_drop.text = variables["checkout_status"]

    self.product_table.disabled = not visibility
    self.ids.validity_button.disabled = not visibility
    self.main_button.disabled = not visibility

    # remove widgets so they can't accidentally be interacted with while in the "more info" dropdown
    if variables["iconpath"] == "app/assets/dashmark.png" and visibility:
        self.remove_widget(self.confirm_button_invalids)
        self.remove_widget(self.button_change_user)
    # re-add widgets so they can be used again
    elif variables["iconpath"] == "app/assets/dashmark.png":
        self.add_widget(self.confirm_button_invalids, index=6)
        self.add_widget(self.button_change_user, index=5)

    objs = [self.ids.voornaam_drop,
            self.ids.voornaam_text,
            self.ids.naam_drop,
            self.ids.naam_text,
            self.ids.email_drop,
            self.ids.email_text,
            self.ids.lidstatus_drop,
            self.ids.lidstatus_text,
            self.product_table,
            self.ids.validity_drop,
            self.ids.validity_text,
            self.ids.checkout_status_drop,
            self.ids.checkout_status_text,
            self.main_button,
            self.ids.validity_button]

    for obj in objs:
        obj.opacity = int(visibility)


class ValidInvalidUsedScreen(MDScreen):
    # load the associated kv file
    kv = Builder.load_file('app/screens/valid_invalid_used_screen/valid_invalid_used_screen.kv')

    def __init__(self, **kwargs):
        super(ValidInvalidUsedScreen, self).__init__(**kwargs)

        self.product_table: MDDataTable = MDDataTable()
        self.added_item: int = 0

    # called when the screen is loaded. set the image correctly and load the table from the "more info" dropdown
    # when the ticket is valid, automatically validate it
    # when the ticket is invalid, load widgets made for invalid tickets
    def on_pre_enter(self):
        self.ids.validity_image.source = variables["iconpath"]
        self.load_table(start_visible=False)
        if variables["iconpath"] == "app/assets/checkmark.png":
            self.add_first_nonconsumed()
            self.change_validity(True)
            variables["id_list"] = []
        if variables["iconpath"] == "app/assets/dashmark.png":
            self.load_actions_invalids()

    # called when the app starts, loads the dropdown with the options for validity so this only needs to happen once
    def on_kv_post(self, obj):
        self.load_dropdown()
        self.ask_update_user()

    # called when the screen is left. reset all variables that may otherwise influence the next scanned item
    def on_leave(self):
        variables["id_list"] = []
        self.remove_widget(self.product_table)
        if variables["iconpath"] == "app/assets/dashmark.png":
            self.remove_widget(self.confirm_button_invalids)
            self.remove_widget(self.button_change_user)
            self.clear_popup_user()
            self.errortextuser.opacity = 0

    # change the validity of an interaction based on the given parameters
    def change_validity(self, by_entry: bool):
        if by_entry:
            validity = "consumed"
        else:
            validity = self.main_button.text.lower()

        for ids in variables["id_list"]:
            patch_transaction(variables["token"], ids, validity)

            # add the validated ticket to the history
            if by_entry:
                edit_mode = "automatisch geverifieerd"
            else:
                edit_mode = "manueel aangepast naar " + validity
            add_to_history(variables["main_button_events"].text, variables["email"], edit_mode, variables["voornaam"],
                           variables["naam"], variables["prev_result"], 1)

        response_dict = get_results(variables["prev_args"]["token"], variables["prev_args"]["uuid"],
                                    variables["prev_args"]["event_uuid"], False)
        if response_dict["validity"] == "APITokenError":
            send_to_screen(self, "APITokenError")  # send user to token refresh screen if token is expired
        variables["table_data"] = response_dict["table_data"]
        self.remove_widget(self.product_table)

        if by_entry:  # if the function was called by the user entering the screen, load the table invisible
            self.load_table(False)
        else:
            self.load_table(True)

    # called when the button to change the validity is pressed, extracts data and calls change_validity
    def change_validity_button(self):
        self.change_validity(False)
        variables["id_list"] = []

    def load_table(self, start_visible: bool = False):  # loads the table with the data acquired from the qr code
        self.product_table = MDDataTable(
            size_hint_y=0.575,
            size_hint_x=1,
            check=True,
            pos_hint={"x": 0, "y": 0.15},
            # add 1 to width scaling when on pc
            column_data=[("[size=30]Item[/size]", dp(Window.width * 0.062 * (0.65 + float(variables["pc"])))),
                         ("[size=30]Validity[/size]", dp(Window.width * 0.023 * (0.65 + float(variables["pc"])))),
                         ("[size=30]To Pay[/size]", dp(Window.width * 0.015 * (0.65 + float(variables["pc"])))),
                         ("[size=30]id[/size]", dp(Window.width * 0.015 * (0.65 + float(variables["pc"]))))],
            row_data=variables["table_data"],
            opacity=int(start_visible),
            disabled=not start_visible,
            background_color=(1, 1, 1, 1),
            background_color_cell=(0, 0, 1, 0),
            background_color_header=(0, 0, 1, 0),
            background_color_selected_cell=(0, 0, 1, 0))
        self.product_table.bind(on_check_press=self.check_press)
        self.add_widget(self.product_table, index=9)

    # adds id of the checked transaction to the id_list and removes when unchecked
    def check_press(self, instance_table, current_row):
        if int(current_row[3].replace('[size=30]', '').replace("[/size]", "")) in variables["id_list"]:
            variables["id_list"].remove(int(current_row[3].replace('[size=30]', '').replace("[/size]", "")))
        else:
            variables["id_list"].append(int(current_row[3].replace('[size=30]', '').replace("[/size]", "")))

    def add_first_nonconsumed(self):  # adds first ticket with a validity other than consumed to the id_list
        for row in variables["table_data"]:
            if row[1] != '[size=30]consumed[/size]':
                variables["id_list"].append(int(row[3].replace('[size=30]', '').replace("[/size]", "")))
                break

    def make_visible(self):  # changes the visibility of all dropdown elements
        alg_make_visible(self, not variables["visibility"])
        variables["visibility"] = not variables["visibility"]

    def set_invisible(self):  # sets the visibility of all dropdown elements to invisible
        if variables["visibility"]:
            alg_make_visible(self, False)
            variables["visibility"] = False

    def load_dropdown(self):  # loads the dropdown with the options for validity
        self.dropdown_validity = DropDown()
        items = ["Consumed", "Valid", "Invalid"]

        for item in items:
            opts = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts.bind(on_release=lambda opt: self.dropdown_validity.select(opt.text))
            self.dropdown_validity.add_widget(opts)

        self.main_button = Button(
            text='Valid',
            opacity=0,
            disabled=True,
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.main_button.bind(on_release=self.dropdown_validity.open)
        self.dropdown_validity.bind(on_select=lambda instance, x: setattr(self.main_button, 'text', x))

        self.add_widget(self.main_button, index=8)

    def load_actions_invalids(self):  # loads the actions for paying when an invalid ticket was scanned

        amount = (variables["table_data"][0][2].replace("[size=30]", "").replace("[/size]", "")
                  .replace("NVT", "€0.00"))
        self.amount_label_invalids = MDLabel(
            text=amount,
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.add_widget(self.amount_label_invalids)

        self.confirm_button_invalids = Button(
            text="Valideer",
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0.5, 'y': 0.1},
            font_name='app/assets/D-DIN.otf',
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png')
        self.confirm_button_invalids.bind(on_release=lambda x: self.validate())
        self.add_widget(self.confirm_button_invalids, index=6)

        self.button_change_user = Button(
            disabled=True,
            # !!!!! is disabled as user change is not implemented in the api, remove when this is implemented !!!!!
            text="Pas eigenaar aan",
            size_hint=(1, 0.05),
            pos_hint={'x': 0, 'y': 0.15},
            font_name='app/assets/D-DIN.otf',
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png')
        self.button_change_user.bind(on_release=lambda x: self.show_popup_user())
        self.add_widget(self.button_change_user, index=5)

    def validate(self):  # validates specifically the invalid ticket
        ids = int(self.product_table.row_data[0][3].replace('[size=30]', '').replace("[/size]", ""))
        patch_transaction(variables["token"], ids, "consumed")

        # add the validated ticket to the history
        add_to_history(variables["main_button_events"].text, variables["email"], "valideer ongeldig ticket",
                       variables["voornaam"], variables["naam"], variables["prev_result"])
        response_dict = get_results(variables["prev_args"]["token"], variables["prev_args"]["uuid"],
                                    variables["prev_args"]["event_uuid"], False)
        if response_dict["validity"] == "APITokenError":
            send_to_screen(self, "APITokenError")  # send user to token refresh screen if token is expired
        variables["table_data"] = response_dict["table_data"]
        self.remove_widget(self.product_table)
        self.load_table(False)

    def ask_update_user(self):  # initiate the popup elements
        # initiate the background image so if the table is underneath the popup, everything remains visible
        self.backgroundimageuser = Image(
            source='app/assets/background.png',
            opacity=0,
            size_hint=(0.9, 0.4),
            pos_hint={"x": 0.05, "y": 0.3},
            fit_mode="fill"
        )
        self.add_widget(self.backgroundimageuser, index=4)

        self.confirmtextuser = MDLabel(
            text="Vul het email adress van de nieuwe gebruiker in.",
            size_hint=(0.86, 0.15),
            pos_hint={"x": 0.07, "y": 0.5},
            font_name='app/assets/D-DIN.otf',
            opacity=0
        )
        self.add_widget(self.confirmtextuser, index=2)

        self.errortextuser = MDLabel(
            text="Deze gebruiker bestaat niet, probeer het opnieuw.",
            size_hint=(0.86, 0.05),
            pos_hint={"x": 0.07, "y": 0.48},
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            text_color=(1, 0, 0, 1),
            font_size=45
        )
        self.add_widget(self.errortextuser, index=2)

        self.inputuser = TextInput(
            hint_text="Email",
            multiline=False,
            size_hint=(0.86, None),
            height=dp(30),
            pos_hint={"x": 0.07, "y": 0.42},
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.inputuser.bind(on_text_validate=lambda x: self.change_user())
        self.add_widget(self.inputuser, index=3)

        self.cancel_buttonuser = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.05, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="annuleer",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.cancel_buttonuser.bind(on_release=lambda x: self.clear_popup_user())
        self.add_widget(self.cancel_buttonuser, index=3)

        self.continue_buttonuser = Button(
            size_hint=(0.45, 0.1),
            pos_hint={"x": 0.5, "y": 0.3},
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png',
            text="Ga verder",
            font_name='app/assets/D-DIN.otf',
            opacity=0,
            disabled=True
        )
        self.continue_buttonuser.bind(on_release=lambda x: self.change_user())
        self.add_widget(self.continue_buttonuser, index=1)

    def show_popup_user(self):  # shows the popup
        self.cancel_buttonuser.opacity = 1
        self.cancel_buttonuser.disabled = False
        self.continue_buttonuser.opacity = 1
        self.continue_buttonuser.disabled = False
        self.inputuser.opacity = 1
        self.inputuser.disabled = False
        self.confirmtextuser.opacity = 1
        self.backgroundimageuser.opacity = 1
        self.ids.more_info_button.disabled = True
        self.main_button_invalids.disabled = True
        self.confirm_button_invalids.disabled = True

    def clear_popup_user(self):  # hides the popup
        self.errortextuser.opacity = 0
        self.cancel_buttonuser.opacity = 0
        self.cancel_buttonuser.disabled = True
        self.continue_buttonuser.opacity = 0
        self.continue_buttonuser.disabled = True
        self.inputuser.opacity = 0
        self.inputuser.disabled = True
        self.confirmtextuser.opacity = 0
        self.backgroundimageuser.opacity = 0
        self.ids.more_info_button.disabled = False
        self.main_button_invalids.disabled = False
        self.confirm_button_invalids.disabled = False

    def change_user(self):
        lidstatus = check_new_user(variables["token"], self.inputuser.text)
        if lidstatus == "User not found":
            self.errortextuser.opacity = 1
            return

        if lidstatus["lid"]:
            invalid_fixed = False
            for i in range(len(variables["table_data"])):
                if self.product_table.row_data[i][1] == "[size=30]invalid[/size]" and not invalid_fixed:
                    ids = int(self.product_table.row_data[i][3].replace('[size=30]', '').replace("[/size]", ""))
                    patch_transaction(variables["token"], interaction_id=ids, validity="valid",
                                      force_patch=False, user=self.inputuser.text)
                elif not (self.product_table.row_data[i][1] == "[size=30]invalid[/size]" and not invalid_fixed):
                    ids = int(self.product_table.row_data[i][3].replace('[size=30]', '').replace("[/size]", ""))
                    patch_transaction(variables["token"], interaction_id=ids, force_patch=False,
                                      user=self.inputuser.text)

            response_dict = get_results(variables["prev_args"]["token"], variables["prev_args"]["uuid"],
                                        variables["prev_args"]["event_uuid"])

            # when there is data to be gained, save them in variables for access on other screens
            old_email = variables["email"]  # save old email
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

            variables["id_list"] = []
            self.remove_widget(self.product_table)
            self.remove_widget(self.main_button_invalids)
            self.remove_widget(self.confirm_button_invalids)
            self.clear_popup_user()
            self.errortextuser.opacity = 0
            self.remove_widget(self.button_change_user)
            self.clear_popup_user()
            add_to_history(variables["main_button_events"].text, old_email + " to " + variables["email"],
                           "change user", variables["voornaam"],
                           variables["naam"], variables["prev_result"])
            self.manager.current = "redirect"
        else:
            ids = int(self.product_table.row_data[0][3].replace('[size=30]', '').replace("[/size]", ""))
            patch_transaction(variables["token"], interaction_id=ids, force_patch=False, user=self.inputuser.text)
            response_dict = get_userdata(variables["token"], lidstatus["uuid"])
            old_email = variables["email"]  # save old email
            variables["voornaam"] = response_dict["voornaam"]
            self.ids.voornaam_drop.text = variables["voornaam"]
            variables["naam"] = response_dict["achternaam"]
            self.ids.naam_drop.text = variables["naam"]
            variables["email"] = self.inputuser.text
            self.ids.email_drop.text = variables["email"]
            add_to_history(variables["main_button_events"].text, old_email + " to " + variables["email"],
                           "change user", variables["voornaam"],
                           variables["naam"], variables["prev_result"])
            self.clear_popup_user()
