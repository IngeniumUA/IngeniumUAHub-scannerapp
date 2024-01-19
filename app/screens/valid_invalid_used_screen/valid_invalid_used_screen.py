from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.uix.datatables import MDDataTable
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.config import Config
from kivy.storage.jsonstore import JsonStore

from app.functions.variables import variables
from app.api.hub_api import update_validity
from app.functions.get_results import get_results
from app.functions.send_to_screen import send_to_screen

Config.set('graphics', 'resizable', True)  # make images and other elements resize when not the right dimensions


def add_to_history(event: str, mail: str, edit_mode: str, naam: str, achternaam: str, count: int, uuid: str) -> None:
    """
    adds the validated ticket with the given info the history file, if the file doesn't exist, it will be created

    Examples
    --------
    >>> add_to_history("All-In", "<EMAIL>", "automatic verification", "<NAME>", "<LAST NAME>", 1)

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
    self.ids.count_input.disabled = not visibility
    self.main_button.disabled = not visibility

    # remove widgets so they can't accidentally be interacted with while in the "more info" dropdown
    if variables["iconpath"] == "app/assets/dashmark.png" and visibility:
        self.remove_widget(self.main_button_invalids)
        self.remove_widget(self.confirm_button_invalids)
    # re-add widgets so they can be used again
    elif variables["iconpath"] == "app/assets/dashmark.png":
        self.add_widget(self.main_button_invalids, index=2)
        self.add_widget(self.confirm_button_invalids, index=1)

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
            self.ids.validity_button,
            self.ids.count_input]

    for obj in objs:
        obj.opacity = int(visibility)

    if variables["show_count_error"]:  # error message should only be shown outside the dropdown
        self.ids.count_error.opacity = int(visibility)


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
            variables["id_list"] = dict()
        if variables["iconpath"] == "app/assets/dashmark.png":
            self.load_dropdown_invalids()

    # called when the app starts, loads the dropdown with the options for validity so this only needs to happen once
    def on_kv_post(self, obj):
        self.load_dropdown()

    # called when the screen is left. reset all variables that may otherwise influence the next scanned item
    def on_leave(self):
        variables["id_list"] = dict()
        self.remove_widget(self.product_table)
        self.ids.count_input.text = "alle"
        if variables["iconpath"] == "app/assets/dashmark.png":
            self.remove_widget(self.main_button_invalids)
            self.remove_widget(self.confirm_button_invalids)

    # change the validity of an interaction based on the given parameters
    def change_validity(self, by_entry: bool, count: int | str = 1):
        if by_entry:
            validity = "consumed"
        else:
            validity = self.main_button.text.lower()

        for ids in list(variables["id_list"].keys()):
            if count == "alle":
                count = variables["id_list"][ids]
            if count > variables["id_list"][ids]:
                count = variables["id_list"][ids]
            update_validity(variables["token"], ids, validity, count)

            # add the validated ticket to the history
            if by_entry:
                edit_mode = "automatisch geverifieerd"
            else:
                edit_mode = "manueel aangepast"
            add_to_history(variables["main_button_events"].text, variables["email"], edit_mode, variables["voornaam"],
                           variables["naam"], count, variables["prev_result"])

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
        if self.ids.count_input.text.isdigit():
            count = int(self.ids.count_input.text)
            self.change_validity(False, count)
            variables["show_count_error"] = False
            self.ids.count_error.opacity = 0
        elif self.ids.count_input.text.lower() == "alle":
            self.change_validity(False, "alle")
            variables["show_count_error"] = False
            self.ids.count_error.opacity = 0
        else:
            variables["show_count_error"] = True
            self.ids.count_error.opacity = 1
        variables["id_list"] = dict()

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
        if int(current_row[3].replace('[size=30]', '').replace("[/size]", "")) in list(variables["id_list"].keys()):
            del variables["id_list"][int(current_row[3].replace('[size=30]', '').replace("[/size]", ""))]
        else:
            variables["id_list"][int(current_row[3].replace('[size=30]', '').replace("[/size]", ""))] = (
                int(current_row[0].replace('[size=30]', '').replace("[/size]", "").split(" x ")[0]))

    def add_first_nonconsumed(self):  # adds first ticket with a validity other than consumed to the id_list
        for row in variables["table_data"]:
            if row[1] != '[size=30]consumed[/size]':
                variables["id_list"][int(row[3].replace('[size=30]', '').replace("[/size]", ""))] = (
                    int(row[0].replace('[size=30]', '').replace("[/size]", "").split(" x ")[0]))
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
            size_hint=(0.425, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.main_button.bind(on_release=self.dropdown_validity.open)
        self.dropdown_validity.bind(on_select=lambda instance, x: setattr(self.main_button, 'text', x))

        self.add_widget(self.main_button, index=3)

    def load_dropdown_invalids(self):  # loads the dropdown for paying when an invalid ticket was scanned
        self.dropdown_invalids = DropDown()
        first = True
        huidig = ""
        floatalle = 0
        self.saved_i = 0
        for i in range(len(variables["table_data"])):
            amount = (variables["table_data"][i][2].replace("[size=30]€", "").replace("[/size]", "")
                      .replace("[size=30]NVT", "0"))
            amount = float(amount)
            if first and int(amount) != 0:
                huidig = "%.2f" % (amount / int(variables["table_data"][i][0].split(" x ")[0].replace("[size=30]", "")))
                self.saved_i = i
                first = False
            floatalle += amount
        if huidig == "":
            huidig = "%.2f" % 0
        huidig = "Huidig ticket: €" + huidig
        alle = "Alle Tickets: €" + "%.2f" % floatalle
        self.invalids_items = [huidig, alle]

        for item in self.invalids_items:
            opts_invalids = Button(
                text=item,
                size_hint_y=None,
                height=dp(30),
                font_name='app/assets/D-DIN.otf')
            opts_invalids.bind(on_release=lambda opt_invalids: self.dropdown_invalids.select(opt_invalids.text))
            self.dropdown_invalids.add_widget(opts_invalids)

        self.main_button_invalids = Button(
            text=huidig,
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0, 'y': 0.1},
            font_name='app/assets/D-DIN.otf')
        self.main_button_invalids.bind(on_release=self.dropdown_invalids.open)
        self.dropdown_invalids.bind(on_select=lambda instance, x: setattr(self.main_button_invalids, 'text', x))

        self.add_widget(self.main_button_invalids, index=2)

        self.confirm_button_invalids = Button(
            text="Valideer",
            size_hint=(0.5, 0.05),
            pos_hint={'x': 0.5, 'y': 0.1},
            font_name='app/assets/D-DIN.otf',
            background_normal='app/assets/buttonnormal.png',
            background_down='app/assets/buttondown.png')
        self.confirm_button_invalids.bind(on_release=lambda x: self.validate())
        self.add_widget(self.confirm_button_invalids, index=1)

    def validate(self):  # validates specifically the invalid tickets according to the invalid dropdown
        if self.main_button_invalids.text.startswith("Huidig ticket"):
            count = 1
            ids = int(self.product_table.row_data[self.saved_i][3].replace('[size=30]', '').replace("[/size]", ""))
            update_validity(variables["token"], ids, "consumed", count)

            # add the validated ticket to the history
            add_to_history(variables["main_button_events"].text, variables["email"], "enkel ongeldig ticket",
                           variables["voornaam"], variables["naam"], count, variables["prev_result"])
            # to_subtract = float(self.main_button_invalids.text.replace('Huidig ticket: €', ''))
            # new_to_pay = float(self.product_table.row_data[self.saved_i][2].replace('[size=30]€', '')
            #                    .replace("[/size]", "")) - to_subtract
            # self.product_table.update_row(self.product_table.row_data[self.saved_i],
            #                               [self.product_table.row_data[self.saved_i][0],
            #                                "[size=30]" + "consumed" + "[/size]",
            #                                '[size=30]€' + "%.2f" % new_to_pay + "[/size]",
            #                                self.product_table.row_data[self.saved_i][3]])
            response_dict = get_results(variables["prev_args"]["token"], variables["prev_args"]["uuid"],
                                        variables["prev_args"]["event_uuid"], False)
            if response_dict["validity"] == "APITokenError":
                send_to_screen(self, "APITokenError")  # send user to token refresh screen if token is expired
            variables["table_data"] = response_dict["table_data"]
            self.remove_widget(self.product_table)
            self.load_table(True)
        else:
            for i in range(len(variables["table_data"])):
                if self.product_table.row_data[i][1] == "[size=30]invalid[/size]":
                    ids = int(self.product_table.row_data[i][3].replace('[size=30]', '').replace("[/size]", ""))
                    count = int(self.product_table.row_data[i][0]
                                .replace('[size=30]', '').replace("[/size]", "").split(" x ")[0])
                    update_validity(variables["token"], ids, "consumed", count)

                    # add the validated ticket to the history
                    add_to_history(variables["main_button_events"].text, variables["email"],
                                   "meerdere ongeldige tickets", variables["voornaam"],
                                   variables["naam"], count, variables["prev_result"])

            response_dict = get_results(variables["prev_args"]["token"], variables["prev_args"]["uuid"],
                                        variables["prev_args"]["event_uuid"], False)
            if response_dict["validity"] == "APITokenError":
                send_to_screen(self, "APITokenError")  # send user to token refresh screen if token is expired
            variables["table_data"] = response_dict["table_data"]
            self.remove_widget(self.product_table)
            self.load_table(True)
