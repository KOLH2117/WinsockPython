import socket
import threading
import time
import tkinter as tk
from tkcalendar import Calendar, DateEntry
from tkinter import messagebox,ttk
from PIL import ImageTk,Image
from datetime import datetime
import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick 
from ctypes import windll
 
HEADER = 64
FORMAT = 'utf-8'

DISCONNECT_MESSAGE = "!DISCONNECT"

WRONG_PASSWORD = "Login Failed! Username or password is incorrect"

NOT_SIGN_UP = "User is not registered!"

LOGIN = "!LOGIN"
SIGN_UP = "!SIGN UP"
ALREADY_LOGGED = "Account has already logged in!"
LOGIN_MSG_SUCCESS = "Login successful!"
SIGN_UP_SUCCESS = "Sign up successful!"
ALREADY_EXIT = "Account has already exited!"
FAIL = "!FAIL"

FOUND = "!FOUND"
NOT_FOUND = "!NOT FOUND"
DONE = "!DONE"
ERROR = "!ERROR"


class Justify:
    def center(master,app_width,app_height):
        SCREEN_HEIGHT = master.winfo_screenheight()
        SCREEN_WIDTH = master.winfo_screenwidth()
        
        x = (SCREEN_WIDTH/2) - (app_width/2)  
        y = (SCREEN_HEIGHT/2) - (app_height/2)
        
        master.geometry(f"{app_width}x{app_height}+{int(x)}+{int(y)}")   

        
class Tk(tk.Tk):     
    def move_window(self):
        def SaveLastClickPos(event):
            global lastClickX, lastClickY
            lastClickX = event.x
            lastClickY = event.y


        def Dragging(event):
            x, y = event.x - lastClickX + root.winfo_x(), event.y - lastClickY + root.winfo_y()
            root.geometry("+%s+%s" % (x , y))
            
        self.bind('<Button-1>', SaveLastClickPos)
        self.bind('<B1-Motion>', Dragging)

    def set_appwindow(self):
        GWL_EXSTYLE=-20
        WS_EX_APPWINDOW=0x00040000
        WS_EX_TOOLWINDOW=0x00000080
        hwnd = windll.user32.GetParent(self.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        self.wm_withdraw()
        self.after(10, lambda: self.wm_deiconify())  
    
    """Xoá màn hình app"""
    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
        
class LoadingScreen(tk.Toplevel):
    def __init__(self,master):
        self.root = tk.Toplevel(master)
        self.master = master
        self.master.withdraw()
        self.app_width = 350
        self.app_height = 80
        self.root.resizable(False, False)
        Justify.center(self.root,self.app_width,self.app_height)
        self.root.wm_attributes("-transparentcolor",self.root["bg"])
        self.root.overrideredirect(1)
      
        
        self.frame = tk.Frame(self.root,width = 120,height = 28)
        self.frame.place(x = 120,y = 35 )
        tk.Label(self.frame,text= "Đang kết nối...",fg = "#3a7ff6",font= "Bahnschrift 13").place(x = 0,y=0)
        for i in range(16):
            tk.Label(self.root,bg ="#000",width = 2, height = 1).place(x =(i)*22,y = 10)

        self.root.update()
        self.thread = threading.Thread(target =self.play_animation)
        self.thread.setDaemon(True)
        self.thread.start()
        self.root.after(20, self.check_thread)
    def play_animation(self):
        for i in range(5):
            for j in range(16):
                tk.Label(self.root,bg ="#3a7ff6",width = 2, height = 1).place(x =(j)*22,y = 10)
                time.sleep(0.06)
                self.root.update_idletasks()
                tk.Label(self.root,bg ="#000",width = 2, height = 1).place(x =(j)*22,y = 10)
            
    def check_thread(self):
        if self.thread.is_alive():
            self.root.after(20, self.check_thread)
        else:
            self.root.destroy() 
            self.master.deiconify()
            # self.master.destroy()  
        
        
class CustomMessageBox:
    def __init__(self,master):
        self.root = tk.Toplevel()
        self.root.config(bg = "black")
        return
    def showwarningWithCounter(self,master):
        top = openNewWindow(master)
        top.title("Warning")
        top.icon()
        top.iconbitmap(f"{PATH_IMG}Client.ico")
        return
 
class SocketClient:
    def __init__(self):
        self.create_socket()
        return       
    
    def create_socket(self):
        self.CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_connections(self,HOST_IP):     
        self.HOST = HOST_IP
        self.PORT = 5050
        self.ADDR = (self.HOST,self.PORT)
    
        try:
            self.CLIENT.connect(self.ADDR)
        except socket.error as e:
            return False
        else:
            threading.Thread(target=self.listen_from_server).start()
            return True
            
    def send(self,msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            self.CLIENT.send(send_length)
            self.CLIENT.send(message)
        except socket.error as e:
            raise socket.error
        
    def receive(self):
        msg = ""
        try:
            msg_length = self.CLIENT.recv(HEADER).decode(FORMAT)
        except socket.error:
            raise socket.error
        else:
            if msg_length:
                msg = self.CLIENT.recv(int(msg_length)).decode(FORMAT) 
            return msg 

    def register(self,username, password):   
        try:
            self.send("Register")
            self.send(username)
            self.send(password)
            sign_up_msg = self.receive()
        except socket.error:
            return ERROR
        else:
            return sign_up_msg
            
    def login(self,username, password):        
        try:
            self.send("Login")
            self.send(username)
            self.send(password)
            login_msg = self.receive()
        except socket.error as e:
            return ERROR
        else:
            return login_msg
    
    def start_query_from_server(self,name,date):
        list_gold = []
        try:
            self.send("QUERY")
            self.send(name)
            self.send(date.strftime("%Y%m%d"))
            
            msg = self.receive()
            if msg == FOUND:
                length = self.receive()
                if length:
                    n = int(length)
                    for i in range(n):
                        name_recv = self.receive()
                        buy_price = self.receive() + ",000"
                        sell_price = self.receive() + ",000"
                        list_gold.append((name_recv,buy_price,sell_price))
                    msg = self.receive()
        except socket.error:
            return ERROR,None
        else:
            return msg,list_gold
    
    def get_chart_value(self,name):   
        valid_date = []
        buy = []
        sell = []
        try:
            """Gửi yêu cầu và thông tin đến server"""
            self.send("CHART")
            self.send(name)
            
            """Nhận dữ liệu từ server"""
            length = self.receive()
            length = int(length)
            valid_date = []
            buy = []
            sell = []
            for i in range(length):
                date_str = self.receive()
                valid_date.append(date_str)
                
            for i in range(length):
                buy_price = self.receive()
                buy.append(buy_price)
                
            for i in range(length):
                sell_price = self.receive()
                sell.append(sell_price)  
            
            """Nhận phản hồi từ server""" 
            msg = self.receive()    
        except socket.error:
            return ERROR,valid_date,buy,sell
        else:
            return msg,valid_date,buy,sell
            
    def server_crash(self):
        reconnect = messagebox.askquestion("Status","Server is disconnect.\nReconnect to server?")
        if reconnect == 0:
            root.destroy()
            os._exit(1)
        else:
            self.CLIENT.close()
            self.clear_frame(root)

    def listen_from_server(self):
        while True:
            msg = self.receive()
            print(msg)
            if msg == DISCONNECT_MESSAGE:
                messagebox.showwarning("Status", "Server will be shut down")
                break
        
    
    def disconnect(self):
        try:
            self.send(DISCONNECT_MESSAGE)
        finally: 
            self.CLIENT.close()
                
    
         

"""GUI của client"""   


"""Hàm để thoát chương trình"""
def exit():
    ask = messagebox.askyesno("Status","Exit Now?",parent = root)
    if ask == 0:
        return
    else:
        try:
            send(DISCONNECT_MESSAGE)
        finally: 
            CLIENT.close()
            root.destroy()
            sys.exit()

"""Tạo của sổ mới"""
def openNewWindow(master):
    newWindow = tk.Toplevel(master)
    newWindow.title("New Window")
    return newWindow


"""Form để tra giá vàng"""
class QueryGoldForm:
    def __init__(self,app):
        Tk.clear_frame(app.root)
        self.app = app
        self.root = app.root
        self.client = app.client
        
        
        
        """Các thông số và giao diện"""
        self.app_width = 900
        self.app_height = 600
        
        """Căn giữa chương trình"""
        Justify.center(self.root, self.app_width, self.app_height)
        
        self.canvas = tk.Canvas(
            self.root ,
            bg = "#3a6ff7",
            height = 600,
            width = 900,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            50, 0, 50+800, 0+600,
            fill = "#ffffff",
            outline = "")

        self.canvas.create_text(
            450.0, 44.5,
            text = "TRA CỨU GIÁ VÀNG",
            fill = "#000000",
            font = ("None", int(24.0)))

        self.canvas.create_rectangle(
            393, 65, 393+115, 65+2,
            fill = "#000000",
            outline = "")

        self.canvas.create_text(
            136.0+15, 138.5,
            text = "Nhập loại vàng:",
            fill = "#000000",
            font = ("None", int(18.0)))

        self.canvas.create_text(
            117.5+10, 212.5,
            text = "Chọn ngày:",
            fill = "#000000",
            font = ("None", int(18.0)))
        
        self.entry0_bg = self.canvas.create_image(
            330.0+25, 138.5,
            image = TEXT_BOX_GOLD_IMG)

        self.name = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            font=("",13))

        self.name.place(
            x = 240.5+15, y = 116+10,
            width = 179.0,
            height = 30)
        
        self.cal = DateEntry(
                        width=12,
                        background='darkblue',
                        foreground='white',
                        borderwidth=0,
                        showweeknumbers= False,
                        date_pattern= "dd/mm/yyyy",
                        maxdate= datetime.now())
        
        self.cal.place(
                x = 117.5+80, y = 200,
                width = 100,
                height = 30)
        
        self.search_button = tk.Button(
            image = SEARCH_BUTTON_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.find_button_clicked,
            relief = "flat")
        
        self.search_button.place(
            x = 686, y = 144,
            width = 143,
            height = 58)

        self.my_tree = ttk.Treeview(self.root)
        self.my_tree['columns'] = ("Đơn vị: đồng/lượng","Giá mua","Giá bán")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        """Chỉnh sửa màu cho bảng"""
        self.style.configure("Treeview",
                        background='#E9E9E9',
                        foreground= 'black',
                        rowheight = 25, 
                        fieldbackground='#E9E9E9',
                        )
        
        """Thay đổi màu khi người dùng chọn"""
        self.style.map('Treeview',background = [('selected','#0E74EC')])
        
        """Định dạng cột"""
        self.my_tree.column("#0",width = 0, stretch =tk.NO)
        self.my_tree.column("Đơn vị: đồng/lượng",anchor = tk.W,width = 140)
        self.my_tree.column("Giá mua",anchor = tk.W,width = 80)
        self.my_tree.column("Giá bán",anchor = tk.W,width = 80)
        
        """Tạo heading của bảng"""
        self.my_tree.heading("#0",text = "",anchor = tk.W)
        self.my_tree.heading("Đơn vị: đồng/lượng",text = "Đơn vị: đồng/lượng",anchor = tk.W)
        self.my_tree.heading("Giá mua",text = "Giá mua",anchor = tk.W)
        self.my_tree.heading("Giá bán",text = "Giá bán",anchor = tk.W)
        
        self.my_tree.place(
            x =70 ,y = 250,
            width = 760,
            height = 330
        )
        
        self.my_tree.bind("<Double-1>",self.chart_button_clicked)
        
        self.minimize_button = tk.Button(
            image = MINIMIZE_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command =   app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 802 , y = 0,
            width = 24,
            height = 24)
        
        self.exit_button = tk.Button(
        image = EXIT_BUTTON_IMG,
        borderwidth = 0,
        highlightthickness = 0,
        command = self.exit_button_clicked,
        relief = "flat")

        self.exit_button.place(
            x = 826, y = 0,
            width = 24,
            height = 24)
        """Cờ hiệu và các hàm chức năng"""
        self.status = None
        self.flag = 0
        
    
    """Các hàm hỗ trợ"""       
    def clear_table(self):
        if self.my_tree.get_children():
            for record in self.my_tree.get_children():
                 self.my_tree.delete(record)
                 
    def check_input(self):
        self.clear_table()
            
        if not self.name:
            messagebox.showwarning("Status","Please fill the entry!")
            return False  
        
        return True
    
    """Các hàm để hiện thanh tiến trình"""
    def start_progress_bar(self):
        self.handle_thread = [
            threading.Thread(target = self.get_list_gold_threads),
            threading.Thread(target = self.get_value_of_chart)
            ]
        s = ttk.Style()
        TROUGH_COLOR = 'white'
        BAR_COLOR = '#3A6FF7'
        s.configure("bar.Horizontal.TProgressbar", 
                    troughcolor=TROUGH_COLOR, 
                    bordercolor=TROUGH_COLOR, 
                    background=BAR_COLOR, 
                    lightcolor=BAR_COLOR, 
                    darkcolor=BAR_COLOR,
                    borderwidth = 0)
        
        self.process = ttk.Progressbar(self.root,style="bar.Horizontal.TProgressbar",orient=tk.HORIZONTAL,length=300,mode = "indeterminate")
        self.process.place(x = 50,y = 250+330,
                    width = 760+40,height = 20)
        
        
        self.open_chart_thread = self.handle_thread[self.flag]
        self.open_chart_thread.setDaemon(True)
        self.process.start()
        self.open_chart_thread.start()
        self.root.after(20, self.check_thread)
        
    def check_thread(self):
        if self.open_chart_thread.is_alive():
            self.root.after(20, self.check_thread)
        else:
            self.process.stop()
            self.process.destroy()
            if self.flag == 0:
                self.display_table()
            else:
                self.open_chart_window()
            
            
    """Hàm để lấy dữ liệu từ server """
    def get_list_gold_threads(self):
        self.status,self.list_gold = self.client.start_query_from_server(self.name.get(),self.cal.get_date())
    
    """Hàm hiện kết quả lên bảng"""    
    def display_table(self):
        if self.status == DONE:
            count = 0
            for item in self.list_gold:
                self.my_tree.insert('',index='end',iid = count,text='',values= (item[0],item[1],item[2]))
                count += 1
            messagebox.showinfo("Status","Success")
        elif self.status == NOT_FOUND:
            messagebox.showerror("Status",NOT_FOUND)  
        elif self.status == ERROR:
            return
  
    """Hàm để lấy dữ liệu đồ thị từ server"""      
    def get_value_of_chart(self):
        """Lấy dòng người dùng đang chọn"""
        selected = self.my_tree.focus()
        
        """Lấy dữ liệu của dòng đó"""
        value = self.my_tree.item(selected,'values')
        
        self.chart_name = value[0]
        self.search_button['state'] = "disabled"
        
        """Tạo yêu cầu gửi tới server và trả về trạng thái,giá trị cột ngày, và 2 giá trị giá mua và giá bán theo từng ngày"""
        self.status,self.valid_date,self.buy,self.sell  = self.client.get_chart_value(self.chart_name)
        
    """Mở đồ thị giá vàng"""
    def open_chart_window(self,event=None):
        if self.status == ERROR:
            return        
        self.search_button['state'] = 'normal'
         
        self.valid_date = [datetime.strptime(item,"%d/%m/%Y") for item in self.valid_date]
        self.buy = [int(item.replace(",","")) for item in self.buy]
        self.sell = [int(item.replace(",","")) for item in self.sell]
        
        fig, ax = plt.subplots()
        lines = []
        #plt.subplots_adjust(left=0.1, bottom=0.1, right=0.6, top=0.8)
        l, = ax.plot(self.valid_date, self.buy, label="Mua")
        lines.append(l)
        l, = ax.plot(self.valid_date, self.sell, label="Bán") 
        lines.append(l)
        
        fmt = '{x:,.0f}k'
        tick = mtick.StrMethodFormatter(fmt)
        ax.yaxis.set_major_formatter(tick)
        
        annot = ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def update_annot(line, idx):
            posx, posy = [line.get_xdata()[idx], line.get_ydata()[idx]]
            annot.xy = (mdates.date2num(posx), posy)
            text = f'Ngày: {posx.strftime("%#d/%m/%Y")}\n{line.get_label()}: {posy:,.0f}k'
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.4)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for line in lines:
                    cont, ind = line.contains(event)
                    if cont:
                        update_annot(line, ind['ind'][0])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
        fig.canvas.manager.set_window_title('Đồ thị thay đổi giá vàng')
        
        plt.subplots_adjust(right=0.8)
        plt.title(f"{self.chart_name}",pad= 20)
        plt.gcf().autofmt_xdate()
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        plt.legend(handles=lines,bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.show()

    def chart_button_clicked(self,event = None):
        self.flag = 1
        self.start_progress_bar()
    
    def find_button_clicked(self,event = None):
        if self.check_input() == False:
            return
        self.flag = 0
        self.start_progress_bar()
        
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Status","Exit Now?",parent = self.root)
        if ask == 0:
            return
        else:
            self.client.disconnect()
            self.root.destroy()
            sys.exit()    

"""Form để đăng ký"""  
class SignUpForm:
    def __init__(self,app):
        Tk.clear_frame(app.root)
        
        self.app = app
        self.root = app.root
        self.client = app.client
        
        self.app_width = 600
        self.app_height = 300
        
        Justify.center(self.root,self.app_width,self.app_height)
        
        self.canvas = tk.Canvas(
            self.root,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            100, 0, 100+400, 0+300,
            fill = "#ffffff",
            outline = "")

        self.canvas.create_text(
            299.5, 25.5,
            text = "ĐĂNG KÝ TÀI KHOẢN",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.entry0_bg = self.canvas.create_image(
            299.5, 89.0,
            image = TEXT_BOX)

        self.username = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0)

        self.username.delete(0,'end')
        self.username.place(
            x = 191.0+2, y = 64+22,
            width = 217.0,
            height = 25)

        self.entry1_bg = self.canvas.create_image(
            299.5, 150.0,
            image = TEXT_BOX)

        self.password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show = "*")
        self.password.delete(0,'end')
        self.password.bind("<Return>",self.sign_up_button_clicked)
        self.password.place(
            x = 191.0+2, y = 125+22,
            width = 217.0,
            height = 25)

        self.entry2_bg = self.canvas.create_image(
            299.5, 211.0,
            image = TEXT_BOX)

        self.re_enter_password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show="*")
        self.re_enter_password.delete(0,'end')
        self.re_enter_password.bind("<Return>",self.sign_up_button_clicked)
        self.re_enter_password.place(
            x = 191.0+2, y = 186+22,
            width = 217.0,
            height = 25)
        
        self.canvas.create_text(
            219.5+4, 78.5,
            text = "Tài khoản",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            219.5+5, 138.0,
            text = "Mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            242.0+15, 199.0,
            text = "Xác nhận mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))


        self.canvas.create_rectangle(
            264, 37, 264+72, 37+2,
            fill = "#000000",
            outline = "")

        self.b1 = tk.Button(
            image = SIGN_UP_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.sign_up_button_clicked,
            relief = "flat")

        self.b1.place(
            x = 248, y = 248,
            width = 103,
            height = 38)

        self.show = tk.Button(
            image = SHOW_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            relief = "flat")

        self.show.bind("<Button-1>",(lambda event: self.show_and_hide_password(button = self.show,entry = (self.password,self.re_enter_password))))
                
        self.show.place(
            x = 371, y = 186,
            width = 47,
            height = 50)
        
        self.minimize_button = tk.Button(
            image = MINIMIZE_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 452 , y = 0,
            width = 24,
            height = 24)
        
        self.exit_button = tk.Button(
        image = EXIT_BUTTON_IMG,
        borderwidth = 0,
        highlightthickness = 0,
        command = self.exit_button_clicked,
        relief = "flat")

        self.exit_button.place(
            x = 476, y = 0,
            width = 24,
            height = 24)
    
    def show_and_hide_password(self,even = None,*args,**kwargs):
        for entry in kwargs["entry"]:
            if entry['show'] == "*":
                kwargs["button"].config(image = HIDE_IMG)
                entry.config(show = "")
            else:
                kwargs["button"].config(image = SHOW_IMG)
                entry.config(show = "*")

    def checkInput(self,username,password, re_enter_password):
        if password == "" or username == "" or re_enter_password =="":
            messagebox.showwarning("Warning","Please enter both of field")
            return False
        msg = "Valid"
        if len(password) < 8:
            msg = "Password must be at least 8 characters contain"
        elif re.search('[0-9]',password) is None:
            msg = "Make sure your password has a number in it"
        elif re.search('[A-Z]',password) is None:
            msg = "Make sure your password has a capital letter in it"
        
        if re_enter_password:
            if password != re_enter_password:
                messagebox.showwarning("Warning","Password does not match")
                return False
        if msg == "Valid":
            return True       
        else:
            messagebox.showwarning("Invalid Password",msg)
            return False    
    
    def sign_up_button_clicked(self):
        username = self.username.get()
        password = self.password.get()
        re_enter_password = self.re_enter_password.get()
        if self.checkInput(username,password,re_enter_password):
            status = self.client.register(username,password)
            if status == ALREADY_EXIT:
                messagebox.showwarning("Status","The username is already taken")
            elif status == SIGN_UP_SUCCESS:
                messagebox.showinfo("Status","Sign up successfully")
                self.login_form = LoginForm(self.app)
            elif status == ERROR:
                return
            
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Status","Exit Now?",parent = self.root)
        if ask == 0:
            return
        else:
            self.client.disconnect()
            self.root.destroy()
            sys.exit()
 
 
"""Form để đăng nhập"""       
class LoginForm:
    def __init__(self,app):
        Tk.clear_frame(app.root)
        
        self.app = app
        self.root = app.root
        self.client = app.client
        
        self.app_width = 600
        self.app_height = 300
        
        Justify.center(self.root,self.app_width,self.app_height)
        
        self.canvas = tk.Canvas(
            self.root,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            100, 0, 100+400, 0+300,
            fill = "#ffffff",
            outline = "")

        self.canvas.create_text(
            298.5, 37.5,
            text = "ĐĂNG NHẬP VÀO SERVER",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.entry0_bg = self.canvas.create_image(
            298.5, 108.0,
            image = TEXT_BOX)

        self.username = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0)

        self.username.delete(0,'end')
        self.username.place(
            x = 190.0+2, y = 83+20,
            width = 217.0,
            height = 25)

        self.entry1_bg = self.canvas.create_image(
            298.5, 186.0,
            image = TEXT_BOX)

        self.password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show = "*")

        self.password.delete(0,'end')
        self.password.bind("<Return>",self.login_button_clicked)
        
        self.password.place(
            x = 190.0+2, y = 161+21,
            width = 217.0,
            height = 25)

        self.canvas.create_text(
            218.5+5, 93.5+2,
            text = "Tài khoản",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            218.5+5, 174.0,
            text = "Mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_rectangle(
            264, 50, 264+72, 50+2,
            fill = "#000000",
            outline = "")

        self.login_button = tk.Button(
            image = SIGN_IN_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.login_button_clicked,
            relief = "flat")

        self.login_button.place(
            x = 246, y = 239,
            width = 103,
            height = 38)

        self.show = tk.Button(
            image = SHOW_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            relief = "flat")

        self.show.bind("<Button-1>",(lambda event: self.show_and_hide_password(button = self.show,entry = (self.password,))))
        self.show.place(
            x = 370, y = 161,
            width = 47,
            height = 50)

        self.sign_up = tk.Button(
            image = CREATE_ACC_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.create_account_button_clicked,
            relief = "flat")

        self.sign_up.place(
            x = 339, y = 215,
            width = 78,
            height = 13)

        self.minimize_button = tk.Button(
            image = MINIMIZE_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 452 , y = 0,
            width = 24,
            height = 24)
        
        self.exit_button = tk.Button(
            image = EXIT_BUTTON_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.exit_button_clicked,
            relief = "flat")

        self.exit_button.place(
            x = 476, y = 0,
            width = 24,
            height = 24)
       
    def show_and_hide_password(self,even = None,*args,**kwargs):
        
        for entry in kwargs["entry"]:
            if entry['show'] == "*":
                kwargs["button"].config(image = HIDE_IMG)
                entry.config(show = "")
            else:
                kwargs["button"].config(image = SHOW_IMG)
                entry.config(show = "*")
                
    def checkInput(self,username,password):
        if password == "" or username == "":
            messagebox.showwarning("Warning","Please enter both of field")
            return False
        
        msg = "Valid Password"
        if len(password) < 8:
            msg = "Password must be at least 8 characters contain"
        elif re.search('[0-9]',password) is None:
            msg = "Make sure your password has a number in it"
        elif re.search('[A-Z]',password) is None:
            msg = "Make sure your password has a capital letter in it"
        
        if msg == "Valid Password":
            return True       
        else:
            messagebox.showwarning("Invalid Password",msg)
            return False  
    
    def create_account_button_clicked(self,Even = None):
        self.register = SignUpForm(self.app)
    
    def login_button_clicked(self ,even = None):
        
        if self.checkInput(self.username.get(), self.password.get()):
            t = threading.Thread(target = self.login)
            t.start()
            t.setDaemon(True)
    
    def login(self):
        status = self.client.login(self.username.get(),self.password.get())
        if status == LOGIN_MSG_SUCCESS:
            messagebox.showinfo("Status",LOGIN_MSG_SUCCESS)
            self.query_gold_form = QueryGoldForm(self.app)
        elif status == ALREADY_LOGGED:
            messagebox.showwarning("Status",ALREADY_LOGGED + "\nPlease use another account")
        elif status == WRONG_PASSWORD:
            messagebox.showerror("Status" , WRONG_PASSWORD) 
        elif status == NOT_SIGN_UP:
            messagebox.showwarning("Status" , "Your account is not exists" )
        elif status == ERROR:
            return       
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Status","Exit Now?",parent = self.root)
        if ask == 0:
            return
        else:
            self.client.disconnect()
            self.root.destroy()
            sys.exit() 
 
"""Form ban đầu để nhập địa chỉ IP SERVER""" 
class InputHostIp(tk.Frame):
    def __init__(self,app):
        self.app = app
        self.root = app.root
        self.client = app.client
        self.app_width = 600
        self.app_height = 300
        
        Justify.center(self.root ,self.app_width,self.app_height)
    
        self.canvas = tk.Canvas(
            self.root ,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            300, 0, 300+300, 0+300,
            fill = "#ffffff",
            outline = "")

        self.entry0_bg = self.canvas.create_image(
            449.5, 137.5,
            image = HOST_IMG)

        self.host_input_field = tk.Entry(
            bd = 0,
            bg = "#dedede",
            highlightthickness = 0)

        self.host_input_field.insert(tk.END,"HOST IP")
        self.host_input_field.bind("<Button-1>",(lambda event: self.host_input_field.delete(0,'end')))
        self.host_input_field.bind("<Return>", self.connect_button_clicked)
        
        self.host_input_field.place(
            x = 380.0-3, y = 115+21,
            width = 139.0,
            height = 25)

        self.canvas.create_text(
            384.5, 126.5,
            text = "IP",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            450.5, 50.0,
            text = "NHẬP HOST IP",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_rectangle(
            428, 61, 428+44, 61+1,
            fill = "#000000",
            outline = "")

        self.b0 = tk.Button(
            image = CONNECT_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.connect_button_clicked,
            relief = "flat")

        self.b0.place(
            x = 410, y = 219,
            width = 80,
            height = 40)
        
        self.canvas.create_text(
            140, 50.0,
            text = "CHƯƠNG TRÌNH TRA CỨU",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            33, 80,
            text = "GIÁ",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            85, 80,
            text = "VÀNG",
            fill = "#FAFF00",
            font = ("Roboto-Bold", int(15.0)))
        
        self.label1 = tk.Label(image=GOLD_IMG)
        self.label1.image = GOLD_IMG
        self.label1.place(x=150, y=90, width= 100,height=100)
        
        self.canvas.create_text(
            80, 220,
            text = "Phát triển bởi:",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            142, 250,
            text = "20127067 - Trần Hồng Quân",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            154, 280,
            text = "20127665 - Dương Quang Vinh",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.minimize_button = tk.Button(
            image = MINIMIZE_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 552, y = 0,
            width = 24,
            height = 24)
        
        self.exit_button = tk.Button(
            image = EXIT_BUTTON_IMG,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.exit_button_clicked,
            relief = "flat")

        self.exit_button.place(
            x = 576, y = 0,
            width = 24,
            height = 24)
    
    
    
    def connect_button_clicked(self,event = None):
        HOST_IP = self.host_input_field.get()
        if HOST_IP == "":
            messagebox.showwarning("Warning","Please input the field")
            return

        HOST_IP_PREFIX = HOST_IP.split('.')
        if len(HOST_IP_PREFIX) < 4 or len(HOST_IP_PREFIX) > 4:
            messagebox.showerror("Error","Not a IP-v4 prefix")
            return 
        else:
            for Val in HOST_IP_PREFIX:
                try:
                    Val = int(Val)
                    if Val > 255:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error","Not a IP-v4 prefix")
                    return 
                
        
        if self.client.start_connections(HOST_IP) == True:
            messagebox.showinfo("Status", f"Connected to {HOST_IP}")
            self.login = LoginForm(self.app)
        else:
            messagebox.showerror("Status", "Can't connect to server")
        
    def exit_button_clicked(self):
        self.root.destroy()
        sys.exit()
        
class ClientApplication(tk.Frame):
    def __init__(self,master,*args,**kwargs):
        self.z = 0
        self.client = SocketClient()
        self.root = master
        
        self.root.configure(bg = "#3a7ff6")
        self.root.overrideredirect(True)
        self.root.after(10, lambda: Tk.set_appwindow(self.root))
        self.root.resizable(False, False)
    
        self.root.tk.call('wm', 'iconphoto', root._w, GOLD_IMG)
        self.root.bind('<Map>',  self.frameMapped) 
        
        Tk.move_window(self.root)
        self.input_host = InputHostIp(self)
        
    def minimizeGUI(self):
        self.root.state('withdrawn')
        self.root.overrideredirect(False)
        self.root.state('iconic')
        self.z = 1

    def frameMapped(self,event=None):
        self.root.overrideredirect(True)
        if self.z == 1:
            Tk.set_appwindow(self.root)
            self.z = 0
   
"""Lấy đường dẫn của chương trình"""
DIR = os.path.dirname(__file__)
PATH_IMG = f"{DIR}/Images/"
root = tk.Tk()
"""Danh sách cái hình ảnh chương trình cần"""
img = Image.open(f"{PATH_IMG}Gold_img.png")
img = img.resize((100, 100))
GOLD_IMG = ImageTk.PhotoImage(img)

HOST_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}Host_img.png")
EXIT_BUTTON_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}exit_button.png")
TEXT_BOX = ImageTk.PhotoImage(file=f"{PATH_IMG}TextBox.png")
SIGN_IN_IMG = ImageTk.PhotoImage(file=f"{PATH_IMG}Login_Button.png")
CONNECT_IMG = ImageTk.PhotoImage(file=f"{PATH_IMG}Connect_Button.png")
SHOW_IMG = ImageTk.PhotoImage(file = f"{PATH_IMG}Show.png")
HIDE_IMG = ImageTk.PhotoImage(file = f"{PATH_IMG}Hide.png")
CREATE_ACC_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}Create_account.png")
SIGN_UP_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}Sign_up_Button.png")
TEXT_BOX_GOLD_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}gold_input.png")
SEARCH_BUTTON_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}Search_button.png")
MINIMIZE_IMG = ImageTk.PhotoImage(file= f"{PATH_IMG}Minimize.png")


if __name__ == "__main__":
    app = ClientApplication(root)
    # Loading = LoadingScreen(root)
    root.mainloop()
    