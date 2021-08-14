HEADER = 64
FORMAT = 'utf-8'




"""Command"""
LOGIN = "!LOGIN"
SIGN_UP = "!SIGN UP"
QUERY = "!QUERY"
CHART = "!CHART"
DISCONNECT_MESSAGE = "!DISCONNECT"
FAIL = "!FAIL"
FOUND = "!FOUND"
NOT_FOUND = "!NOT FOUND"
DONE = "!DONE"
ERROR = "!ERROR"

WRONG_PASSWORD = "Login Failed! Username or password is incorrect"
NOT_SIGN_UP = "User is not registered!"
ALREADY_LOGGED = "Account has already logged in!"
LOGIN_MSG_SUCCESS = "Login successful!"
SIGN_UP_SUCCESS = "Sign up successful!"
ALREADY_EXIT = "Account has already exited!"


PATH_IMG = "Images/"
IMG_LIST = {
        "CLIENT_ICON"       : [f"{PATH_IMG}Client.ico",None],

        "GOLD_IMG"          : [f"{PATH_IMG}Gold_img.png", None],
        "HOST_INPUT"        : [f"{PATH_IMG}Host_input.png", None],
        "TEXT_BOX"          : [f"{PATH_IMG}Text_box.png", None],
        "TEXT_BOX_GOLD_IMG" : [f"{PATH_IMG}Gold_input.png",None],
        
        "DELETE_BUTTON"     : [f"{PATH_IMG}Delete_button.png", None],
        "SHOW_IMG"          : [f"{PATH_IMG}Show.png", None],
        "HIDE_IMG"          : [f"{PATH_IMG}Hide.png", None],
        "CREATE_ACC_IMG"    : [f"{PATH_IMG}Create_account.png", None],
        "SIGN_UP_IMG"       : [f"{PATH_IMG}Sign_up_Button.png", None],
        "SEARCH_BUTTON_IMG" : [f"{PATH_IMG}Search_button.png",None],
        "MINIMIZE_IMG"      : [f"{PATH_IMG}Minimize_button.png", None ],
        "GOBACK_IMG"        : [f"{PATH_IMG}Goback_button.png",None],
        "EXIT_BUTTON_IMG"   : [f"{PATH_IMG}Exit_button.png", None],
        "CONNECT_IMG"       : [f"{PATH_IMG}Connect_Button.png", None],
        "SIGN_IN_IMG"       : [f"{PATH_IMG}Login_Button.png", None]
    }