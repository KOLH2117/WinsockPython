import re
import socket
import threading
import tkinter as tk
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from fuzzywuzzy import fuzz,process  
import time
import sys
import os

import tempfile
DIR = os.path.dirname(__file__)

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
    
    #Get the list of golds from third-party
    def get_gold_list(date):
        all_golds = {}
        
        #Request to URL and get html data
        URL = f"https://tygia.com/api.php?column=0&cols=1&title=1&chart=0&gold=1&rate=0&expand=2&nganhang=VIETCOM&ngay={date}"
        html_text = requests.get(URL).text
        soup = BeautifulSoup(html_text,"lxml")
        
        #Extract the date of data from html
        present_day = soup.find("span",id = "datepk1")
        
        #Extract the list of information about gold
        list_gold = soup.find_all("tr",class_ = "rmore rmore1")
        # SJC_HCM = soup.find("tr",id = "SJCH_Ch_Minh")
        # SJC_HN = soup.find("tr",id = "SJCH_N_i")
        list_gold.append(soup.find("tr",id = "SJCH_Ch_Minh"))
        list_gold.append(soup.find("tr",id = "SJCH_N_i"))
        list_gold.append(soup.find("tr", id = "DOJIH_N_iAVPL"))
        list_gold.append(soup.find("tr", id = "DOJIH_Ch_MinhAVPL"))
        list_gold.extend(soup.find_all("tr",class_ = "rmore3"))
        list_gold.extend(soup.find_all("tr",class_ = "rmore4"))
        list_gold.extend(soup.find_all("tr",class_ = "rmore5"))
        #Get the value of the gold consists of name,buy_price,sell_price
        values = []
        for gold in list_gold:
            if gold:
                #Get the gold name
                name = gold.find("td",class_ = "c1 text-left")
                
                #Get the buy tag
                buy = name.find_next("td")
                #Check if the value is available
                if buy.find_all('div'):
                    buy_price = buy.div.div.span.text
                else:
                    buy_price = "0"
                
                #Get the sell tag
                sell = buy.find_next("td")
                if sell.find_all('div'):
                    sell_price = sell.div.div.span.text
                else:
                    sell_price = "0"
                name = " ".join(name.text.split())
                
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
        all_golds[present_day.text] = values 
        return all_golds

class ServerDatabase:
    def __init__(self):
        self.setup_database()
        self.Thread = threading.Thread(target = self.update_datebase_30min_per_day,daemon= True).start()
            
    #Set up database
    def setup_database(self):
        #Connect to the database
        with sqlite3.connect(DIR + "\\Server Database\\database.db",check_same_thread=False) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    userID INTEGER PRIMARY KEY,
                    username VARCHAR(20) NOT NULL,
                    password VARCHAR(20) NOT NULL
                )           
            """)
            
            conn.commit()
            
    #Start gathering and update data each 30 min on another thread
    def update_datebase_30min_per_day(self,date = datetime.now()):
        date = date.strftime("%Y%m%d")
        while True:
            with sqlite3.connect(DIR + '\\Server Database\\Golds.db',check_same_thread = False) as conn:
                cursor = conn.cursor()    
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

    def find_approximate_from_database(name, date):
        results = []
        with sqlite3.connect(DIR + '\\Server Database\\Golds.db',check_same_thread = False) as conn:
            cursor = conn.cursor()
            values = cursor.execute(f"""SELECT * FROM '{date}'""").fetchall()
            if not values:
                return results
            list_of_name = [gold[0] for gold in values]
            the_most_close = process.extractOne(name,list_of_name)
            
            #If the percent larger than 95%
            if the_most_close[1] >= 95:
                values = cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[the_most_close[0]])
                results.extend(values.fetchall())
            else:
                list_of_name = process.extractWithoutOrder(name,list_of_name)
                list_of_name = [item[0] for item in list_of_name if item[1] >= 80]
                
                for name_str in list_of_name:
                    cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[name_str])
                    results.extend(cursor.fetchall())
                    
        return results

    def create_table_to_gold_database(date):  
        golds = ThirdPartyServerData.get_gold_list(date)
        
        with sqlite3.connect(DIR + '\\Server Database\\Golds.db',check_same_thread = False) as conn:
            cursor = conn.cursor()
            for table_name, values in golds.items():
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS'{table_name}' (
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

    def find_user_info(username):
        with sqlite3.connect(DIR + '\\Server Database\\database.db',check_same_thread = False) as conn:
            cursor = conn.cursor()
            find_user = ("SELECT * FROM users WHERE username = ?")
            cursor.execute(find_user,[username])
            result =  cursor.fetchall()
        
        return result

    def insert_user(username,password):
        with sqlite3.connect(DIR + '\\Server Database\\database.db',check_same_thread = False) as conn:
            cursor = conn.cursor()
            insert_user = ("""INSERT INTO users (username,password) VALUES (?, ?)""")
            cursor.execute(insert_user,[(username),(password)])
            conn.commit()
        
    def query_from_database(name,date):
        date_format = datetime.strptime(date,"%Y%m%d").strftime("%#d/%#m/%Y")
        with sqlite3.connect(DIR + '\\Server Database\\Golds.db',check_same_thread = False) as conn:
            cur = conn.cursor()
            find_table = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name= '{date_format}'").fetchall()
        if find_table == []:
            ServerDatabase.create_table_to_gold_database(date)
        results =  ServerDatabase.find_approximate_from_database(name,date_format)
        
        return results
    
    def query_from_database_15_before(name,date):
        date_time = datetime.strptime(date,"%Y%m%d")
        pre_15_day = date_time - timedelta(days=15)
        buy = []
        sell = []
        valid_days = []
        while pre_15_day <= date_time:
            date = pre_15_day.strftime("%Y%m%d")
            date_format = pre_15_day.strftime("%#d/%#m/%Y")
            with sqlite3.connect(DIR + '\\Server Database\\Golds.db',check_same_thread = False) as conn:
                cur = conn.cursor()
                find_table = cur.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name= '{date_format}'""").fetchall()
            if find_table == []:
                ServerDatabase.create_table_to_gold_database(date)
                
            result = cur.execute(f"SELECT BUY,SELL FROM '{date_format}' WHERE NAME = ?",[name]).fetchall()
            if result:
                valid_days.append(date_format)
                for item in result:
                    buy.append(item[0])
                    sell.append(item[1])
            pre_15_day += timedelta(days=1)
        
        return valid_days,buy,sell

class SocketServerPython:
    def __init__(self,app):
        self.flag = True
        self.last_query_date = None
        self.clients = {}
        self.addresses = {}
        self.app = app.main_page
        
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
    
    def sub_backend(self,client):
        global server_disconnect_flag
        while True:
            if server_disconnect_flag:
                self.send(client,"ACK")
            else:
                self.send(client,DISCONNECT_MESSAGE)
                break
    
    def server_disconnect(self):
        self.broadcast(DISCONNECT_MESSAGE)
        del self.addresses
        
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
        connected = True
        while connected:
            try:
                msg = self.recv(client)
            except socket.error as e:
                self.client_crash(client)
                break
            else:
                if msg == DISCONNECT_MESSAGE:
                    self.client_disconnect(client)
                    connected = False
                    break
                elif msg == "Login":
                    if self.log_in(client) == True:
                        break;
                else:
                    self.register(client)    
        
        while connected:
            try:
                msg = self.recv(client)
            except socket.error as e:
                self.client_crash(client)
            else:
                if msg == "QUERY":
                    self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} just make a search request")
                    self.receive_client_query(client)
                elif msg == "CHART":
                    self.send_charts_data(client)
                elif msg == DISCONNECT_MESSAGE:
                    self.client_log_out(client)
                    connected = False
    
    #Sets up handling for incoming clients.
    def accept_incoming_connections(self):
        while True:
            try:
                client, client_address = self.SERVER.accept()
            except socket.error:
                break
            else:
                self.app.insert_to_text_box(f"[SERVER] {client_address} has connected.")
                self.addresses[client] = client_address
                threading.Thread(target=self.sub_backend, args=(client,)).start()
                threading.Thread(target=self.handle_client, args=(client,)).start() 
    
    #Start the server
    def start_server(self):
        try:
            self.SERVER.bind(ADDR) #Bind server trên địa chỉ ADDR 
            self.SERVER.listen(5)
        except socket.error:
            pass
        else:
            ACCEPT_THREAD = threading.Thread(target=self.accept_incoming_connections)
            ACCEPT_THREAD.start()
    
    def broadcast(self,msg,prefix = ""):
        for sock in self.addresses:
            self.send(sock,prefix+msg)
            
        #Handle the register process
    
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
                    if client in self.clients:
                        """Nếu đăng nhập rồi thì trả về False kèm thông báo"""
                        self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} has already logged in")
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
            valid_days,buy,sell = ServerDatabase.query_from_database_15_before(name,date)
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
            
             
class MainPage:
    def __init__(self,app):
        self.root = app.root
        self.root.title("SERVER")

        DIR = os.getcwd()
        PATH_IMG = f"{DIR}/Images/"
        self.root.iconbitmap(f"{PATH_IMG}Server.ico")

        self.app_height = 400
        self.app_width = 621

        screen_height = self.root.winfo_screenheight()
        screen_width = self.root.winfo_screenwidth()

        x = (screen_width/2)   - (self.app_width/2)
        y = (screen_height/2)  - (self.app_height/2)

        self.root.geometry(f"{self.app_width}x{self.app_height}+{int(x)}+{int(y)}")

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
        return
        
    def run(self):
        self.root.mainloop()
    

    def insert_to_text_box(self,msg):
        self.status_list.insert(tk.END,msg)
        
    #When closing the server
    def on_closing(self):
        global server_disconnect_flag 
        server_disconnect_flag = False
        self.root.destroy()
        os._exit(1)
        # if SERVER.fileno() == -1:
        #     root.destroy()
        #     return 
        # try:
        #     if addresses:
        #         for sock in addresses:
        #             send(sock,DISCONNECT_MESSAGE)
        # except socket.error:
        #     print(socket.error)
        
        # SERVER.close()
        # root.destroy()
        # sys.exit()
server_disconnect_flag = True        

class ServerApplication():
    def __init__(self,master):
        self.root = master
        self.root.resizable(False,False)
        self.main_page = MainPage(self)
        self.server = SocketServerPython(self)
        self.database = ServerDatabase()
        
    

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApplication(root)
    root.mainloop()


