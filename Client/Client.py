import socket
import threading
import time
import tkinter as tk
from tkcalendar import Calendar, DateEntry
from tkinter import messagebox,ttk
from PIL import ImageTk,Image
from datetime import datetime
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick 
 
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
LOGIN_MSG_SUCCESS = "Login successful!"
WRONG_PASSWORD = "Login Failed! Username or password is incorrect"
NOT_REGISTERED = "User is not registered!"
ALREADY_LOGGED = "Account has already logged in!"

#Backend
def server_crash():
    reconnect =messagebox.askquestion("Status","Server is disconnect.\nReconnect to server?")
    if reconnect == 0:
        on_closing()
    else:
        client_socket.close()
        clear_frame(root)
        input_host()
        
def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    try:
        client_socket.send(send_length)
        client_socket.send(message)
    except socket.error as e:
        raise socket.error(e)
      
def receive():
    """Handles receiving of messages."""
    msg = ""
    try:
        msg_length = client_socket.recv(HEADER).decode(FORMAT)
    except socket.error:
        raise socket.error
    except OSError:  # Possibly client has left the chat.
        raise OSError
    else:
        if msg_length:
            msg = client_socket.recv(int(msg_length)).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                raise socket.error(DISCONNECT_MESSAGE)  
        return msg

def on_closing():
    try:
        status = client_socket.fileno()
    except NameError:
        root.destroy()
    else:
        if status != -1:
            try:
                send(DISCONNECT_MESSAGE)
            finally: 
                client_socket.close()
                root.destroy()
        else:
            root.destroy()

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def check_password(password):
    return True 


def start_query_from_server(name,date,my_tree):
    if my_tree.get_children():
        for record in my_tree.get_children():
            my_tree.delete(record)
    global date_charts 
    date_charts = date
    if not name:
        messagebox.showwarning("Status","Please fill the entry!")
        return
    try:
        send("QUERY")
    except socket.error:
        server_crash()
    else:
        send(name)
        send(date.strftime("%Y%m%d"))
        
        msg = receive()
        if msg == "FOUND":
            length = receive()
            if length:
                n = int(length)
                count = 0
                for i in range(n):
                    name_recv = receive()
                    buy_price = receive() + ",000"
                    sell_price = receive() + ",000"
                    my_tree.insert('',index='end',iid = count,text='',values= (name_recv,buy_price,sell_price))
                    count += 1
                msg = receive()
                if msg  == "DONE":
                    messagebox.showinfo("Status","Success")
        elif msg == "NOT FOUND":
            messagebox.showerror("Status",msg)
        
def register(username, password,re_enter_password):   
    if password == "" or username == "" or re_enter_password == "":
        messagebox.showwarning("Warning","Please enter all of fields")
        return
    else:
        if len(password) < 8:
            messagebox.showwarning("Password","Password must be at least 8 characters contain")
            return
        else:
            if re_enter_password != password:
                messagebox.showwarning("Warning","Password does not match")
                return
            #check_password(password)
    
    try:
        send("Register")
        send(username)
        send(password)
    except socket.error:
        server_crash()
    else:
        login_msg = receive()
        if login_msg == "Exist":
            messagebox.showwarning("Account is already exist","The username is already taken")
        elif login_msg == "Success":
            messagebox.showinfo("Status","Sign up successfully")
            login_form()

def login(username, password):
    if password == "" or username == "":
        messagebox.showwarning("Warning","Please enter both of field")
        return
    else:
        if len(password) < 8:
            messagebox.showwarning("Password","Password must be at least 8 characters contain")
            return
        else:
            check_password(password)
            
    try:
        send("Login")
        send(username)
        send(password)
    except socket.error as e:
        server_crash()
    else:
        try:
            login_msg = receive()
        except socket.error:
            server_crash()
        else:
            if login_msg == LOGIN_MSG_SUCCESS:
                messagebox.showinfo("Status",LOGIN_MSG_SUCCESS)
                query_gold_form()
                return
            elif login_msg == ALREADY_LOGGED:
                messagebox.showwarning("Status",ALREADY_LOGGED + "\nUse another account")
            
            elif login_msg == WRONG_PASSWORD:
                messagebox.showerror("Status" , WRONG_PASSWORD)
            elif login_msg == NOT_REGISTERED:
                register = messagebox.showwarning("Account is not registered" , "Your account is not registered!" )
                register = messagebox.askyesno("Not registered", "Register Now???")
                if register == 0:
                    return
                else:
                    register_form() 
      
def start_connections(HOST_IP):     
    global HOST,PORT,ADDR,client_socket
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
    HOST = HOST_IP
    PORT = 5050
    ADDR = (HOST,PORT)
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   
    try:
        client_socket.connect(ADDR)
    except socket.error as e:
        messagebox.showerror("Status", "Can't connect to server")
    else:
        messagebox.showinfo("Status", f"Connected to {HOST}")
        login_form()

#GUI of client        
def openNewWindow():
    # Toplevel object which will 
    # be treated as a new window
    newWindow = tk.Toplevel(root)
    
    # sets the title of the
    # Toplevel widget
    newWindow.title("New Window")

    return newWindow

def open_chart(date,my_tree,search_button):
    s = ttk.Style()
    #s.theme_use('clam')
    TROUGH_COLOR = 'white'
    BAR_COLOR = '#3A6FF7'
    s.configure("bar.Horizontal.TProgressbar", 
                troughcolor=TROUGH_COLOR, 
                bordercolor=TROUGH_COLOR, 
                background=BAR_COLOR, 
                lightcolor=BAR_COLOR, 
                darkcolor=BAR_COLOR,
                borderwidth = 0)
    
    process = ttk.Progressbar(root,style="bar.Horizontal.TProgressbar",orient=tk.HORIZONTAL,length=300,mode = "determinate")
    process.place(x = 50,y = 250+330,
                  width = 760+40,height = 20)
    def step():
        for i in range(20):
            process['value'] = i*10
            root.update_idletasks()
            time.sleep(0.2)
    def stop():
        process.stop()
        process.destroy()
    search_button['state'] = "disabled"
    try:
        send("CHART")
    except socket.error:
        server_crash()
    else:
        #Grab record number
        selected = my_tree.focus()
        
        #Grab record value
        value = my_tree.item(selected,'values')
        
        #Send name and date to server
        send(value[0])
        send(date.strftime("%Y%m%d"))
        
        step()   
        length = receive()
        length = int(length)
        valid_date = []
        buy = []
        sell = []
        for i in range(length):
            date_str = receive()
            valid_date.append(date_str)
            
        for i in range(length):
            buy_price = receive()
            buy.append(buy_price)
            
        for i in range(length):
            sell_price = receive()
            sell.append(sell_price)
            
            
        msg = receive()
        if msg == "DONE":
            search_button['state'] = 'normal'
        
         
        valid_date = [datetime.strptime(item,"%d/%m/%Y") for item in valid_date]
        buy = [int(item.replace(",","")) for item in buy]
        sell = [int(item.replace(",","")) for item in sell]
        
        fig, ax = plt.subplots()
        lines = []
        #plt.subplots_adjust(left=0.1, bottom=0.1, right=0.6, top=0.8)
        l, = ax.plot(valid_date, buy, label="Mua")
        lines.append(l)
        l, = ax.plot(valid_date, sell, label="Bán") 
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
        plt.title(f"{value[0]}",pad= 20)
        plt.gcf().autofmt_xdate()
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        plt.legend(handles=lines,bbox_to_anchor=(1.05, 1), loc='upper left')
        stop()
        plt.show()
        
  
def query_gold_form():
    clear_frame(root)
    
    x = (SCREEN_WIDTH/2) - (900/2)
    y = (SCREEN_HEIGHT/2) - (600/2)

    root.geometry(f"900x600+{int(x)}+{int(y)}")
    root.configure(bg = "#3a6ff7")
    canvas = tk.Canvas(
        root,
        bg = "#3a6ff7",
        height = 600,
        width = 900,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge")
    canvas.place(x = 0, y = 0)

    canvas.create_rectangle(
        50, 0, 50+800, 0+600,
        fill = "#ffffff",
        outline = "")

    canvas.create_text(
        450.0, 44.5,
        text = "TRA CỨU GIÁ VÀNG",
        fill = "#000000",
        font = ("None", int(24.0)))

    canvas.create_rectangle(
        393, 65, 393+115, 65+2,
        fill = "#000000",
        outline = "")

    canvas.create_text(
        136.0+15, 138.5,
        text = "Nhập loại vàng:",
        fill = "#000000",
        font = ("None", int(18.0)))

    canvas.create_text(
        117.5+10, 212.5,
        text = "Chọn ngày:",
        fill = "#000000",
        font = ("None", int(18.0)))
    
    entry0_bg = canvas.create_image(
        330.0+25, 138.5,
        image = type_gold_img)

    name = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0,
        font=("",13))

    name.place(
        x = 240.5+15, y = 116+10,
        width = 179.0,
        height = 30)
    
    cal = DateEntry(
                    width=12,
                    background='darkblue',
                    foreground='white',
                    borderwidth=0,
                    showweeknumbers= False,
                    date_pattern= "dd/mm/yyyy",
                    maxdate= datetime.now())
    
    cal.place(
            x = 117.5+80, y = 200,
            width = 100,
            height = 30)
    
    b0 = tk.Button(
        image = search_button_img,
        borderwidth = 0,
        highlightthickness = 0,
        command = (lambda : start_query_from_server(name.get(),cal.get_date(),my_tree)),
        relief = "flat")
    
    b0.place(
        x = 686, y = 144,
        width = 143,
        height = 58)

    my_tree = ttk.Treeview(root)
    my_tree['columns'] = ("Đơn vị: đồng/lượng","Giá mua","Giá bán")
    
    style = ttk.Style()
    style.theme_use('clam')
    #Config table style
    style.configure("Treeview",
                    background='#E9E9E9',
                    foreground= 'black',
                    rowheight = 25, 
                    fieldbackground='#E9E9E9',
                    )
    #Change the select record color
    style.map('Treeview',background = [('selected','#0E74EC')])
    
    
    #Format columns
    my_tree.column("#0",width = 0, stretch =tk.NO)
    my_tree.column("Đơn vị: đồng/lượng",anchor = tk.W,width = 140)
    my_tree.column("Giá mua",anchor = tk.W,width = 80)
    my_tree.column("Giá bán",anchor = tk.W,width = 80)
    
    #Create headings
    my_tree.heading("#0",text = "",anchor = tk.W)
    my_tree.heading("Đơn vị: đồng/lượng",text = "Đơn vị: đồng/lượng",anchor = tk.W)
    my_tree.heading("Giá mua",text = "Giá mua",anchor = tk.W)
    my_tree.heading("Giá bán",text = "Giá bán",anchor = tk.W)
    
    my_tree.place(
        x =70 ,y = 250,
        width = 760,
        height = 330
    )
    
    my_tree.bind("<Double-1>",lambda event : open_chart(date_charts,my_tree,b0))

def hide_pass(widget):
    widget.config(show = "*") 

def show_pass(widget):
    widget.config(show = "")
  
def register_form():
    clear_frame(root)
    x = (SCREEN_WIDTH/2) - 300
    y = (SCREEN_HEIGHT/2) - (300/2)
    root.geometry(f"600x300+{int(x)}+{int(y)}")
    root.configure(bg = "#3a7ff6")
    canvas = tk.Canvas(
        root,
        bg = "#3a7ff6",
        height = 300,
        width = 600,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge")
    canvas.place(x = 0, y = 0)


    canvas.create_rectangle(
        100, 0, 100+400, 0+300,
        fill = "#ffffff",
        outline = "")

    canvas.create_text(
        299.5, 25.5,
        text = "ĐĂNG KÝ TÀI KHOẢN",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    entry0_bg = canvas.create_image(
        299.5, 89.0,
        image = textBox)

    username = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0)

    username.delete(0,'end')
    username.place(
        x = 191.0+2, y = 64+22,
        width = 217.0,
        height = 25)

    entry1_bg = canvas.create_image(
        299.5, 150.0,
        image = textBox)

    password = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0,
        show = "*")
    password.delete(0,'end')
    password.bind("<Return>",(lambda event : threading.Thread(target= register,args=(username.get(),password.get(),re_enter_password.get())).start()))
    password.place(
        x = 191.0+2, y = 125+22,
        width = 217.0,
        height = 25)

    entry2_bg = canvas.create_image(
        299.5, 211.0,
        image = textBox)

    re_enter_password = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0,
        show="*")
    re_enter_password.delete(0,'end')
    re_enter_password.bind("<Return>",(lambda event : threading.Thread(target= register,args=(username.get(),password.get(),re_enter_password.get())).start()))
    re_enter_password.place(
        x = 191.0+2, y = 186+22,
        width = 217.0,
        height = 25)
    
    show0 = tk.Button(
        image = show_img,
        borderwidth = 0,
        highlightthickness = 0,
        relief = "flat")

    show0.bind("<Button-1>",(lambda event: show_pass(re_enter_password)))
    show0.bind("<ButtonRelease-1>",(lambda event: hide_pass(re_enter_password)))
    
    show0.place(
        x = 371, y = 186,
        width = 47,
        height = 50)

    canvas.create_text(
        219.5+4, 78.5,
        text = "Tài khoản",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    canvas.create_text(
        219.5+5, 138.0,
        text = "Mật khẩu",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    canvas.create_text(
        242.0+15, 199.0,
        text = "Xác nhận mật khẩu",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))


    canvas.create_rectangle(
        264, 37, 264+72, 37+2,
        fill = "#000000",
        outline = "")

    b1 = tk.Button(
        image = sign_up_img,
        borderwidth = 0,
        highlightthickness = 0,
        command = (lambda :threading.Thread(target= register,args=(username.get(),password.get(),re_enter_password.get())).start()),
        relief = "flat")

    b1.place(
        x = 248, y = 248,
        width = 103,
        height = 38)

    show1 = tk.Button(
        image = show_img,
        borderwidth = 0,
        highlightthickness = 0,
        relief = "flat")

    show1.bind("<Button-1>",(lambda event: show_pass(password)))
    show1.bind("<ButtonRelease-1>",(lambda event: hide_pass(password)))
    
    show1.place(
        x = 371, y = 125,
        width = 47,
        height = 50)
    
def login_form():
    clear_frame(root)
    x = (SCREEN_WIDTH/2) - 300
    y = (SCREEN_HEIGHT/2) - (300/2)
    root.geometry(f"600x300+{int(x)}+{int(y)}")
    root.configure(bg = "#3a7ff6")
    canvas = tk.Canvas(
        root,
        bg = "#3a7ff6",
        height = 300,
        width = 600,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge")
    canvas.place(x = 0, y = 0)

    canvas.create_rectangle(
        100, 0, 100+400, 0+300,
        fill = "#ffffff",
        outline = "")

    canvas.create_text(
        298.5, 37.5,
        text = "ĐĂNG NHẬP VÀO SERVER",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    entry0_bg = canvas.create_image(
        298.5, 108.0,
        image = textBox)

    username = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0)

    username.delete(0,'end')
    username.place(
        x = 190.0+2, y = 83+20,
        width = 217.0,
        height = 25)

    entry1_bg = canvas.create_image(
        298.5, 186.0,
        image = textBox)

    password = tk.Entry(
        bd = 0,
        bg = "#e9e9e9",
        highlightthickness = 0,
        show = "*")

    password.delete(0,'end')
    password.bind("<Return>",(lambda event : threading.Thread(target= login,args=(username.get(),password.get())).start()))
    password.place(
        x = 190.0+2, y = 161+21,
        width = 217.0,
        height = 25)

    canvas.create_text(
        218.5+5, 93.5+2,
        text = "Tài khoản",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    canvas.create_text(
        218.5+5, 174.0,
        text = "Mật khẩu",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    canvas.create_rectangle(
        264, 50, 264+72, 50+2,
        fill = "#000000",
        outline = "")

    login_button = tk.Button(
        image = sign_in_img,
        borderwidth = 0,
        highlightthickness = 0,
        command = (lambda :threading.Thread(target= login,args=(username.get(),password.get())).start()),
        relief = "flat")

    login_button.place(
        x = 246, y = 239,
        width = 103,
        height = 38)

    show = tk.Button(
        image = show_img,
        borderwidth = 0,
        highlightthickness = 0,
        relief = "flat")

    show.bind("<Button-1>",(lambda event: show_pass(password)))
    show.bind("<ButtonRelease-1>",(lambda event: hide_pass(password)))
    show.place(
        x = 370, y = 161,
        width = 47,
        height = 50)

    sign_up = tk.Button(
        image = create_acc_img,
        borderwidth = 0,
        highlightthickness = 0,
        command = register_form,
        relief = "flat")

    sign_up.place(
        x = 339, y = 215,
        width = 78,
        height = 13)
 
def input_host():
    x = (SCREEN_WIDTH/2) - 300
    y = (SCREEN_HEIGHT/2) - (300/2)
    root.geometry(f"600x300+{int(x)}+{int(y)}")
    root.configure(bg = "#3a7ff6")
    canvas = tk.Canvas(
        root,
        bg = "#3a7ff6",
        height = 300,
        width = 600,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge")
    canvas.place(x = 0, y = 0)

    canvas.create_rectangle(
        150, 0, 150+300, 0+300,
        fill = "#ffffff",
        outline = "")

    entry0_bg = canvas.create_image(
        299.5, 137.5,
        image = Host_img)

    host_input_field = tk.Entry(
        bd = 0,
        bg = "#dedede",
        highlightthickness = 0)

    host_input_field.insert(tk.END,"HOST IP")
    host_input_field.bind("<Button-1>",(lambda event:host_input_field.delete(0,'end')))
    host_input_field.bind("<Return>", (lambda event : start_connections(host_input_field.get())))
    
    host_input_field.place(
        x = 230.0-3, y = 115+21,
        width = 139.0,
        height = 25)

    canvas.create_text(
        234.5, 126.5,
        text = "IP",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))

    canvas.create_text(
        300.5, 50.0,
        text = "NHẬP HOST IP",
        fill = "#000000",
        font = ("Roboto-Bold", int(12.0)))


    canvas.create_rectangle(
        278, 61, 278+44, 61+1,
        fill = "#000000",
        outline = "")

    b0 = tk.Button(
        image = connect_img,
        borderwidth = 0,
        highlightthickness = 0,
        command = (lambda: start_connections(host_input_field.get())),
        relief = "flat")

    b0.place(
        x = 260, y = 219,
        width = 80,
        height = 40)
    
root = tk.Tk()
root.title("CLIENT") 
root.iconbitmap("Images/Client.ico")
SCREEN_HEIGHT = root.winfo_screenheight()
SCREEN_WIDTH = root.winfo_screenwidth()

#Get directory of program
DIR = os.getcwd()
PATH_IMG = f"{DIR}/Images/"
x = (SCREEN_WIDTH/2) - 300
y = (SCREEN_HEIGHT/2) - (300/2)

#List of img program used
Host_img = ImageTk.PhotoImage(file= f"{PATH_IMG}Host_img.png")
textBox = ImageTk.PhotoImage(file=f"{PATH_IMG}TextBox.png")
sign_in_img = ImageTk.PhotoImage(file=f"{PATH_IMG}Login_Button.png")
connect_img = ImageTk.PhotoImage(file=f"{PATH_IMG}Connect_Button.png")
show_img = ImageTk.PhotoImage(file = f"{PATH_IMG}Show.png")
create_acc_img = ImageTk.PhotoImage(file= f"{PATH_IMG}Create_account.png")
sign_up_img = ImageTk.PhotoImage(file= f"{PATH_IMG}Sign_up_Button.png")
type_gold_img = ImageTk.PhotoImage(file= f"{PATH_IMG}gold_input.png")
search_button_img = ImageTk.PhotoImage(file= f"{PATH_IMG}Search_button.png")

root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_closing)



if __name__ == "__main__":
    input_host()
    root.mainloop()
    