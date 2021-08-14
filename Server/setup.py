import cx_Freeze
import sys
import os

base = None

if sys.platform == 'win32':
    base = "Win32Gui"
    
os.environ['TCL_LIBRARY'] = r'C:\Users\duong\AppData\Local\Programs\Python\Python39\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\duong\AppData\Local\Programs\Python\Python39\tcl\tk8.6'
   
executables = [cx_Freeze.Executable("Server.py",base=base,icon= "Images/Server.ico")]

cx_Freeze.setup(
    name = "ServerApplication",
    options = {"build_exe" : {
        "packages" : [
            "tkinter",
            "requests",
            "sqlite3",
            "os",
            "threading",
            "socket",
            "json",
            "time",
            "bs4",
            "datetime"],
        "excludes" : [
            "matplotlib",
            "test",
            "psutil",
            ],
        "include_files" : ["Images"]}},
    version = "0.1",
    description = "Server Tra cứu giá vàng",
    executables = executables
)