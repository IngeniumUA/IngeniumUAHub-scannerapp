from app.functions.variables import variables
from app.api.hub_api import refresh_token
from app.api.hub_api import PyToken


def send_to_screen(self, validity) -> None:
    """
    Function to send the user to the appropriate screen based on the validity

    Examples
    --------
    >>> send_to_screen(self, "valid")
    None

    Parameters
    ----------
    :param self:
    :param validity:

    Returns
    -------
    :return: None
    """
    # detect which validity or error the qr code has and send user to the appropriate screen
    if validity == "APITokenError":
        variables["prev_result"] = ""
        variables["token"] = refresh_token(variables["token"])
        # when the token is expired, attempt to refresh the token. if this fails, bring user back to login screen
        if variables["token"] == PyToken(access_token="", refresh_token=""):
            variables["prev_screen"] = "scan"
            self.manager.transition.direction = "right"
            self.manager.current = "login"
        else:
            self.manager.transition.direction = "left"
            self.manager.current = "token"

    elif validity == "valid":
        variables["iconpath"] = "app/assets/checkmark.png"  # set icon to green checkmark
        self.manager.transition.direction = "left"
        self.manager.current = "valid_invalid_used"

    elif validity == "invalid":
        variables["iconpath"] = "app/assets/dashmark.png"  # set icon to orange "stop sign"
        self.manager.transition.direction = "left"
        self.manager.current = "valid_invalid_used"

    # when ticket is invalid but data was still acquired
    elif (validity == "consumed" or validity == "eventError"
          or validity == "manually_verified"):
        variables["iconpath"] = "app/assets/xmark.png"  # set icon to red cross
        self.manager.transition.direction = "left"
        self.manager.current = "valid_invalid_used"

    elif validity == "UUIDError":
        self.manager.transition.direction = "left"
        self.manager.current = "payless"

    elif validity == "emptyEvent":  # when no event was given
        self.ids.event_empty.opacity = 1

    elif validity == "scan_screen":  # when the user needs to get sent back to the scan screen
        self.manager.transition.direction = "right"
        self.manager.current = "scan"
    else:
        print("ERROR - validity unknown")  # this should never happen, print for debugging
