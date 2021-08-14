import cx_Freeze
import sys
import os


base = None

if sys.platform == 'win32':
    base = "Win32Gui"

os.environ['TCL_LIBRARY'] = r'C:\Users\duong\AppData\Local\Programs\Python\Python39\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\duong\AppData\Local\Programs\Python\Python39\tcl\tk8.6'
  
executables = [cx_Freeze.Executable("Client.py",base=base,icon= "Images/Client.ico")]

cx_Freeze.setup(
    name = "ClientApplication",
    options = {"build_exe" : {
        "packages" : [
            "socket",
            "datetime",
            "re",
            "tkinter",
            "matplotlib",
            "tkcalendar",
            "json",
            "time",
            "threading",
            "socket",],
        "excludes" : ["requests","test","psutil","pandas","notebook","asyncio","qtpy","sqlite3","unittest","testpath","traitlets","multiprocessing"], 
        "include_files" : ["Images"]}},
    version = "0.1",
    description = "Client",
    executables = executables
)