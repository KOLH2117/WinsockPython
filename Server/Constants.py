import socket

"""1 số hàm số"""
HEADER = 64
HOST = socket.gethostbyname(socket.gethostname())

PORT = 5050
ADDR = (HOST,PORT)
FORMAT = 'utf-8'

CLIENT_DISCONNECT_MSG = "Client has disconnected from server." 
DISCONNECT_MESSAGE = "!DISCONNECT"

WRONG_PASSWORD = "Login Failed! Username or password is incorrect"

NOT_SIGN_UP = "User is not registered!"

"""Command"""
LOGIN = "!LOGIN"
SIGN_UP = "!SIGN UP"
QUERY = "!QUERY"
CHART = "!CHART"

ALREADY_LOGGED = "Account has already logged in!"
LOGIN_MSG_SUCCESS = "Login successful!"
SIGN_UP_SUCCESS = "Sign up successful!"
ALREADY_EXIT = "Account has already exited!"
FAIL = "!FAIL"

FOUND = "!FOUND"
NOT_FOUND = "!NOT FOUND"
DONE = "!DONE"
ERROR = "!ERROR"

ICON = 'Images\Server.ico'