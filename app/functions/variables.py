# here all variables are kept that need to be shared across screens or need to be saved when switched to another screen
variables = {
    "token": None,
    "visibility": False,
    "iconpath": "",

    "prev_screen": "",
    "prev_result": "",
    "prev_args": dict(),
    "current_selected_event": "",

    "voornaam": "",
    "naam": "",
    "email": "",
    "lidstatus": "",
    "table_data": "",
    "validity": "",
    "checkout_status": "",
    "notes": "",
    "id_list": [],

    "main_button_events": None,
    "main_button_events_price": None,
    "main_button_events_totals": None,
    "event_items": dict(),
    "history_table": [],

    "pc": bool,
    "api_url": "",
    "api_suffix": "",

    "options": {"auto_return": False,
                "enable_image_capture": False}
}
