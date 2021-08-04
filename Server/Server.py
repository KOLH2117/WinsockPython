import re
import socket
import threading
import tkinter as tk
from tkinter import messagebox
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from fuzzywuzzy import process  
import time
import sys
import os

DIR = os.path.dirname(__file__)
USER_DATABASE_PATH = DIR + "\\Server Database\\database.db"
GOLDS_DATABASE_PATH = DIR + "\\Server Database\\Golds.db"

HEADER = 64
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (HOST,PORT)
FORMAT = 'utf-8'

CLIENT_DISCONNECT_MSG = "Client has disconnected from server." 
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

"""Nếu đường dẫn không tồn tại thì tạo đường dẫn"""
if not os.path.exists('Server Database'):
    os.makedirs('Server Database')
 
class ThirdPartyServerData:
    def __init__(self):
        return
    
    """Hàm lấy giá vàng"""
    def get_gold_list(date):
        all_golds = {}
        
        """Sử dụng thư viện requests để lấy html response"""
        URL = f"https://tygia.com/api.php?column=0&cols=1&title=1&chart=0&gold=1&rate=0&expand=2&nganhang=VIETCOM&ngay={date}"
        try:
            html_text = requests.get(URL).text
        except:
            messagebox.showerror("Status","Can't connect to third party server")
            os._exit(1)
        soup = BeautifulSoup(html_text,"lxml")
        
        try:
            """Lấy ngày đang tra cứu từ html"""
            present_day = soup.find("span",id = "datepk1")
            
            """Dựa vào class và id để tìm lấy dữ liệu từ html"""
            list_gold = soup.find_all("tr",class_ = "rmore rmore1")
            list_gold.append(soup.find("tr",id = "SJCH_Ch_Minh"))
            list_gold.append(soup.find("tr",id = "SJCH_N_i"))
            list_gold.append(soup.find("tr", id = "DOJIH_N_iAVPL"))
            list_gold.append(soup.find("tr", id = "DOJIH_Ch_MinhAVPL"))
            list_gold.extend(soup.find_all("tr",class_ = "rmore3"))
            list_gold.extend(soup.find_all("tr",class_ = "rmore4"))
            list_gold.extend(soup.find_all("tr",class_ = "rmore5"))
            """Danh sách trả về gồm loại vàng,giá mua,giá bán"""
            values = []
            for gold in list_gold:
                if gold:
                    """Tìm đến thẻ chứa loại vàng"""
                    name = gold.find("td",class_ = "c1 text-left")
                    
                    """Tìm đến thẻ chứa giá mua"""
                    buy = name.find_next("td")
                    
                    """Nếu tồn tại thì trích xuất giá mua ra"""
                    if buy.find_all('div'):
                        buy_price = buy.div.div.span.text
                    else:
                        """Nếu không có thẻ mua thì cho nó bằng 0"""
                        buy_price = "0"
                    
                    """Tìm đến thẻ chứa giá mua"""
                    sell = buy.find_next("td")
                    
                    """Nếu tồn tại thì trích xuất giá mua ra"""
                    if sell.find_all('div'):
                        sell_price = sell.div.div.span.text
                    else:
                        """Nếu không có thẻ mua thì cho nó bằng 0"""
                        sell_price = "0"
                    
                    """Xoá khoảng trắn thừa trong loại vàng"""
                    name = " ".join(name.text.split())
                    
                    
                    """Trường hợp đặc biệt đối với Mi Hồng 950 third party bị lộn giá mua với giá bán"""
                    """Đã kiểm chứng với nhiều trang lấy giá vàng khác"""
                    if gold['id'] != "1OTHERMi_H_ng_950SJC":
                        values.append({
                                    "name" : name,
                                    "buy" : buy_price, 
                                    "sell" : sell_price}
                                    )
                    else:
                        values.append({
                                    "name" : name,
                                    "buy" : sell_price, 
                                    "sell" : buy_price}
                                    )
            """Trả về dạng dict với key là ngày tra"""
            all_golds[present_day.text] = values 
            return all_golds
        except:
            return None

class ServerDatabase:
    def __init__(self):
        self.setup_database()
        threading.Thread(target = self.update_datebase_30min_per_day,daemon= True).start()
            
    """Chuẩn bị cơ sở dữ liệu"""
    def setup_database(self):
        """Kết nối đến database"""
        with sqlite3.connect(USER_DATABASE_PATH,check_same_thread=False) as conn:
            cursor = conn.cursor()
            """Tạo bảng dữ liệu người dùng nếu chưa tồn tại"""
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    userID INTEGER PRIMARY KEY,
                    username VARCHAR(20) NOT NULL,
                    password VARCHAR(20) NOT NULL
                )           
            """)
            
            conn.commit()
    
    """Hàm tìm dữ liệu người dùng trong cơ sở dữ liệu"""
    def find_user_info(username):
        with sqlite3.connect(USER_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            find_user = ("SELECT * FROM users WHERE username = ?")
            cursor.execute(find_user,[username])
            result =  cursor.fetchall()
        
        return result

    """Hàm nhập dữ liệu người dùng vào cơ sở dữ liệu"""
    def insert_user(username,password):
        with sqlite3.connect(USER_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            insert_user = ("""INSERT INTO users (username,password) VALUES (?, ?)""")
            cursor.execute(insert_user,[(username),(password)])
            conn.commit()
            
    """Hàm cập nhật dữ liệu từ third party 30 phút 1 lần"""
    def update_datebase_30min_per_day(self,date = datetime.now()):
        date = date.strftime("%Y%m%d")
        while True:
            with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
                cursor = conn.cursor()    
                """Lấy dữ liệu từ third party về"""
                golds = ThirdPartyServerData.get_gold_list(date)
                
                for table_name, values in golds.items():
                    listOfTables = cursor.execute(f"""SELECT name FROM sqlite_master WHERE type='table'
                                        AND name='{table_name}';""").fetchall()
                    if listOfTables == []:
                        cursor.execute(f"""CREATE TABLE '{table_name}'(
                            NAME VARCHAR(20) PRIMARY KEY,
                            BUY VARCHAR(20),
                            SELL VARCHAR(20))
                            """)
                        for value in values:
                            name = value['name']
                            buy = value['buy']
                            sell = value["sell"]
                            cursor.execute(f"""INSERT INTO '{table_name}' VALUES(?,?,?)""",[name,buy,sell])
                    else:
                        for value in values:
                            name = value['name']
                            buy = value['buy']
                            sell = value["sell"]
                            cursor.execute(f"""UPDATE '{table_name}' SET BUY = ?,SELL = ? WHERE NAME = ?""",[buy,sell,name])
                conn.commit()
                
            min = 30
            time.sleep(min*60)

    """Hàm tìm dữ liệu giá vàng trong database tìm gần đúng tên"""
    def find_approximate_from_database(name, date):
        results = []
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            values = cursor.execute(f"""SELECT * FROM '{date}'""").fetchall()
            if not values:
                return results
            list_of_name = [gold[0] for gold in values]
            """Tìm tên gần đúng nhất với tên người dùng đang tìm"""
            the_most_close = process.extractOne(name,list_of_name)
            
            """Nếu độ chính xác hơn 95% thì trả về giá vàng của loại đó"""
            if the_most_close[1] >= 95:
                values = cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[the_most_close[0]])
                results.extend(values.fetchall())
            else:
                """Nếu độ chính xác bé hơn 95% thì trả về 1 danh sách giá vàng của các loại gần đúng với độ chính xác hơn 80%"""
                list_of_name = process.extractWithoutOrder(name,list_of_name)
                list_of_name = [item[0] for item in list_of_name if item[1] >= 80]
                
                for name_str in list_of_name:
                    cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[name_str])
                    results.extend(cursor.fetchall())
                    
        return results

    """Hàm tạo bảng dữ liệu"""
    def create_table_to_gold_database(date):  
        golds = ThirdPartyServerData.get_gold_list(date)
        if golds == None:
            return False
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            for table_name, values in golds.items():
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{table_name}' (
                        NAME VARCHAR(20) PRIMARY KEY,
                        BUY VARCHAR(20),
                        SELL VARCHAR(20))
                            """)
                for item in values:
                    name = item['name']
                    buy = item['buy']
                    sell = item['sell']
                    cursor.execute(f"""INSERT INTO '{table_name}' VALUES (?,?,?)""",[name,buy,sell])
                
            conn.commit()
            return True
        
    def query_from_database(name,date):
        date_format = datetime.strptime(date,"%Y%m%d").strftime("%#d/%#m/%Y")
        if ServerDatabase.check_gold_table_exists(date_format) == False:
            if ServerDatabase.create_table_to_gold_database(date) == False:
                return None
        results =  ServerDatabase.find_approximate_from_database(name,date_format)
        print(results)
        return results
    
    def check_gold_table_exists(table_name):
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cur = conn.cursor()
            find_table = cur.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name= '{table_name}'""").fetchall()
        if find_table == []:
            return False
        return True
    
    def query_from_database_15_days_before(name,date):
        date_time = datetime.strptime(date,"%Y%m%d")
        pre_15_day = date_time - timedelta(days=15)
        buy = []
        sell = []
        valid_days = []
        while pre_15_day <= date_time:
            date = pre_15_day.strftime("%Y%m%d")
            date_format = pre_15_day.strftime("%#d/%#m/%Y")
            if ServerDatabase.check_gold_table_exists(date_format) == False:
                if ServerDatabase.create_table_to_gold_database(date) == False:
                    continue
            result = ServerDatabase.find_approximate_from_database(name,date_format)
            # result = cur.execute(f"SELECT BUY,SELL FROM '{date_format}' WHERE NAME = ?",[name]).fetchall()
            if result:
                valid_days.append(date_format)
                for item in result:
                    buy.append(item[1])
                    sell.append(item[2])
            pre_15_day += timedelta(days=1)
        
        return valid_days,buy,sell

class SocketServer:
    def __init__(self,app):
        self.flag = True
        self.last_query_date = None
        self.clients = {}
        self.addresses = {}
        self.app = app.main_page
        self.receive_q = []
        self.create_server()
        self.start_server()

        return
    
    """Gửi dữ liệu đến client theo format gửi độ dài rồi gửi nội dung"""
    def send(self,client,msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            client.send(send_length)
            client.send(message)
        except socket.error:
            raise socket.error

    """Nhận dữ liệu từ client"""
    def recv(self,client): 
        msg = ""
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
        except socket.error:
            raise socket.error
        else:   
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT)
            return msg    

    def create_server(self):
        self.SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def server_re_online(self,client):
        username = self.recv(client)
        self.app.insert_to_text_box(f"[SERVER] {username} - Welcome to Server")
        self.clients[client] = username
        
    """Client ngắt kết nối"""
    def client_disconnect(self,client):
        self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} disconnected")
        del self.addresses[client]
        client.close()

    """Client đăng xuất"""
    def client_log_out(self,client):
        self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} log out")
        
        del self.clients[client]
        del self.addresses[client]
        client.close()
        
    """Khi client đột ngột tắt"""
    def client_crash(self,client):
        self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} crash ")
        del self.clients[client]
        del self.addresses[client]  
        client.close() 
         
    """Xử lí yêu cầu người dùng"""    
    def handle_client(self,client):
        global server_disconnect_flag
        login_status = False
        connected = True
        stop_receive = False
        while connected:
            """Lắng nghe và gửi thông báo điến client liên tục"""
            if stop_receive == False:
                self.send(client,"PACKET")
                msg = self.recv(client)
                """Nếu client có tín hiệu cần gửi thông tin đế server thì dừng quá trình này"""
                if msg == ALREADY_LOGGED:
                    login_status = True
                    self.server_re_online(client)
                elif msg == "STOP_FROM_CLIENT":
                    stop_receive = True  
                    self.send(client,"STOP_FROM_SERVER") 
                elif msg == DISCONNECT_MESSAGE:
                    self.client_disconnect(client)
                    break
            else:
                """Trạng thái đăng nhập = False là chưa đăng nhập vào server"""
                if login_status == False:
                    try:
                        msg = self.recv(client)
                    except socket.error as e:
                        self.client_crash(client)
                        break
                    else:
                        if msg == DISCONNECT_MESSAGE:
                            self.client_disconnect(client)
                            connected = False
                        elif msg == "Login":
                            if self.log_in(client) == True:
                                login_status = True
                        else:
                            self.register(client) 
                        stop_receive = False
                else:
                    """Đăng nhập thành công thì client mới có quyền tra cứu"""
                    try:
                        msg = self.recv(client)
                    except socket.error as e:
                        self.client_crash(client)
                    else:
                        if msg == "QUERY":
                            self.receive_client_query(client)
                        elif msg == "CHART":
                            self.send_charts_data(client)
                        elif msg == DISCONNECT_MESSAGE:
                            self.client_log_out(client)
                            connected = False
                        stop_receive = False
                        
            """Tín hiệu để phá vòng lập và gửi thông báo server ngừng kết nối đến các client"""
            if server_disconnect_flag:
                break
        """Khi mà server còn đang kết nối đến client thì gửi tín hiệu ngừng kết nối"""
        if connected:
            self.send(client,DISCONNECT_MESSAGE)
        
               
       
    """Chờ các client khác kết nối"""
    def accept_incoming_connections(self):
        while True:
            try:
                client, client_address = self.SERVER.accept()
            except socket.error:
                break
            else:
                self.app.insert_to_text_box(f"[SERVER] {client_address} has connected.")
                self.addresses[client] = client_address
                threading.Thread(target=self.handle_client, args=(client,)).start() 
    
    """Chạy server"""
    def start_server(self):
        try:
            self.SERVER.bind(ADDR) #Bind server trên địa chỉ ADDR 
            self.SERVER.listen(5)
        except socket.error:
            pass
        else:
            ACCEPT_THREAD = threading.Thread(target=self.accept_incoming_connections)
            ACCEPT_THREAD.start()
    
    """Người dùng đăng kí"""
    def register(self,client):
        try:    
            username = self.recv(client)
            password = self.recv(client)
        except socket.error as e:
            self.client_crash(client)
        else:
            result = ServerDatabase.find_user_info(username)
            
            if result:
                self.send(client,ALREADY_EXIT)
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} sign up failed")
            else:
                self.send(client,SIGN_UP_SUCCESS)
                ServerDatabase.insert_user(username,password)
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} sign up successfully")

    """Người dùng đăng nhập"""
    def log_in(self,client):
        try:    
            username = self.recv(client)
            password = self.recv(client)
      
            """Tìm người dùng trong cơ sở dữ liệu"""
            result = ServerDatabase.find_user_info(username)
            
            """Nếu tìm thấy"""
            if result:
                """Kiểm tra mật khẩu có đúng hay không"""
                if result[0][2] == password:
                    """Nếu đúng thì kiểm tra xem người dùng đã đăng nhập hay chưa"""
                    
                    if self.clients:    
                        for key,user in self.clients.items():
                            if user == username:
                                """Nếu đăng nhập rồi thì trả về False kèm thông báo"""
                                self.app.insert_to_text_box(f"[SERVER] {username} has already logged in")
                                self.send(client,ALREADY_LOGGED)
                                return False
                            else:
                                """Nếu chưa đăng nhập và mật khẩu đúng thì trả về True kèm thông báo"""
                                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} has logged in successfully")
                                self.app.insert_to_text_box(f"[SERVER] {username} - Welcome to Server")
                                self.send(client,LOGIN_MSG_SUCCESS) 
                                self.clients[client] = username
                                return True
                    else:
                        """Nếu chưa có người dùng nào đăng nhập và mật khẩu đúng thì trả về True kèm thông báo"""
                        self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} has logged in successfully")
                        self.app.insert_to_text_box(f"[SERVER] {username} - Welcome to Server")
                        self.send(client,LOGIN_MSG_SUCCESS) 
                        self.clients[client] = username
                        return True
                else:
                    """Nếu mật khẩu sai thì trả về False kèm thông báo"""
                    self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} logged in failed")
                    self.send(client,WRONG_PASSWORD)
                    return False
            else:
                """Nếu chưa đăng ký thì trả về False kèm thông báo"""
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} logged in failed")
                self.send(client,NOT_SIGN_UP)
                return False
        except socket.error as e:
            self.client_crash(client) 

    def receive_client_query(self,client):
        try:
            self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} just make a search request")
            name = self.recv(client)
            date = self.recv(client)
            results = ServerDatabase.query_from_database(name,date)
              
            if results:
                self.last_query_date = date
                self.send(client,FOUND)
               
                self.send(client,str(len(results)))
                for item in results:
                    self.send(client,item[0])
                    self.send(client,item[1])
                    self.send(client,item[2])
                self.send(client,DONE)
                self.app.insert_to_text_box(f"[SERVER] Send results to {self.clients[client]} successfully")
            else:
                self.app.insert_to_text_box(f"[SERVER] Send no results to {self.clients[client]}")
                self.send(client,NOT_FOUND)
        except socket.error:
            self.client_crash(client)
        
    def send_charts_data(self,client):
        try:
            name = self.recv(client)
            date = self.last_query_date
            valid_days,buy,sell = ServerDatabase.query_from_database_15_days_before(name,date)
            self.send(client,str(len(valid_days)))
            for item in valid_days:
                self.send(client,item)
            for item in buy:
                self.send(client,item)
            for item in sell:
                self.send(client,item)
            self.send(client,DONE)
        except socket.error:
            self.client_crash(client)


def center(master,app_width,app_height):
    SCREEN_HEIGHT = master.winfo_screenheight()
    SCREEN_WIDTH = master.winfo_screenwidth()
    
    x = (SCREEN_WIDTH/2) - (app_width/2)  
    y = (SCREEN_HEIGHT/2) - (app_height/2)
    
    master.geometry(f"{app_width}x{app_height}+{int(x)}+{int(y)}")   
            
class LoadingScreen():
    def __init__(self,master,*args,**kwargs):
        if "time_live" in kwargs:
            self.time_live = kwargs.get("time_live")
        else:
            self.time_live = 5
        self.root = tk.Toplevel(master)
        self.master = master
        self.master.withdraw()
        self.app_width = 350
        self.app_height = 80
        self.root.resizable(False, False)
        """Căn thanh loading giữa màn hình"""
        center(self.root,self.app_width,self.app_height)
        self.root.wm_attributes("-transparentcolor",self.root["bg"])
        self.root.overrideredirect(1)
        
        self.frame = tk.Frame(self.root,width = 200,height = 28)
        self.frame.place(x = 100,y = 35 )
        tk.Label(self.frame,text= "Server đang shut down...",fg = "#3a7ff6",font= "Bahnschrift 13").place(x = 0,y=0)
        for i in range(16):
            tk.Label(self.root,bg ="#000",width = 2, height = 1).place(x =(i)*22,y = 10)

        self.root.update()
        self.thread = threading.Thread(target =self.play_animation)
        self.thread.setDaemon(True)
        self.thread.start()
        self.root.after(20, self.check_thread)
        
    def play_animation(self): 
        for i in range(self.time_live):
            if i != self.time_live - 1:   
                for j in range(16):
                    tk.Label(self.root,bg ="#3a7ff6",width = 2, height = 1).place(x =(j)*22,y = 10)
                    time.sleep(0.06)
                    self.root.update_idletasks()
                    tk.Label(self.root,bg ="#000",width = 2, height = 1).place(x =(j)*22,y = 10)
            else:
                for j in range(16):
                    tk.Label(self.root,bg ="#3a7ff6",width = 2, height = 1).place(x =(j)*22,y = 10)
                    time.sleep(0.06)
                    self.root.update_idletasks()
                
    def check_thread(self):
        if self.thread.is_alive():
            self.root.after(20, self.check_thread)
        else:
            self.root.destroy() 
            self.master_exit()
            
    def master_exit(self):
        self.master.destroy()
        os._exit(1)
                         
class MainPage:
    def __init__(self,app):
        self.root = app.root
        self.root.title("SERVER")

        DIR = os.getcwd()
        PATH_IMG = f"{DIR}/Images/"
        self.root.iconbitmap(f"{PATH_IMG}Server.ico")

        self.app_height = 400
        self.app_width = 621

        center(self.root,self.app_width,self.app_height)

        self.messages_frame = tk.Frame(self.root)
        self.scrollbar = tk.Scrollbar(self.messages_frame)
        self.status_list = tk.Listbox(self.messages_frame,width = 100,height = 22,yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_list.pack(side=tk.LEFT, fill=tk.BOTH)
        self.status_list.pack()

        self.messages_frame.pack()

        self.quit_but = tk.Button(self.root,text = "Quit",width = 30,command = self.on_closing)
        self.quit_but.pack(pady = (10,10))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
        self.status_list.insert(tk.END,f"Waiting for connection at {HOST}...")
    
    def insert_to_text_box(self,msg):
        self.status_list.insert(tk.END,msg)
    
    def on_closing(self):
        global server_disconnect_flag 
        server_disconnect_flag = True
        
        """Giao diện tắt server"""
        self.loading = LoadingScreen(self.root,time_live = 5)
        
server_disconnect_flag = False        

class ServerApplication():
    def __init__(self,master):
        self.root = master
        self.root.resizable(False,False)
        self.main_page = MainPage(self)
        self.server = SocketServer(self)
        self.database = ServerDatabase()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApplication(root)
    root.mainloop()


