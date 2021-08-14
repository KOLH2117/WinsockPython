import tkinter as tk
from UI import Tk,InputHostIp 
from SocketClient import SocketClient 

class ClientApplication:
    def __init__(self,master,*args,**kwargs):
        """Khởi tạo"""
        self.z = 0
        self.root = master
        self.client = SocketClient()
        
        Tk.move_window(self.root)
        self.client.set_app(self)
        self.root.title("CLIENT")
        self.root.configure(bg = "#3a7ff6")
        self.root.overrideredirect(True)
        self.root.after(10, lambda: Tk.set_appwindow(self.root))
        self.root.resizable(False, False)
        self.root.bind('<Map>',  self.frameMapped) 
        
        """Màn hình nhập IP"""
        self.input_host = InputHostIp(self)
    
    """Hàm thu nhỏ màn hình"""
    def minimizeGUI(self):
        self.root.state('withdrawn')
        self.root.overrideredirect(False)
        self.root.state('iconic')
        self.z = 1

    """Hàm bổ trợ"""
    def frameMapped(self,event=None):
        self.root.overrideredirect(True)
        if self.z == 1:
            Tk.set_appwindow(self.root)
            self.z = 0
            
    """Hàm reset chương trình"""        
    def reset(self):
        self.delete_app()
        self.__init__(self.root)
    
    """Hàm xoá chương trình cũ"""
    def delete_app(self):
        del self.client
        del self.input_host
        